"""Purchases, restocks and time-boxed holds.

Concurrency strategy: never read-then-write. Every stock change is ONE conditional UPDATE
(`... WHERE quantity - reserved > 0`) and we check `rowcount`. The database serialises those
statements, so N concurrent buyers of M units yield exactly M winners - no locks held in Python.
"""
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models import Hold, Order, User, Vehicle, utcnow
from app.services.base import BaseService
from app.services.errors import ConflictError, ForbiddenError, NotFoundError


class InventoryService(BaseService):
    def __init__(self, db, hold_minutes: int = 10):
        super().__init__(db)
        self.hold_minutes = hold_minutes

    # ---------- helpers ----------
    def _get_vehicle(self, vehicle_id: int) -> Vehicle:
        vehicle = self.db.get(Vehicle, vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle not found")
        return vehicle

    def _active_hold(self, user_id: int, vehicle_id: int, now: datetime) -> Hold | None:
        return self.db.scalar(
            select(Hold).where(
                Hold.user_id == user_id,
                Hold.vehicle_id == vehicle_id,
                Hold.status == "active",
                Hold.expires_at > now,
            )
        )

    def _close_hold(self, hold: Hold, new_status: str) -> bool:
        """Atomically move an active hold to `new_status`. Returns False if someone else got there first."""
        res = self.db.execute(
            update(Hold)
            .where(Hold.id == hold.id, Hold.status == "active")
            .values(status=new_status)
            .execution_options(synchronize_session=False)
        )
        return res.rowcount == 1

    def _expire_due(self, now: datetime) -> int:
        """Release every hold whose time is up. Safe to run concurrently (each hold is claimed once)."""
        due = self.db.execute(
            select(Hold.id, Hold.vehicle_id, Hold.user_id).where(Hold.status == "active", Hold.expires_at <= now)
        ).all()
        expired = 0
        for hold_id, vehicle_id, user_id in due:
            claimed = self.db.execute(
                update(Hold)
                .where(Hold.id == hold_id, Hold.status == "active")
                .values(status="expired")
                .execution_options(synchronize_session=False)
            )
            if claimed.rowcount != 1:
                continue
            self.db.execute(
                update(Vehicle)
                .where(Vehicle.id == vehicle_id, Vehicle.reserved > 0)
                .values(reserved=Vehicle.reserved - 1)
                .execution_options(synchronize_session=False)
            )
            self._record("hold_expired", vehicle_id=vehicle_id, user_id=user_id, delta=0)
            expired += 1
        return expired

    # ---------- public API ----------
    def expire_due_holds(self, now: datetime | None = None) -> int:
        with self._tx():
            return self._expire_due(now or utcnow())

    def list_user_holds(self, user: User, now: datetime | None = None) -> list[Hold]:
        self.expire_due_holds(now)
        return list(
            self.db.scalars(
                select(Hold).where(Hold.user_id == user.id, Hold.status == "active").order_by(Hold.expires_at)
            )
        )

    def place_hold(self, user: User, vehicle_id: int, now: datetime | None = None) -> Hold:
        now = now or utcnow()
        with self._tx():
            self._expire_due(now)
            vehicle = self._get_vehicle(vehicle_id)
            if self._active_hold(user.id, vehicle_id, now):
                raise ConflictError("You already have a hold on this vehicle")
            res = self.db.execute(
                update(Vehicle)
                .where(Vehicle.id == vehicle_id, Vehicle.quantity - Vehicle.reserved > 0)
                .values(reserved=Vehicle.reserved + 1)
                .execution_options(synchronize_session=False)
            )
            if res.rowcount != 1:
                raise ConflictError("No unit is available to hold")
            hold = Hold(vehicle_id=vehicle_id, user_id=user.id, expires_at=now + timedelta(minutes=self.hold_minutes))
            try:
                self.db.add(hold)
                self.db.flush()
            except IntegrityError:
                raise ConflictError("You already have a hold on this vehicle")
            self._record("hold_placed", vehicle=vehicle, user=user, detail=f"{self.hold_minutes} min")
        return hold

    def release_hold(self, user: User, vehicle_id: int, now: datetime | None = None) -> None:
        now = now or utcnow()
        with self._tx():
            self._expire_due(now)
            vehicle = self._get_vehicle(vehicle_id)
            hold = self._active_hold(user.id, vehicle_id, now)
            if not hold:
                raise NotFoundError("You have no active hold on this vehicle")
            if not self._close_hold(hold, "released"):
                raise ConflictError("Hold is no longer active")
            self.db.execute(
                update(Vehicle)
                .where(Vehicle.id == vehicle_id, Vehicle.reserved > 0)
                .values(reserved=Vehicle.reserved - 1)
                .execution_options(synchronize_session=False)
            )
            self._record("hold_released", vehicle=vehicle, user=user)

    def purchase(
        self, user: User, vehicle_id: int, hold_id: int | None = None, now: datetime | None = None
    ) -> Vehicle:
        """Buy one unit. If the user holds a unit of this vehicle, the hold is consumed; otherwise a free unit is needed."""
        now = now or utcnow()
        with self._tx():
            self._expire_due(now)
            vehicle = self._get_vehicle(vehicle_id)

            if hold_id is not None:
                hold = self.db.get(Hold, hold_id)
                if not hold or hold.vehicle_id != vehicle_id or hold.user_id != user.id:
                    raise NotFoundError("Hold not found")
                if hold.status != "active" or hold.expires_at <= now:
                    raise ConflictError("That hold has expired")
            else:
                hold = self._active_hold(user.id, vehicle_id, now)

            if hold:
                if not self._close_hold(hold, "converted"):
                    raise ConflictError("Hold is no longer active")
                res = self.db.execute(
                    update(Vehicle)
                    .where(Vehicle.id == vehicle_id, Vehicle.quantity > 0, Vehicle.reserved > 0)
                    .values(quantity=Vehicle.quantity - 1, reserved=Vehicle.reserved - 1)
                    .execution_options(synchronize_session=False)
                )
            else:
                res = self.db.execute(
                    update(Vehicle)
                    .where(Vehicle.id == vehicle_id, Vehicle.quantity - Vehicle.reserved > 0)
                    .values(quantity=Vehicle.quantity - 1)
                    .execution_options(synchronize_session=False)
                )
            if res.rowcount != 1:
                raise ConflictError("This vehicle is out of stock")
            self.db.add(
                Order(
                    user_id=user.id,
                    vehicle_id=vehicle.id,
                    vehicle_label=vehicle.label,
                    category=vehicle.category,
                    color=vehicle.color,
                    price=vehicle.price,
                    from_hold=bool(hold),
                )
            )
            self._record(
                "purchase",
                vehicle=vehicle,
                user=user,
                delta=-1,
                amount=vehicle.price,
                detail="from hold" if hold else None,
            )
        self.db.refresh(vehicle)
        return vehicle

    def restock(self, user: User, vehicle_id: int, quantity: int) -> Vehicle:
        if not user.is_admin:
            raise ForbiddenError("Admin access required")
        with self._tx():
            vehicle = self._get_vehicle(vehicle_id)
            self.db.execute(
                update(Vehicle)
                .where(Vehicle.id == vehicle_id)
                .values(quantity=Vehicle.quantity + quantity)
                .execution_options(synchronize_session=False)
            )
            self._record("restock", vehicle=vehicle, user=user, delta=quantity)
        self.db.refresh(vehicle)
        return vehicle

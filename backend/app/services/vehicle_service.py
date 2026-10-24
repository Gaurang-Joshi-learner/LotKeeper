"""Vehicle CRUD + search. Every mutation writes an audit event in the same transaction."""
from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.models import Hold, User, Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas import SearchParams, VehicleCreate, VehicleUpdate
from app.services.base import BaseService
from app.services.errors import ConflictError, NotFoundError


class VehicleService(BaseService):
    def __init__(self, db):
        super().__init__(db)
        self.repo = VehicleRepository(db)

    def get(self, vehicle_id: int) -> Vehicle:
        vehicle = self.repo.get(vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle not found")
        return vehicle

    def search(self, params: SearchParams) -> list[Vehicle]:
        return self.repo.search(params)

    def create(self, user: User, data: VehicleCreate) -> Vehicle:
        fields = data.model_dump()
        fields["price"] = Decimal(str(fields["price"]))
        vehicle = Vehicle(**fields)
        with self._tx():
            self.repo.add(vehicle)
            self._record("vehicle_created", vehicle=vehicle, user=user, delta=vehicle.quantity)
        return vehicle

    def update(self, user: User, vehicle_id: int, data: VehicleUpdate) -> Vehicle:
        vehicle = self.get(vehicle_id)
        changes = data.model_dump(exclude_unset=True)
        if "price" in changes and changes["price"] is not None:
            changes["price"] = Decimal(str(changes["price"]))
        for required in ("make", "model", "category", "price", "quantity"):
            if required in changes and changes[required] is None:
                raise ConflictError(f"{required} cannot be null")
        if "quantity" in changes and changes["quantity"] < vehicle.reserved:
            raise ConflictError(
                f"Quantity cannot be lower than the {vehicle.reserved} unit(s) currently on hold"
            )
        old_quantity = vehicle.quantity
        try:
            with self._tx():
                for key, value in changes.items():
                    setattr(vehicle, key, value)
                self.db.flush()
                self._record(
                    "vehicle_updated",
                    vehicle=vehicle,
                    user=user,
                    delta=vehicle.quantity - old_quantity,
                    detail=", ".join(sorted(changes)) or None,
                )
        except IntegrityError:
            raise ConflictError("Update would violate stock constraints")
        return vehicle

    def delete(self, user: User, vehicle_id: int) -> None:
        vehicle = self.get(vehicle_id)
        with self._tx():
            self._record("vehicle_deleted", vehicle=vehicle, user=user, delta=-vehicle.quantity)
            self.db.execute(delete(Hold).where(Hold.vehicle_id == vehicle.id))
            self.repo.delete(vehicle)

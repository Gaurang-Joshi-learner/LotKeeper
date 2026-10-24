"""Shared service plumbing: a transaction scope and the audit-log writer."""
from contextlib import contextmanager
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import InventoryEvent, User, Vehicle


class BaseService:
    def __init__(self, db: Session):
        self.db = db

    @contextmanager
    def _tx(self):
        """Commit on success, roll back on any error. Every public service method is one transaction."""
        try:
            yield
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def _record(
        self,
        type_: str,
        *,
        vehicle: Vehicle | None = None,
        vehicle_id: int | None = None,
        vehicle_label: str | None = None,
        user: User | None = None,
        user_id: int | None = None,
        user_email: str | None = None,
        delta: int = 0,
        amount: Decimal | float | None = None,
        detail: str | None = None,
    ) -> None:
        """Append an audit event to the current transaction (committed together with the change itself)."""
        self.db.add(
            InventoryEvent(
                type=type_,
                vehicle_id=vehicle.id if vehicle else vehicle_id,
                vehicle_label=vehicle.label if vehicle else vehicle_label,
                user_id=user.id if user else user_id,
                user_email=user.email if user else user_email,
                delta=delta,
                amount=Decimal(str(amount)) if amount is not None else None,
                detail=detail,
            )
        )

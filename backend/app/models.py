"""SQLAlchemy models.

Stock model:
  quantity  - units physically on the lot
  reserved  - units currently covered by an active hold
  available - quantity - reserved (what a shopper can still buy/hold)
CHECK constraints keep 0 <= reserved <= quantity at the database level, so even a buggy code path
cannot oversell.
"""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Stores naive UTC, always returns timezone-aware UTC (SQLite drops tzinfo otherwise)."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        return None if value is None else value.replace(tzinfo=timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")  # "user" | "admin"
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_vehicle_quantity_nonneg"),
        CheckConstraint("reserved >= 0", name="ck_vehicle_reserved_nonneg"),
        CheckConstraint("reserved <= quantity", name="ck_vehicle_reserved_lte_quantity"),
        CheckConstraint("price > 0", name="ck_vehicle_price_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    make: Mapped[str] = mapped_column(String(60), index=True)
    model: Mapped[str] = mapped_column(String(60), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # "#RRGGBB"
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    @property
    def available(self) -> int:
        return self.quantity - self.reserved

    @property
    def label(self) -> str:
        parts = [str(self.year) if self.year else None, self.make, self.model]
        return " ".join(p for p in parts if p)


class Hold(Base):
    """A time-boxed reservation of one unit for one user."""

    __tablename__ = "holds"
    __table_args__ = (
        Index("ix_holds_status_expires", "status", "expires_at"),
        # A user may hold at most one unit of a given vehicle at a time.
        Index(
            "uq_active_hold_per_user_vehicle",
            "vehicle_id",
            "user_id",
            unique=True,
            sqlite_where=text("status = 'active'"),
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(12), default="active")  # active|converted|expired|released
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)


class InventoryEvent(Base):
    """Append-only audit trail. Denormalised on purpose so history survives deleted vehicles/users."""

    __tablename__ = "inventory_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(24), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    vehicle_label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delta: Mapped[int] = mapped_column(Integer, default=0)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)


class Order(Base):
    """A completed purchase, owned by one user. Snapshots label/price so history never changes
    when the catalogue does (and survives the vehicle being deleted)."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vehicle_label: Mapped[str] = mapped_column(String(160))
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    from_hold: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)

"""All vehicle queries live here so services stay free of SQL details."""
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models import Vehicle
from app.schemas import SearchParams


class VehicleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, vehicle_id: int) -> Vehicle | None:
        return self.db.get(Vehicle, vehicle_id)

    def add(self, vehicle: Vehicle) -> Vehicle:
        self.db.add(vehicle)
        self.db.flush()
        return vehicle

    def delete(self, vehicle: Vehicle) -> None:
        self.db.delete(vehicle)

    def search(self, p: SearchParams) -> list[Vehicle]:
        return list(self.db.scalars(self._build_query(p)))

    @staticmethod
    def _contains(column, text: str):
        return func.lower(column).contains(text.strip().lower(), autoescape=True)

    def _build_query(self, p: SearchParams) -> Select:
        stmt = select(Vehicle)
        if p.make:
            stmt = stmt.where(self._contains(Vehicle.make, p.make))
        if p.model:
            stmt = stmt.where(self._contains(Vehicle.model, p.model))
        if p.category:
            stmt = stmt.where(self._contains(Vehicle.category, p.category))
        if p.q:
            stmt = stmt.where(
                or_(
                    self._contains(Vehicle.make, p.q),
                    self._contains(Vehicle.model, p.q),
                    self._contains(Vehicle.category, p.q),
                )
            )
        if p.min_price is not None:
            stmt = stmt.where(Vehicle.price >= p.min_price)
        if p.max_price is not None:
            stmt = stmt.where(Vehicle.price <= p.max_price)
        if p.in_stock:
            stmt = stmt.where(Vehicle.quantity - Vehicle.reserved > 0)

        order = {
            "newest": (Vehicle.id.desc(),),
            "price_asc": (Vehicle.price.asc(), Vehicle.id.asc()),
            "price_desc": (Vehicle.price.desc(), Vehicle.id.asc()),
            "name": (func.lower(Vehicle.make).asc(), func.lower(Vehicle.model).asc()),
        }[p.sort]
        return stmt.order_by(*order).limit(p.limit).offset(p.offset)

"""Read access to orders. A user can only ever list their own; admins can list everyone's."""
from sqlalchemy import select

from app.models import Order, User
from app.schemas import AdminOrderOut, OrderOut
from app.services.base import BaseService


class OrderService(BaseService):
    def list_for_user(self, user: User, limit: int = 100) -> list[Order]:
        stmt = select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc(), Order.id.desc()).limit(limit)
        return list(self.db.scalars(stmt))

    def list_all(self, limit: int = 100) -> list[AdminOrderOut]:
        stmt = (
            select(Order, User.email)
            .join(User, User.id == Order.user_id)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .limit(limit)
        )
        return [
            AdminOrderOut(**OrderOut.model_validate(order).model_dump(), user_email=email)
            for order, email in self.db.execute(stmt)
        ]

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_order_service
from app.models import User
from app.schemas import OrderOut
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("/mine", response_model=list[OrderOut])
def my_orders(user: User = Depends(get_current_user), svc: OrderService = Depends(get_order_service)):
    """The signed-in user's own purchases, newest first. There is deliberately no way to ask for someone else's."""
    return svc.list_for_user(user)

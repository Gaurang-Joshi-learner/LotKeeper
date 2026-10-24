from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_inventory_service
from app.models import User
from app.schemas import HoldOut
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/api/holds", tags=["holds"])


@router.get("/mine", response_model=list[HoldOut])
def my_holds(user: User = Depends(get_current_user), inventory: InventoryService = Depends(get_inventory_service)):
    """The current user's live holds (drives the countdown timers in the UI)."""
    return inventory.list_user_holds(user)

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_analytics_service, get_order_service, require_admin
from app.core.database import get_db
from app.models import InventoryEvent, User
from app.schemas import AdminOrderOut, AnalyticsOut, EventOut
from app.services.analytics_service import AnalyticsService
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/events", response_model=list[EventOut])
def list_events(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Audit trail, newest first."""
    return list(
        db.scalars(select(InventoryEvent).order_by(InventoryEvent.created_at.desc(), InventoryEvent.id.desc()).limit(limit))
    )


@router.get("/analytics", response_model=AnalyticsOut)
def analytics(svc: AnalyticsService = Depends(get_analytics_service)):
    return svc.summary()


@router.get("/orders", response_model=list[AdminOrderOut])
def all_orders(svc: OrderService = Depends(get_order_service)):
    """Every customer's orders, with the buyer's email."""
    return svc.list_all()

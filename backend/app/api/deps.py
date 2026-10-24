"""FastAPI dependencies: current user, admin guard, service factories."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.inventory_service import InventoryService
from app.services.order_service import OrderService
from app.services.vehicle_service import VehicleService

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Not authenticated", headers={"WWW-Authenticate": "Bearer"}
    )
    if creds is None:
        raise unauthorized
    user_id = decode_access_token(creds.credentials)
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise unauthorized
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


def require_vehicle_writer(
    user: User = Depends(get_current_user), settings: Settings = Depends(get_settings)
) -> User:
    if settings.vehicle_write_admin_only and not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_vehicle_service(db: Session = Depends(get_db)) -> VehicleService:
    return VehicleService(db)


def get_inventory_service(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> InventoryService:
    return InventoryService(db, hold_minutes=settings.hold_minutes)


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(db)

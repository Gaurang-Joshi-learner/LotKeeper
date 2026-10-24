from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import ValidationError

from app.api.deps import (
    get_current_user,
    get_inventory_service,
    get_vehicle_service,
    require_admin,
    require_vehicle_writer,
)
from app.models import User
from app.schemas import (
    HoldOut,
    PurchaseIn,
    RestockIn,
    SearchParams,
    VehicleCreate,
    VehicleOut,
    VehicleUpdate,
)
from app.services.inventory_service import InventoryService
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


def search_params(
    make: str | None = None,
    model: str | None = None,
    category: str | None = None,
    q: str | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    in_stock: bool = False,
    sort: str = Query("newest", pattern="^(newest|price_asc|price_desc|name)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> SearchParams:
    """Collect query params into SearchParams; cross-field errors (min > max) become a clean 422."""
    try:
        return SearchParams(
            make=make, model=model, category=category, q=q, min_price=min_price, max_price=max_price,
            in_stock=in_stock, sort=sort, limit=limit, offset=offset,
        )
    except ValidationError as exc:
        raise HTTPException(422, "; ".join(e["msg"] for e in exc.errors()))


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    body: VehicleCreate, user: User = Depends(require_vehicle_writer), svc: VehicleService = Depends(get_vehicle_service)
):
    return svc.create(user, body)


@router.get("", response_model=list[VehicleOut])
def list_vehicles(
    _: User = Depends(get_current_user),
    svc: VehicleService = Depends(get_vehicle_service),
    inventory: InventoryService = Depends(get_inventory_service),
):
    """All vehicles, including sold-out ones (their `available` is 0 so the UI can disable Purchase)."""
    inventory.expire_due_holds()
    return svc.search(SearchParams(sort="newest", limit=500))


# NOTE: declared before "/{vehicle_id}" so "search" is not parsed as an id.
@router.get("/search", response_model=list[VehicleOut])
def search_vehicles(
    params: SearchParams = Depends(search_params),
    _: User = Depends(get_current_user),
    svc: VehicleService = Depends(get_vehicle_service),
    inventory: InventoryService = Depends(get_inventory_service),
):
    inventory.expire_due_holds()
    return svc.search(params)


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, _: User = Depends(get_current_user), svc: VehicleService = Depends(get_vehicle_service)):
    return svc.get(vehicle_id)


@router.put("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: int,
    body: VehicleUpdate,
    user: User = Depends(require_vehicle_writer),
    svc: VehicleService = Depends(get_vehicle_service),
):
    return svc.update(user, vehicle_id, body)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle_id: int, user: User = Depends(require_admin), svc: VehicleService = Depends(get_vehicle_service)):
    svc.delete(user, vehicle_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{vehicle_id}/purchase", response_model=VehicleOut)
def purchase_vehicle(
    vehicle_id: int,
    body: PurchaseIn | None = None,
    user: User = Depends(get_current_user),
    inventory: InventoryService = Depends(get_inventory_service),
):
    return inventory.purchase(user, vehicle_id, hold_id=body.hold_id if body else None)


@router.post("/{vehicle_id}/restock", response_model=VehicleOut)
def restock_vehicle(
    vehicle_id: int,
    body: RestockIn,
    user: User = Depends(require_admin),
    inventory: InventoryService = Depends(get_inventory_service),
):
    return inventory.restock(user, vehicle_id, body.quantity)


@router.post("/{vehicle_id}/hold", response_model=HoldOut, status_code=status.HTTP_201_CREATED)
def hold_vehicle(
    vehicle_id: int, user: User = Depends(get_current_user), inventory: InventoryService = Depends(get_inventory_service)
):
    return inventory.place_hold(user, vehicle_id)


@router.delete("/{vehicle_id}/hold", status_code=status.HTTP_204_NO_CONTENT)
def release_hold(
    vehicle_id: int, user: User = Depends(get_current_user), inventory: InventoryService = Depends(get_inventory_service)
):
    inventory.release_hold(user, vehicle_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

"""The headline guarantee: stock can never be oversold, however many buyers collide."""
import threading
from concurrent.futures import ThreadPoolExecutor

from app.models import User, Vehicle
from app.services.auth_service import AuthService
from app.services.errors import ConflictError
from app.services.inventory_service import InventoryService


def _setup(session_factory, quantity: int, buyers: int):
    with session_factory() as db:
        auth = AuthService(db)
        users = [auth.register(f"buyer{i}@example.com", "supersecret1") for i in range(buyers)]
        vehicle = Vehicle(make="Toyota", model="Corolla", category="Sedan", price=20000, quantity=quantity)
        db.add(vehicle)
        db.commit()
        return vehicle.id, [u.id for u in users]


def _detached_user(db, user_id):
    """Load the user, then give the pooled connection back so waiting threads can't exhaust the pool."""
    user = db.get(User, user_id)
    db.expunge(user)
    db.rollback()
    return user


def _run_parallel(session_factory, user_ids, action):
    barrier = threading.Barrier(len(user_ids))

    def worker(user_id):
        with session_factory() as db:
            user = _detached_user(db, user_id)
            barrier.wait(timeout=30)  # release every thread at the same instant
            try:
                action(InventoryService(db), user)
                return "ok"
            except ConflictError:
                return "conflict"

    with ThreadPoolExecutor(max_workers=len(user_ids)) as pool:
        return list(pool.map(worker, user_ids))


def test_20_buyers_5_units_exactly_5_succeed(session_factory):
    vehicle_id, user_ids = _setup(session_factory, quantity=5, buyers=20)
    results = _run_parallel(session_factory, user_ids, lambda svc, u: svc.purchase(u, vehicle_id))
    assert results.count("ok") == 5
    assert results.count("conflict") == 15
    with session_factory() as db:
        assert db.get(Vehicle, vehicle_id).quantity == 0


def test_concurrent_holds_never_exceed_stock(session_factory):
    vehicle_id, user_ids = _setup(session_factory, quantity=3, buyers=12)
    results = _run_parallel(session_factory, user_ids, lambda svc, u: svc.place_hold(u, vehicle_id))
    assert results.count("ok") == 3
    with session_factory() as db:
        v = db.get(Vehicle, vehicle_id)
        assert (v.quantity, v.reserved, v.available) == (3, 3, 0)


def test_holds_and_purchases_compete_for_the_same_units(session_factory):
    vehicle_id, user_ids = _setup(session_factory, quantity=4, buyers=16)
    actions = [
        (lambda svc, u: svc.place_hold(u, vehicle_id)) if i % 2 else (lambda svc, u: svc.purchase(u, vehicle_id))
        for i in range(16)
    ]
    barrier = threading.Barrier(16)

    def worker(i):
        with session_factory() as db:
            user = _detached_user(db, user_ids[i])
            barrier.wait(timeout=30)
            try:
                actions[i](InventoryService(db), user)
                return "ok"
            except ConflictError:
                return "conflict"

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(worker, range(16)))
    assert results.count("ok") == 4  # 4 units, shared between holds and purchases
    with session_factory() as db:
        v = db.get(Vehicle, vehicle_id)
        assert v.reserved + (4 - v.quantity) == 4
        assert 0 <= v.reserved <= v.quantity

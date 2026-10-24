from sqlalchemy import func, select

from app.models import User, Vehicle
from app.seed import VEHICLES, seed


def test_seed_creates_demo_data_and_is_idempotent(db):
    seed(db)
    seed(db)  # second run must not duplicate anything
    assert db.scalar(select(func.count(Vehicle.id))) == len(VEHICLES)
    roles = {u.email: u.role for u in db.scalars(select(User))}
    assert roles == {"admin@demo.com": "admin", "shopper@demo.com": "user"}
    assert any(v.quantity == 0 for v in db.scalars(select(Vehicle)))  # demo includes sold-out cars

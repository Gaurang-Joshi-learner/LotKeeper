"""Shared fixtures. Tests run against a real SQLite *file* (never in-memory) created per test."""
import os

os.environ.setdefault("BCRYPT_ROUNDS", "4")  # must be set before the app imports settings

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, build_engine, get_db
from app.main import create_app
from app.models import User

PASSWORD = "supersecret1"


@pytest.fixture()
def engine(tmp_path):
    eng = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False)


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture()
def client(session_factory):
    app = create_app()

    def _override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app)


def register_and_login(client, db, email, role="user"):
    """Register through the API; optionally promote in the DB; return (headers, user_id)."""
    res = client.post("/api/auth/register", json={"email": email, "password": PASSWORD})
    assert res.status_code == 201, res.text
    if role != "user":
        db.execute(update(User).where(User.email == email).values(role=role))
        db.commit()
    token = client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, res.json()["user"]["id"]


@pytest.fixture()
def user_headers(client, db):
    return register_and_login(client, db, "buyer@example.com")[0]


@pytest.fixture()
def other_headers(client, db):
    return register_and_login(client, db, "other@example.com")[0]


@pytest.fixture()
def admin_headers(client, db):
    return register_and_login(client, db, "admin@example.com", role="admin")[0]


@pytest.fixture()
def make_vehicle(client, admin_headers):
    def _make(**overrides):
        body = {"make": "Toyota", "model": "Corolla", "category": "Sedan", "price": 20000, "quantity": 3}
        body.update(overrides)
        res = client.post("/api/vehicles", json=body, headers=admin_headers)
        assert res.status_code == 201, res.text
        return res.json()

    return _make

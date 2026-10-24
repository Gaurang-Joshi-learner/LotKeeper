from tests.conftest import PASSWORD


def test_register_returns_token_and_never_the_password(client):
    res = client.post("/api/auth/register", json={"email": "New@Example.com", "password": PASSWORD})
    assert res.status_code == 201
    body = res.json()
    assert body["user"] == {"id": body["user"]["id"], "email": "new@example.com", "role": "user"}
    assert body["access_token"]
    assert "password" not in res.text


def test_register_duplicate_email_conflicts(client):
    payload = {"email": "dup@example.com", "password": PASSWORD}
    client.post("/api/auth/register", json=payload)
    assert client.post("/api/auth/register", json=payload).status_code == 409


def test_register_duplicate_email_is_case_insensitive(client):
    client.post("/api/auth/register", json={"email": "a@example.com", "password": PASSWORD})
    res = client.post("/api/auth/register", json={"email": "A@EXAMPLE.COM", "password": PASSWORD})
    assert res.status_code == 409


def test_register_validates_email_and_password(client):
    assert client.post("/api/auth/register", json={"email": "nope", "password": PASSWORD}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "a@b.co", "password": "short"}).status_code == 422


def test_register_cannot_self_assign_admin(client):
    res = client.post("/api/auth/register", json={"email": "evil@example.com", "password": PASSWORD, "role": "admin"})
    assert res.status_code == 422


def test_login_success(client):
    client.post("/api/auth/register", json={"email": "u@example.com", "password": PASSWORD})
    res = client.post("/api/auth/login", json={"email": "u@example.com", "password": PASSWORD})
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"


def test_login_fails_identically_for_wrong_password_and_unknown_email(client):
    client.post("/api/auth/register", json={"email": "u@example.com", "password": PASSWORD})
    wrong = client.post("/api/auth/login", json={"email": "u@example.com", "password": "badbadbad1"})
    unknown = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_me_returns_current_user(client, user_headers):
    res = client.get("/api/auth/me", headers=user_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "buyer@example.com"


def test_protected_routes_reject_missing_and_bad_tokens(client):
    assert client.get("/api/vehicles").status_code == 401
    assert client.get("/api/vehicles", headers={"Authorization": "Bearer garbage"}).status_code == 401
    assert client.get("/api/vehicles", headers={"Authorization": "Basic abc"}).status_code == 401


def test_token_for_deleted_user_is_rejected(client, db, user_headers):
    from sqlalchemy import delete

    from app.models import User

    db.execute(delete(User).where(User.email == "buyer@example.com"))
    db.commit()
    assert client.get("/api/auth/me", headers=user_headers).status_code == 401

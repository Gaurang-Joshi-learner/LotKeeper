def test_create_vehicle(client, user_headers):
    res = client.post(
        "/api/vehicles",
        json={"make": "  Honda ", "model": "Civic", "category": "Sedan", "price": 24999.99, "quantity": 4, "year": 2025, "color": "#112233"},
        headers=user_headers,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["id"] and body["make"] == "Honda"
    assert body["price"] == 24999.99
    assert body["quantity"] == 4 and body["reserved"] == 0 and body["available"] == 4


def test_create_requires_auth(client):
    assert client.post("/api/vehicles", json={}).status_code == 401


def test_create_validation(client, user_headers):
    base = {"make": "A", "model": "B", "category": "C", "price": 1, "quantity": 1}
    for bad in (
        {"price": 0},
        {"price": -5},
        {"quantity": -1},
        {"make": ""},
        {"make": "   "},
        {"color": "red"},
        {"year": 1800},
        {"unknown_field": 1},
    ):
        res = client.post("/api/vehicles", json={**base, **bad}, headers=user_headers)
        assert res.status_code == 422, bad


def test_list_includes_sold_out_vehicles(client, user_headers, make_vehicle):
    make_vehicle(model="InStock", quantity=2)
    make_vehicle(model="SoldOut", quantity=0)
    res = client.get("/api/vehicles", headers=user_headers)
    assert res.status_code == 200
    by_model = {v["model"]: v for v in res.json()}
    assert by_model["InStock"]["available"] == 2
    assert by_model["SoldOut"]["available"] == 0


def test_get_vehicle_and_404(client, user_headers, make_vehicle):
    v = make_vehicle()
    assert client.get(f"/api/vehicles/{v['id']}", headers=user_headers).json()["model"] == "Corolla"
    assert client.get("/api/vehicles/9999", headers=user_headers).status_code == 404


def test_partial_update(client, user_headers, make_vehicle):
    v = make_vehicle(price=20000)
    res = client.put(f"/api/vehicles/{v['id']}", json={"price": 18500.5}, headers=user_headers)
    assert res.status_code == 200
    assert res.json()["price"] == 18500.5
    assert res.json()["model"] == "Corolla"  # untouched


def test_update_validation_and_404(client, user_headers, make_vehicle):
    v = make_vehicle()
    assert client.put(f"/api/vehicles/{v['id']}", json={"price": -1}, headers=user_headers).status_code == 422
    assert client.put(f"/api/vehicles/{v['id']}", json={"make": None}, headers=user_headers).status_code == 409
    assert client.put("/api/vehicles/9999", json={"price": 5}, headers=user_headers).status_code == 404


def test_delete_is_admin_only(client, user_headers, admin_headers, make_vehicle):
    v = make_vehicle()
    assert client.delete(f"/api/vehicles/{v['id']}", headers=user_headers).status_code == 403
    assert client.delete(f"/api/vehicles/{v['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/vehicles/{v['id']}", headers=admin_headers).status_code == 404
    assert client.delete(f"/api/vehicles/{v['id']}", headers=admin_headers).status_code == 404


def test_delete_vehicle_with_active_hold_cleans_up(client, user_headers, admin_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    assert client.post(f"/api/vehicles/{v['id']}/hold", headers=user_headers).status_code == 201
    assert client.delete(f"/api/vehicles/{v['id']}", headers=admin_headers).status_code == 204
    assert client.get("/api/holds/mine", headers=user_headers).json() == []


def test_admin_only_writes_flag(client, user_headers, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "vehicle_write_admin_only", True)
    body = {"make": "A", "model": "B", "category": "C", "price": 1, "quantity": 1}
    assert client.post("/api/vehicles", json=body, headers=user_headers).status_code == 403


def test_quantity_cannot_drop_below_reserved(client, user_headers, admin_headers, make_vehicle):
    v = make_vehicle(quantity=2)
    client.post(f"/api/vehicles/{v['id']}/hold", headers=user_headers)
    res = client.put(f"/api/vehicles/{v['id']}", json={"quantity": 0}, headers=admin_headers)
    assert res.status_code == 409

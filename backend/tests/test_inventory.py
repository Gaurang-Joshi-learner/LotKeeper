def test_purchase_decrements_quantity(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=3)
    res = client.post(f"/api/vehicles/{v['id']}/purchase", headers=user_headers)
    assert res.status_code == 200
    assert res.json()["quantity"] == 2 and res.json()["available"] == 2


def test_purchase_last_unit_then_sold_out(client, user_headers, other_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    assert client.post(f"/api/vehicles/{v['id']}/purchase", headers=user_headers).status_code == 200
    res = client.post(f"/api/vehicles/{v['id']}/purchase", headers=other_headers)
    assert res.status_code == 409
    assert "out of stock" in res.json()["detail"]
    assert client.get(f"/api/vehicles/{v['id']}", headers=user_headers).json()["quantity"] == 0


def test_purchase_never_goes_negative(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=0)
    assert client.post(f"/api/vehicles/{v['id']}/purchase", headers=user_headers).status_code == 409
    assert client.get(f"/api/vehicles/{v['id']}", headers=user_headers).json()["quantity"] == 0


def test_purchase_unknown_vehicle_404(client, user_headers):
    assert client.post("/api/vehicles/999/purchase", headers=user_headers).status_code == 404


def test_purchase_requires_auth(client, make_vehicle):
    v = make_vehicle()
    assert client.post(f"/api/vehicles/{v['id']}/purchase").status_code == 401


def test_restock_is_admin_only(client, user_headers, admin_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    assert client.post(f"/api/vehicles/{v['id']}/restock", json={"quantity": 5}, headers=user_headers).status_code == 403
    res = client.post(f"/api/vehicles/{v['id']}/restock", json={"quantity": 5}, headers=admin_headers)
    assert res.status_code == 200 and res.json()["quantity"] == 6


def test_restock_validation_and_404(client, admin_headers, make_vehicle):
    v = make_vehicle()
    for bad in (0, -3):
        assert client.post(f"/api/vehicles/{v['id']}/restock", json={"quantity": bad}, headers=admin_headers).status_code == 422
    assert client.post("/api/vehicles/999/restock", json={"quantity": 1}, headers=admin_headers).status_code == 404


def test_restock_revives_sold_out_vehicle(client, user_headers, admin_headers, make_vehicle):
    v = make_vehicle(quantity=0)
    client.post(f"/api/vehicles/{v['id']}/restock", json={"quantity": 2}, headers=admin_headers)
    assert client.post(f"/api/vehicles/{v['id']}/purchase", headers=user_headers).status_code == 200

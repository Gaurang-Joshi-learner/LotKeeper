from datetime import timedelta

from sqlalchemy import update

from app.models import Hold, utcnow


def events(client, headers):
    res = client.get("/api/admin/events", headers=headers)
    assert res.status_code == 200
    return res.json()


def test_events_are_admin_only(client, user_headers, admin_headers):
    assert client.get("/api/admin/events", headers=user_headers).status_code == 403
    assert client.get("/api/admin/analytics", headers=user_headers).status_code == 403
    assert client.get("/api/admin/events").status_code == 401


def test_every_mutation_is_logged_newest_first(client, user_headers, admin_headers, make_vehicle):
    v = make_vehicle(quantity=2)
    client.post(f"/api/vehicles/{v['id']}/purchase", headers=user_headers)
    client.post(f"/api/vehicles/{v['id']}/restock", json={"quantity": 4}, headers=admin_headers)
    client.put(f"/api/vehicles/{v['id']}", json={"price": 19000}, headers=admin_headers)
    log = events(client, admin_headers)
    assert [e["type"] for e in log] == ["vehicle_updated", "restock", "purchase", "vehicle_created"]
    purchase = log[2]
    assert purchase["user_email"] == "buyer@example.com"
    assert purchase["delta"] == -1 and purchase["amount"] == 20000
    assert purchase["vehicle_label"] == "Toyota Corolla"


def test_failed_purchase_leaves_no_event(client, user_headers, admin_headers, make_vehicle):
    v = make_vehicle(quantity=0)
    client.post(f"/api/vehicles/{v['id']}/purchase", headers=user_headers)
    assert [e["type"] for e in events(client, admin_headers)] == ["vehicle_created"]


def test_history_survives_vehicle_deletion(client, admin_headers, make_vehicle):
    v = make_vehicle()
    client.delete(f"/api/vehicles/{v['id']}", headers=admin_headers)
    log = events(client, admin_headers)
    assert log[0]["type"] == "vehicle_deleted" and log[0]["vehicle_label"] == "Toyota Corolla"


def test_hold_lifecycle_is_logged(client, db, user_headers, admin_headers, make_vehicle):
    v = make_vehicle(quantity=2)
    client.post(f"/api/vehicles/{v['id']}/hold", headers=user_headers)
    db.execute(update(Hold).values(expires_at=utcnow() - timedelta(minutes=1)))
    db.commit()
    client.get("/api/vehicles", headers=user_headers)
    types = [e["type"] for e in events(client, admin_headers)]
    assert types[:2] == ["hold_expired", "hold_placed"]


def test_analytics_totals(client, user_headers, admin_headers, make_vehicle):
    a = make_vehicle(model="A", category="Sedan", price=10000, quantity=3)
    make_vehicle(model="B", category="SUV", price=30000, quantity=1)
    client.post(f"/api/vehicles/{a['id']}/purchase", headers=user_headers)
    client.post(f"/api/vehicles/{a['id']}/hold", headers=user_headers)
    data = client.get("/api/admin/analytics", headers=admin_headers).json()
    assert data["vehicle_count"] == 2
    assert data["units_in_stock"] == 3  # (3-1) + 1
    assert data["units_reserved"] == 1
    assert data["inventory_value"] == 2 * 10000 + 30000
    assert data["units_sold"] == 1 and data["revenue"] == 10000
    cats = {c["category"]: c for c in data["by_category"]}
    assert cats["SUV"]["value"] == 30000 and cats["Sedan"]["units"] == 2
    assert len(data["purchases_by_day"]) == 14
    assert data["purchases_by_day"][-1]["purchases"] == 1
    assert {i["label"] for i in data["low_stock"]} == {"Toyota A", "Toyota B"}


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}

"""Each user's purchases belong to them alone."""
from tests.conftest import register_and_login


def buy(client, headers, vehicle_id):
    res = client.post(f"/api/vehicles/{vehicle_id}/purchase", headers=headers)
    assert res.status_code == 200, res.text


def mine(client, headers):
    res = client.get("/api/orders/mine", headers=headers)
    assert res.status_code == 200
    return res.json()


def test_purchase_creates_an_order_for_the_buyer(client, user_headers, make_vehicle):
    v = make_vehicle(make="Honda", model="Civic", price=24500.5, color="#112233")
    buy(client, user_headers, v["id"])
    [order] = mine(client, user_headers)
    assert order["vehicle_label"] == "Honda Civic"
    assert order["price"] == 24500.5 and order["color"] == "#112233" and order["from_hold"] is False


def test_users_only_see_their_own_orders(client, user_headers, other_headers, make_vehicle):
    a, b = make_vehicle(model="A"), make_vehicle(model="B")
    buy(client, user_headers, a["id"])
    buy(client, other_headers, b["id"])
    buy(client, other_headers, b["id"])
    assert [o["vehicle_label"] for o in mine(client, user_headers)] == ["Toyota A"]
    assert [o["vehicle_label"] for o in mine(client, other_headers)] == ["Toyota B", "Toyota B"]


def test_new_user_starts_with_no_orders(client, user_headers, other_headers, make_vehicle):
    buy(client, user_headers, make_vehicle()["id"])
    assert mine(client, other_headers) == []


def test_orders_require_auth(client):
    assert client.get("/api/orders/mine").status_code == 401


def test_failed_purchase_creates_no_order(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=0)
    client.post(f"/api/vehicles/{v['id']}/purchase", headers=user_headers)
    assert mine(client, user_headers) == []


def test_purchase_from_hold_is_flagged(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    client.post(f"/api/vehicles/{v['id']}/hold", headers=user_headers)
    buy(client, user_headers, v["id"])
    assert mine(client, user_headers)[0]["from_hold"] is True


def test_order_keeps_the_price_paid_after_a_price_change(client, user_headers, admin_headers, make_vehicle):
    v = make_vehicle(price=20000)
    buy(client, user_headers, v["id"])
    client.put(f"/api/vehicles/{v['id']}", json={"price": 99999}, headers=admin_headers)
    assert mine(client, user_headers)[0]["price"] == 20000


def test_order_survives_vehicle_deletion(client, user_headers, admin_headers, make_vehicle):
    v = make_vehicle()
    buy(client, user_headers, v["id"])
    client.delete(f"/api/vehicles/{v['id']}", headers=admin_headers)
    assert mine(client, user_headers)[0]["vehicle_label"] == "Toyota Corolla"


def test_admin_sees_every_order_with_buyer_email(client, db, user_headers, other_headers, admin_headers, make_vehicle):
    v = make_vehicle(quantity=3)
    buy(client, user_headers, v["id"])
    buy(client, other_headers, v["id"])
    res = client.get("/api/admin/orders", headers=admin_headers)
    assert res.status_code == 200
    assert {o["user_email"] for o in res.json()} == {"buyer@example.com", "other@example.com"}


def test_customers_cannot_read_the_admin_order_list(client, user_headers):
    assert client.get("/api/admin/orders", headers=user_headers).status_code == 403

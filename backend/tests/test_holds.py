from datetime import timedelta

from sqlalchemy import update

from app.models import Hold, utcnow


def hold(client, headers, vid):
    return client.post(f"/api/vehicles/{vid}/hold", headers=headers)


def get(client, headers, vid):
    return client.get(f"/api/vehicles/{vid}", headers=headers).json()


def expire_holds_in_db(db):
    db.execute(update(Hold).values(expires_at=utcnow() - timedelta(minutes=1)))
    db.commit()


def test_hold_reduces_available_but_not_quantity(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=3)
    res = hold(client, user_headers, v["id"])
    assert res.status_code == 201
    assert res.json()["status"] == "active"
    now = get(client, user_headers, v["id"])
    assert (now["quantity"], now["reserved"], now["available"]) == (3, 1, 2)


def test_cannot_hold_when_nothing_available(client, user_headers, other_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    assert hold(client, user_headers, v["id"]).status_code == 201
    assert hold(client, other_headers, v["id"]).status_code == 409


def test_cannot_hold_twice(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=3)
    hold(client, user_headers, v["id"])
    assert hold(client, user_headers, v["id"]).status_code == 409
    assert get(client, user_headers, v["id"])["reserved"] == 1


def test_hold_unknown_vehicle_404(client, user_headers):
    assert hold(client, user_headers, 999).status_code == 404


def test_release_restores_availability(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=2)
    hold(client, user_headers, v["id"])
    assert client.delete(f"/api/vehicles/{v['id']}/hold", headers=user_headers).status_code == 204
    assert get(client, user_headers, v["id"])["available"] == 2
    assert client.delete(f"/api/vehicles/{v['id']}/hold", headers=user_headers).status_code == 404


def test_can_hold_again_after_release(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    hold(client, user_headers, v["id"])
    client.delete(f"/api/vehicles/{v['id']}/hold", headers=user_headers)
    assert hold(client, user_headers, v["id"]).status_code == 201


def test_my_holds_lists_only_my_active_holds(client, user_headers, other_headers, make_vehicle):
    a, b = make_vehicle(model="A"), make_vehicle(model="B")
    hold(client, user_headers, a["id"])
    hold(client, other_headers, b["id"])
    mine = client.get("/api/holds/mine", headers=user_headers).json()
    assert [h["vehicle_id"] for h in mine] == [a["id"]]


def test_purchase_consumes_own_hold(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=2)
    hold(client, user_headers, v["id"])
    res = client.post(f"/api/vehicles/{v['id']}/purchase", headers=user_headers)
    assert res.status_code == 200
    body = res.json()
    assert (body["quantity"], body["reserved"], body["available"]) == (1, 0, 1)
    assert client.get("/api/holds/mine", headers=user_headers).json() == []


def test_purchase_with_explicit_hold_id(client, user_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    hid = hold(client, user_headers, v["id"]).json()["id"]
    res = client.post(f"/api/vehicles/{v['id']}/purchase", json={"hold_id": hid}, headers=user_headers)
    assert res.status_code == 200 and res.json()["quantity"] == 0


def test_cannot_use_someone_elses_hold(client, user_headers, other_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    hid = hold(client, user_headers, v["id"]).json()["id"]
    res = client.post(f"/api/vehicles/{v['id']}/purchase", json={"hold_id": hid}, headers=other_headers)
    assert res.status_code == 404


def test_held_last_unit_cannot_be_bought_by_someone_else(client, user_headers, other_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    hold(client, user_headers, v["id"])
    assert client.post(f"/api/vehicles/{v['id']}/purchase", headers=other_headers).status_code == 409


def test_expired_hold_frees_the_unit(client, db, user_headers, other_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    hold(client, user_headers, v["id"])
    expire_holds_in_db(db)
    # listing lazily sweeps, so the unit is available to others again
    assert get(client, other_headers, v["id"])["reserved"] == 1  # not yet swept by a plain GET
    assert client.get("/api/vehicles", headers=other_headers).json()[0]["available"] == 1
    assert client.post(f"/api/vehicles/{v['id']}/purchase", headers=other_headers).status_code == 200


def test_expired_hold_cannot_be_used(client, db, user_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    hid = hold(client, user_headers, v["id"]).json()["id"]
    expire_holds_in_db(db)
    res = client.post(f"/api/vehicles/{v['id']}/purchase", json={"hold_id": hid}, headers=user_headers)
    assert res.status_code == 409


def test_expired_hold_disappears_from_my_holds(client, db, user_headers, make_vehicle):
    v = make_vehicle(quantity=1)
    hold(client, user_headers, v["id"])
    expire_holds_in_db(db)
    assert client.get("/api/holds/mine", headers=user_headers).json() == []
    assert get(client, user_headers, v["id"])["reserved"] == 0

import pytest


@pytest.fixture()
def lot(make_vehicle):
    make_vehicle(make="Toyota", model="Corolla", category="Sedan", price=21000, quantity=3)
    make_vehicle(make="Toyota", model="RAV4", category="SUV", price=34000, quantity=0)
    make_vehicle(make="Honda", model="Civic", category="Sedan", price=25000, quantity=2)
    make_vehicle(make="BMW", model="X5", category="SUV", price=65000, quantity=1)


def names(res):
    assert res.status_code == 200, res.text
    return [f"{v['make']} {v['model']}" for v in res.json()]


def test_search_without_filters_returns_all(client, user_headers, lot):
    assert len(names(client.get("/api/vehicles/search", headers=user_headers))) == 4


def test_filter_by_make_is_case_insensitive_and_partial(client, user_headers, lot):
    assert set(names(client.get("/api/vehicles/search?make=toy", headers=user_headers))) == {"Toyota Corolla", "Toyota RAV4"}


def test_filter_by_model(client, user_headers, lot):
    assert names(client.get("/api/vehicles/search?model=civ", headers=user_headers)) == ["Honda Civic"]


def test_filter_by_category(client, user_headers, lot):
    assert set(names(client.get("/api/vehicles/search?category=suv", headers=user_headers))) == {"Toyota RAV4", "BMW X5"}


def test_price_range_is_inclusive(client, user_headers, lot):
    res = client.get("/api/vehicles/search?min_price=25000&max_price=34000", headers=user_headers)
    assert set(names(res)) == {"Honda Civic", "Toyota RAV4"}


def test_combined_filters(client, user_headers, lot):
    res = client.get("/api/vehicles/search?make=toyota&category=sedan&max_price=22000", headers=user_headers)
    assert names(res) == ["Toyota Corolla"]


def test_in_stock_filter_hides_sold_out(client, user_headers, lot):
    assert "Toyota RAV4" not in names(client.get("/api/vehicles/search?in_stock=true", headers=user_headers))


def test_free_text_query_matches_any_field(client, user_headers, lot):
    assert set(names(client.get("/api/vehicles/search?q=suv", headers=user_headers))) == {"Toyota RAV4", "BMW X5"}


def test_sorting(client, user_headers, lot):
    asc = [v["price"] for v in client.get("/api/vehicles/search?sort=price_asc", headers=user_headers).json()]
    desc = [v["price"] for v in client.get("/api/vehicles/search?sort=price_desc", headers=user_headers).json()]
    assert asc == sorted(asc) and desc == sorted(desc, reverse=True)


def test_no_match_returns_empty_list(client, user_headers, lot):
    assert client.get("/api/vehicles/search?make=ferrari", headers=user_headers).json() == []


def test_wildcards_are_treated_literally(client, user_headers, lot):
    assert client.get("/api/vehicles/search?make=%25", headers=user_headers).json() == []


def test_invalid_params_are_rejected(client, user_headers, lot):
    assert client.get("/api/vehicles/search?min_price=50&max_price=10", headers=user_headers).status_code == 422
    assert client.get("/api/vehicles/search?sort=sideways", headers=user_headers).status_code == 422
    assert client.get("/api/vehicles/search?min_price=-1", headers=user_headers).status_code == 422


def test_search_requires_auth(client):
    assert client.get("/api/vehicles/search").status_code == 401


def test_pagination(client, user_headers, lot):
    page = client.get("/api/vehicles/search?sort=name&limit=2&offset=1", headers=user_headers).json()
    assert len(page) == 2

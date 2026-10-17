import pytest

from app.models.enums import UserRole
from tests.conftest import DEFAULT_PASSWORD

API = "/api/v1"


def _headers(client, make_user, role: UserRole) -> dict[str, str]:
    user = make_user(role)
    tokens = client.post(
        f"{API}/auth/login", json={"email": user.email, "password": DEFAULT_PASSWORD}
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def staff(client, make_user):
    return _headers(client, make_user, UserRole.LIBRARIAN)


@pytest.fixture
def member(client, make_user):
    return _headers(client, make_user, UserRole.MEMBER)


@pytest.fixture
def book_payload(client, staff):
    author = client.post(f"{API}/authors", json={"full_name": "Fyodor Dostoyevski"}, headers=staff)
    category = client.post(f"{API}/categories", json={"name": "Roman"}, headers=staff)
    publisher = client.post(f"{API}/publishers", json={"name": "Can Yayınları"}, headers=staff)
    return {
        "title": "Suç ve Ceza",
        "isbn": "9789750719387",
        "publisher_id": publisher.json()["id"],
        "publish_year": 1866,
        "author_ids": [author.json()["id"]],
        "category_ids": [category.json()["id"]],
    }


def test_book_lifecycle(client, staff, book_payload):
    created = client.post(f"{API}/books", json=book_payload, headers=staff)
    assert created.status_code == 201
    book = created.json()
    assert book["authors"][0]["full_name"] == "Fyodor Dostoyevski"
    assert book["publisher"]["name"] == "Can Yayınları"
    assert (book["copy_count"], book["available_count"]) == (0, 0)

    copy = client.post(
        f"{API}/books/{book['id']}/copies", json={"shelf_location": "A-03-2"}, headers=staff
    )
    assert copy.status_code == 201
    assert copy.json()["barcode"] == f"KTP-{book['id']:04d}-01"
    assert copy.json()["status"] == "available"

    listing = client.get(f"{API}/books", params={"q": "suç", "available": True}, headers=staff)
    assert listing.status_code == 200
    page = listing.json()
    assert page["total"] == 1
    assert page["items"][0]["available_count"] == 1

    by_barcode = client.get(f"{API}/copies/barcode/{copy.json()['barcode']}", headers=staff)
    assert by_barcode.json()["book"]["title"] == "Suç ve Ceza"

    updated = client.put(
        f"{API}/copies/{copy.json()['id']}",
        json={"status": "maintenance", "shelf_location": "A-03-2"},
        headers=staff,
    )
    assert updated.json()["status"] == "maintenance"

    detail = client.get(f"{API}/books/{book['id']}", headers=staff).json()
    assert (detail["copy_count"], detail["available_count"]) == (1, 0)

    assert client.delete(f"{API}/books/{book['id']}", headers=staff).status_code == 204
    assert client.get(f"{API}/books/{book['id']}", headers=staff).status_code == 404


def test_member_can_read_catalog_but_not_write(client, staff, member, book_payload):
    book = client.post(f"{API}/books", json=book_payload, headers=staff).json()

    assert client.get(f"{API}/books", headers=member).status_code == 200
    assert client.get(f"{API}/books/{book['id']}", headers=member).status_code == 200
    assert client.get(f"{API}/categories", headers=member).status_code == 200

    assert client.post(f"{API}/books", json=book_payload, headers=member).status_code == 403
    assert client.get(f"{API}/books/{book['id']}/copies", headers=member).status_code == 403
    assert client.post(f"{API}/authors", json={"full_name": "X"}, headers=member).status_code == 403


def test_catalog_requires_login(client):
    assert client.get(f"{API}/books").status_code == 401


def test_book_validation_errors(client, staff, book_payload):
    bad_isbn = client.post(f"{API}/books", json=book_payload | {"isbn": "123"}, headers=staff)
    assert bad_isbn.status_code == 400
    assert bad_isbn.json()["error"]["code"] == "INVALID_ISBN"

    no_author = client.post(f"{API}/books", json=book_payload | {"author_ids": []}, headers=staff)
    assert no_author.status_code == 422

    client.post(f"{API}/books", json=book_payload, headers=staff)
    duplicate = client.post(f"{API}/books", json=book_payload, headers=staff)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "ISBN_EXISTS"


def test_lookup_endpoints(client, staff):
    root = client.post(f"{API}/categories", json={"name": "Edebiyat"}, headers=staff).json()
    client.post(f"{API}/categories", json={"name": "Roman", "parent_id": root["id"]}, headers=staff)
    categories = client.get(f"{API}/categories", headers=staff).json()
    assert [c["name"] for c in categories] == ["Edebiyat", "Roman"]

    client.post(f"{API}/authors", json={"full_name": "Orhan Pamuk"}, headers=staff)
    authors = client.get(f"{API}/authors", params={"q": "pamuk"}, headers=staff).json()
    assert authors["total"] == 1

    in_use = client.delete(f"{API}/categories/{root['id']}", headers=staff)
    assert in_use.status_code == 409
    assert in_use.json()["error"]["code"] == "ENTITY_IN_USE"

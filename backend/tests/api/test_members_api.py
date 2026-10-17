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


PAYLOAD = {
    "email": "ayse@ornek.com",
    "full_name": "Ayşe Yılmaz",
    "password": "Parola123!",
    "phone": "0532 000 00 00",
    "address": "İstanbul",
    "member_type": "student",
    "membership_start": "2026-01-01",
    "membership_end": "2099-01-01",
}


def test_member_lifecycle(client, staff):
    created = client.post(f"{API}/members", json=PAYLOAD, headers=staff)
    assert created.status_code == 201
    member = created.json()
    assert member["member_no"] == "UYE-000001"
    assert member["status"] == "active"
    assert member["active_loan_count"] == 0
    assert member["unpaid_fine_total"] == "0.00"
    assert "password" not in member

    # yeni üye kendi hesabıyla giriş yapabilir
    login = client.post(
        f"{API}/auth/login", json={"email": PAYLOAD["email"], "password": PAYLOAD["password"]}
    )
    assert login.status_code == 200

    update = {k: v for k, v in PAYLOAD.items() if k != "password"} | {"phone": "0533 111 11 11"}
    updated = client.put(f"{API}/members/{member['id']}", json=update, headers=staff)
    assert updated.json()["phone"] == "0533 111 11 11"

    suspended = client.post(f"{API}/members/{member['id']}/suspend", headers=staff)
    assert suspended.json()["status"] == "suspended"
    listing = client.get(f"{API}/members", params={"status": "suspended"}, headers=staff).json()
    assert [m["member_no"] for m in listing["items"]] == ["UYE-000001"]

    activated = client.post(f"{API}/members/{member['id']}/activate", headers=staff)
    assert activated.json()["status"] == "active"

    for path in ("loans", "fines", "reservations"):
        response = client.get(f"{API}/members/{member['id']}/{path}", headers=staff)
        assert response.status_code == 200
        assert response.json() == []


def test_member_validation_errors(client, staff):
    client.post(f"{API}/members", json=PAYLOAD, headers=staff)

    duplicate = client.post(f"{API}/members", json=PAYLOAD, headers=staff)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_EXISTS"

    bad_dates = client.post(
        f"{API}/members",
        json=PAYLOAD | {"email": "x@ornek.com", "membership_end": "2025-01-01"},
        headers=staff,
    )
    assert bad_dates.json()["error"]["code"] == "INVALID_DATE_RANGE"

    short_password = client.post(
        f"{API}/members", json=PAYLOAD | {"email": "y@ornek.com", "password": "kisa"}, headers=staff
    )
    assert short_password.status_code == 422


def test_members_are_staff_only(client, make_user):
    member = _headers(client, make_user, UserRole.MEMBER)
    assert client.get(f"{API}/members", headers=member).status_code == 403
    assert client.post(f"{API}/members", json=PAYLOAD, headers=member).status_code == 403


def test_unknown_member(client, staff):
    response = client.get(f"{API}/members/999", headers=staff)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

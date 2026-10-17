"""Üye paneli; üye rolü başka üyenin verisine erişemez (403)."""

import pytest

from app.core.security import hash_password
from app.models.enums import UserRole
from tests.conftest import DEFAULT_PASSWORD
from tests.factories import World

API = "/api/v1"


@pytest.fixture
def w(db):
    return World(db)


def _member_login(client, db, member) -> dict[str, str]:
    member.user.password_hash = hash_password(DEFAULT_PASSWORD)
    db.commit()
    tokens = client.post(
        f"{API}/auth/login", json={"email": member.user.email, "password": DEFAULT_PASSWORD}
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_member_sees_only_own_data(client, db, w):
    ayse, ali = w.member(), w.member()
    ayse_loan = w.issue(ayse, w.book()[0])
    w.issue(ali, w.book()[0])
    headers = _member_login(client, db, ayse)

    profile = client.get(f"{API}/me/profile", headers=headers).json()
    assert profile["member_no"] == ayse.member_no
    loans = client.get(f"{API}/me/loans", headers=headers).json()
    assert [loan["id"] for loan in loans] == [ayse_loan.id]
    assert client.get(f"{API}/me/fines", headers=headers).json() == []


def test_member_cannot_access_other_members(client, db, w):
    ayse, ali = w.member(), w.member()
    ali_loan = w.issue(ali, w.book()[0])
    headers = _member_login(client, db, ayse)

    assert client.get(f"{API}/members/{ali.id}", headers=headers).status_code == 403
    assert client.get(f"{API}/members/{ali.id}/loans", headers=headers).status_code == 403
    assert client.get(f"{API}/loans", headers=headers).status_code == 403
    renew = client.post(f"{API}/me/loans/{ali_loan.id}/renew", headers=headers)
    assert renew.status_code == 403
    assert renew.json()["error"]["code"] == "FORBIDDEN"


def test_member_renews_own_loan(client, db, w):
    ayse = w.member()
    loan = w.issue(ayse, w.book()[0])
    headers = _member_login(client, db, ayse)

    renewed = client.post(f"{API}/me/loans/{loan.id}/renew", headers=headers)
    assert renewed.status_code == 200
    assert renewed.json()["renew_count"] == 1


def test_member_reservations(client, db, w):
    holder, ayse, ali = w.member(), w.member(), w.member()
    [copy] = w.book()
    w.issue(holder, copy)
    headers = _member_login(client, db, ayse)

    created = client.post(f"{API}/me/reservations", json={"book_id": copy.book_id}, headers=headers)
    assert created.status_code == 201
    assert created.json()["queue_position"] == 1
    assert [r["id"] for r in client.get(f"{API}/me/reservations", headers=headers).json()] == [
        created.json()["id"]
    ]

    ali_headers = _member_login(client, db, ali)
    forbidden = client.delete(f"{API}/me/reservations/{created.json()['id']}", headers=ali_headers)
    assert forbidden.status_code == 403

    cancelled = client.delete(f"{API}/me/reservations/{created.json()['id']}", headers=headers)
    assert cancelled.json()["status"] == "cancelled"


def test_member_can_search_catalog(client, db, w):
    w.book()
    headers = _member_login(client, db, w.member())
    assert client.get(f"{API}/books", params={"q": "Kitap"}, headers=headers).json()["total"] == 1


def test_staff_cannot_use_member_panel(client, make_user):
    user = make_user(UserRole.LIBRARIAN)
    tokens = client.post(
        f"{API}/auth/login", json={"email": user.email, "password": DEFAULT_PASSWORD}
    ).json()
    response = client.get(
        f"{API}/me/loans", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 403

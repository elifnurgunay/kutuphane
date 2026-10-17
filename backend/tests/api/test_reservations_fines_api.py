from datetime import timedelta

import pytest

from app.models.enums import UserRole
from tests.conftest import DEFAULT_PASSWORD
from tests.factories import World

API = "/api/v1"


def _login(client, user) -> dict[str, str]:
    tokens = client.post(
        f"{API}/auth/login", json={"email": user.email, "password": DEFAULT_PASSWORD}
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def w(db):
    return World(db)


@pytest.fixture
def staff(client, make_user):
    return _login(client, make_user(UserRole.LIBRARIAN))


@pytest.fixture
def admin(client, make_user):
    return _login(client, make_user(UserRole.ADMIN))


def test_reservation_lifecycle(client, staff, w):
    [copy] = w.book()
    w.issue(w.member(), copy)
    a, b = w.member(), w.member()

    first = client.post(
        f"{API}/reservations", json={"book_id": copy.book_id, "member_id": a.id}, headers=staff
    )
    assert first.status_code == 201
    assert first.json()["queue_position"] == 1
    assert first.json()["member_no"] == a.member_no
    second = client.post(
        f"{API}/reservations", json={"book_id": copy.book_id, "member_id": b.id}, headers=staff
    ).json()
    assert second["queue_position"] == 2

    duplicate = client.post(
        f"{API}/reservations", json={"book_id": copy.book_id, "member_id": a.id}, headers=staff
    )
    assert duplicate.json()["error"]["code"] == "RESERVATION_EXISTS"

    queue = client.get(f"{API}/reservations", params={"book_id": copy.book_id}, headers=staff)
    assert [r["queue_position"] for r in queue.json()["items"]] == [1, 2]

    cancelled = client.delete(f"{API}/reservations/{first.json()['id']}", headers=staff)
    assert cancelled.json()["status"] == "cancelled"
    assert (
        client.get(f"{API}/reservations", params={"status": "waiting"}, headers=staff).json()[
            "items"
        ][0]["queue_position"]
        == 1
    )


def test_available_book_cannot_be_reserved(client, staff, w):
    [copy] = w.book()
    response = client.post(
        f"{API}/reservations",
        json={"book_id": copy.book_id, "member_id": w.member().id},
        headers=staff,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BOOK_AVAILABLE_NO_RESERVATION"


def test_return_response_reports_reservation(client, staff, w):
    [copy] = w.book()
    loan = w.issue(w.member(), copy)
    waiting = w.member()
    client.post(
        f"{API}/reservations",
        json={"book_id": copy.book_id, "member_id": waiting.id},
        headers=staff,
    )

    returned = client.post(f"{API}/loans/{loan.id}/return", headers=staff).json()
    assert returned["reserved_for"]["member_no"] == waiting.member_no
    ready = client.get(f"{API}/reservations", params={"status": "ready"}, headers=staff).json()
    assert ready["items"][0]["assigned_barcode"] == copy.barcode


def _make_fine(w):
    loan = w.issue(w.member(), w.book()[0])
    return w.return_(loan, today=loan.due_date + timedelta(days=5)).fines[0]


def test_fines_pay_and_list(client, staff, w):
    fine = _make_fine(w)
    _make_fine(w)

    unpaid = client.get(f"{API}/fines", params={"status": "unpaid"}, headers=staff).json()
    assert unpaid["total"] == 2
    assert unpaid["total_amount"] == "20.00"
    assert unpaid["items"][0]["book_title"].startswith("Kitap")

    paid = client.post(f"{API}/fines/{fine.id}/pay", headers=staff)
    assert paid.json()["status"] == "paid"
    again = client.post(f"{API}/fines/{fine.id}/pay", headers=staff)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "FINE_NOT_UNPAID"


def test_only_admin_can_waive(client, staff, admin, w):
    fine = _make_fine(w)

    forbidden = client.post(f"{API}/fines/{fine.id}/waive", headers=staff)
    assert forbidden.status_code == 403
    waived = client.post(f"{API}/fines/{fine.id}/waive", headers=admin)
    assert waived.json()["status"] == "waived"


def test_members_cannot_use_staff_endpoints(client, make_user):
    headers = _login(client, make_user(UserRole.MEMBER))
    assert client.get(f"{API}/reservations", headers=headers).status_code == 403
    assert client.get(f"{API}/fines", headers=headers).status_code == 403

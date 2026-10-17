from datetime import date

import pytest

from app.models import Book, BookCopy, Member, User
from app.models.enums import MemberType, UserRole
from tests.conftest import DEFAULT_PASSWORD

API = "/api/v1"


def _login(client, user) -> dict[str, str]:
    tokens = client.post(
        f"{API}/auth/login", json={"email": user.email, "password": DEFAULT_PASSWORD}
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def staff(client, make_user):
    return _login(client, make_user(UserRole.LIBRARIAN))


@pytest.fixture
def member(db):
    member = Member(
        user=User(
            email="ayse@test.local", password_hash="x", full_name="Ayşe", role=UserRole.MEMBER
        ),
        member_no="UYE-000001",
        member_type=MemberType.STUDENT,
        membership_start=date(2026, 1, 1),
        membership_end=date(2099, 1, 1),
    )
    db.add(member)
    db.commit()
    return member


@pytest.fixture
def copies(db):
    items = [BookCopy(book=Book(title=f"Kitap {i}"), barcode=f"KTP-000{i}-01") for i in range(1, 6)]
    db.add_all(items)
    db.commit()
    return items


def test_issue_renew_return(client, staff, member, copies):
    issued = client.post(
        f"{API}/loans", json={"member_id": member.id, "barcode": "ktp-0001-01"}, headers=staff
    )
    assert issued.status_code == 201
    loan = issued.json()
    assert loan["book_title"] == "Kitap 1"
    assert loan["member_no"] == "UYE-000001"
    assert loan["status"] == "active"

    open_loans = client.get(
        f"{API}/loans", params={"status": "open", "member_id": member.id}, headers=staff
    ).json()
    assert [item["id"] for item in open_loans["items"]] == [loan["id"]]
    by_barcode = client.get(
        f"{API}/loans", params={"barcode": "KTP-0001-01", "status": "open"}, headers=staff
    )
    assert by_barcode.json()["total"] == 1

    renewed = client.post(f"{API}/loans/{loan['id']}/renew", headers=staff)
    assert renewed.json()["renew_count"] == 1
    again = client.post(f"{API}/loans/{loan['id']}/renew", headers=staff)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "RENEW_LIMIT"

    returned = client.post(f"{API}/loans/{loan['id']}/return", headers=staff)
    assert returned.status_code == 200
    body = returned.json()
    assert body["loan"]["status"] == "returned"
    assert body["fines"] == []
    assert body["reserved_for"] is None


def test_limit_error_message(client, staff, member, copies):
    for copy in copies[:3]:
        client.post(
            f"{API}/loans", json={"member_id": member.id, "barcode": copy.barcode}, headers=staff
        )

    response = client.post(
        f"{API}/loans", json={"member_id": member.id, "barcode": copies[3].barcode}, headers=staff
    )
    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "LOAN_LIMIT_EXCEEDED", "message": "Üye ödünç limitine ulaştı (3/3)."}
    }

    eligibility = client.get(f"{API}/loans/eligibility/{member.id}", headers=staff).json()
    assert eligibility["can_borrow"] is False
    assert eligibility["active_loan_count"] == 3
    assert eligibility["loan_limit"] == 3
    assert [p["code"] for p in eligibility["problems"]] == ["LOAN_LIMIT_EXCEEDED"]


def test_damaged_return_and_lost(client, staff, member, copies):
    first = client.post(
        f"{API}/loans", json={"member_id": member.id, "barcode": copies[0].barcode}, headers=staff
    ).json()
    returned = client.post(
        f"{API}/loans/{first['id']}/return",
        json={"damaged": True, "damage_fine": "25", "notes": "Islanmış"},
        headers=staff,
    ).json()
    assert [(f["reason"], f["amount"]) for f in returned["fines"]] == [("damaged", "25.00")]

    second = client.post(
        f"{API}/loans", json={"member_id": member.id, "barcode": copies[1].barcode}, headers=staff
    ).json()
    lost = client.post(f"{API}/loans/{second['id']}/mark-lost", headers=staff).json()
    assert lost["loan"]["status"] == "lost"
    assert (lost["fine"]["reason"], lost["fine"]["amount"]) == ("lost", "150.00")

    lost_list = client.get(f"{API}/loans", params={"status": "lost"}, headers=staff).json()
    assert lost_list["total"] == 1


def test_loans_are_staff_only(client, make_user, member):
    headers = _login(client, make_user(UserRole.MEMBER))
    assert client.get(f"{API}/loans", headers=headers).status_code == 403
    response = client.post(
        f"{API}/loans", json={"member_id": member.id, "barcode": "KTP-0001-01"}, headers=headers
    )
    assert response.status_code == 403

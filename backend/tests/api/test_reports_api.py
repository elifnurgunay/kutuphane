from datetime import timedelta

import pytest

from app.models.enums import UserRole
from tests.conftest import DEFAULT_PASSWORD
from tests.factories import TODAY, World

API = "/api/v1/reports"


@pytest.fixture
def staff(client, make_user):
    user = make_user(UserRole.LIBRARIAN)
    tokens = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": DEFAULT_PASSWORD}
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def data(db):
    w = World(db)
    w.issue(w.member(), w.book()[0], today=TODAY - timedelta(days=40))  # gecikmiş
    return w


def test_dashboard_endpoint(client, staff, data):
    body = client.get(f"{API}/dashboard", headers=staff).json()
    assert body["total_books"] == 1
    assert body["open_loans"] == 1
    assert body["recent_activity"][0]["kind"] == "loan"


def test_list_reports_json(client, staff, data):
    for path in ("popular-books", "overdue", "active-members", "category-stats"):
        response = client.get(f"{API}/{path}", headers=staff)
        assert response.status_code == 200, path
    assert client.get(f"{API}/overdue", headers=staff).json()[0]["days_late"] > 0


def test_csv_export(client, staff, data):
    response = client.get(f"{API}/overdue", params={"format": "csv"}, headers=staff)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="gecikmis-oduncler.csv"' in response.headers["content-disposition"]
    text = response.content.decode("utf-8-sig")
    header, row = text.strip().splitlines()
    assert header.startswith("Üye no;Üye;Telefon;Kitap")
    assert ";Kitap 1;" in row


def test_invalid_period(client, staff):
    response = client.get(
        f"{API}/popular-books", params={"from": "2026-10-10", "to": "2026-10-01"}, headers=staff
    )
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_reports_are_staff_only(client, make_user):
    user = make_user(UserRole.MEMBER)
    tokens = client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": DEFAULT_PASSWORD}
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get(f"{API}/dashboard", headers=headers).status_code == 403

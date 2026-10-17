import pytest

from app.models.enums import UserRole
from tests.conftest import DEFAULT_PASSWORD

API = "/api/v1"


def _login(client, user) -> dict[str, str]:
    tokens = client.post(
        f"{API}/auth/login", json={"email": user.email, "password": DEFAULT_PASSWORD}
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def admin(client, make_user):
    return _login(client, make_user(UserRole.ADMIN))


@pytest.fixture
def librarian(client, make_user):
    return _login(client, make_user(UserRole.LIBRARIAN))


def test_settings_read_and_update(client, admin, librarian):
    assert client.get(f"{API}/settings", headers=librarian).json()["daily_fine"] == "2.00"

    forbidden = client.put(f"{API}/settings", json={"daily_fine": "3"}, headers=librarian)
    assert forbidden.status_code == 403

    updated = client.put(f"{API}/settings", json={"daily_fine": "3"}, headers=admin)
    assert updated.json()["daily_fine"] == "3.00"

    invalid = client.put(f"{API}/settings", json={"loan_days": "0"}, headers=admin)
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


def test_staff_management(client, admin, librarian):
    created = client.post(
        f"{API}/staff",
        json={
            "email": "yeni@kutuphane.local",
            "full_name": "Yeni Görevli",
            "role": "librarian",
            "password": "Parola123!",
        },
        headers=admin,
    )
    assert created.status_code == 201
    user = created.json()
    assert "password_hash" not in user

    login = client.post(
        f"{API}/auth/login", json={"email": "yeni@kutuphane.local", "password": "Parola123!"}
    )
    assert login.status_code == 200

    deactivated = client.put(
        f"{API}/staff/{user['id']}",
        json={
            "email": user["email"],
            "full_name": user["full_name"],
            "role": "librarian",
            "is_active": False,
        },
        headers=admin,
    )
    assert deactivated.json()["is_active"] is False
    inactive_login = client.post(
        f"{API}/auth/login", json={"email": "yeni@kutuphane.local", "password": "Parola123!"}
    )
    assert inactive_login.json()["error"]["code"] == "USER_INACTIVE"

    reset = client.post(
        f"{API}/staff/{user['id']}/reset-password",
        json={"new_password": "BaskaParola1!"},
        headers=admin,
    )
    assert reset.status_code == 204

    assert len(client.get(f"{API}/staff", headers=admin).json()) == 3
    assert client.get(f"{API}/staff", headers=librarian).status_code == 403


def test_audit_log_endpoint(client, admin, librarian):
    client.post(f"{API}/authors", json={"full_name": "Sabahattin Ali"}, headers=librarian)

    logs = client.get(f"{API}/audit-logs", params={"entity": "authors"}, headers=admin).json()
    assert logs["total"] == 1
    entry = logs["items"][0]
    assert entry["action"] == "create"
    assert entry["user_name"] == "Test librarian"
    assert entry["details"]["full_name"] == "Sabahattin Ali"

    assert client.get(f"{API}/audit-logs", headers=librarian).status_code == 403

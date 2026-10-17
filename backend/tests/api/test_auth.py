from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import STAFF_ROLES, require_roles
from app.core.db import get_db
from app.core.errors import register_error_handlers
from app.models.enums import UserRole
from tests.conftest import DEFAULT_PASSWORD

PREFIX = "/api/v1/auth"


def _login(client, email, password=DEFAULT_PASSWORD):
    return client.post(f"{PREFIX}/login", json={"email": email, "password": password})


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_and_me(client, make_user):
    make_user(UserRole.LIBRARIAN, email="gorevli@test.local")

    response = _login(client, "gorevli@test.local")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"

    me = client.get(f"{PREFIX}/me", headers=_auth(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "gorevli@test.local"
    assert me.json()["role"] == "librarian"
    assert "password_hash" not in me.json()


def test_login_wrong_password_uses_error_format(client, make_user):
    make_user(email="kisi@test.local")

    response = _login(client, "kisi@test.local", "yanlis")
    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "INVALID_CREDENTIALS", "message": "E-posta veya şifre hatalı."}
    }


def test_validation_error_uses_error_format(client):
    response = client.post(f"{PREFIX}/login", json={"email": "x"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_me_requires_token(client):
    response = client.get(f"{PREFIX}/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_me_rejects_refresh_token(client, make_user):
    make_user(email="kisi@test.local")
    tokens = _login(client, "kisi@test.local").json()

    response = client.get(f"{PREFIX}/me", headers=_auth(tokens["refresh_token"]))
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_refresh(client, make_user):
    make_user(email="kisi@test.local")
    tokens = _login(client, "kisi@test.local").json()

    response = client.post(f"{PREFIX}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    me = client.get(f"{PREFIX}/me", headers=_auth(response.json()["access_token"]))
    assert me.status_code == 200


def test_logout(client, make_user):
    make_user(email="kisi@test.local")
    tokens = _login(client, "kisi@test.local").json()

    assert client.post(f"{PREFIX}/logout", headers=_auth(tokens["access_token"])).status_code == 204


def test_change_password(client, make_user):
    make_user(email="kisi@test.local")
    tokens = _login(client, "kisi@test.local").json()

    response = client.post(
        f"{PREFIX}/change-password",
        headers=_auth(tokens["access_token"]),
        json={"current_password": DEFAULT_PASSWORD, "new_password": "YeniParola456!"},
    )
    assert response.status_code == 204
    assert _login(client, "kisi@test.local").status_code == 401
    assert _login(client, "kisi@test.local", "YeniParola456!").status_code == 200


def test_change_password_rejects_short_password(client, make_user):
    make_user(email="kisi@test.local")
    tokens = _login(client, "kisi@test.local").json()

    response = client.post(
        f"{PREFIX}/change-password",
        headers=_auth(tokens["access_token"]),
        json={"current_password": DEFAULT_PASSWORD, "new_password": "kisa"},
    )
    assert response.status_code == 422


def _staff_only_client(db) -> TestClient:
    probe = FastAPI()
    register_error_handlers(probe)
    probe.dependency_overrides[get_db] = lambda: db

    @probe.get("/staff-only", dependencies=[Depends(require_roles(*STAFF_ROLES))])
    def staff_only():
        return {"ok": True}

    return TestClient(probe)


def test_require_roles(client, db, make_user):
    make_user(UserRole.ADMIN, email="admin@test.local")
    make_user(UserRole.MEMBER, email="uye@test.local")
    probe = _staff_only_client(db)

    admin_token = _login(client, "admin@test.local").json()["access_token"]
    member_token = _login(client, "uye@test.local").json()["access_token"]

    assert probe.get("/staff-only", headers=_auth(admin_token)).status_code == 200
    forbidden = probe.get("/staff-only", headers=_auth(member_token))
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"


def test_validation_messages_are_turkish(client, make_user):
    make_user(email="kisi@test.local")
    tokens = _login(client, "kisi@test.local").json()

    response = client.post(
        f"{PREFIX}/change-password",
        headers=_auth(tokens["access_token"]),
        json={"current_password": DEFAULT_PASSWORD, "new_password": "kisa"},
    )
    error = response.json()["error"]
    assert error["message"] == "Yeni şifre en az 8 karakter olmalı."
    assert error["details"] == [{"field": "Yeni şifre", "message": error["message"]}]

    missing = client.post(f"{PREFIX}/login", json={"email": "kisi@test.local"})
    assert missing.json()["error"]["message"] == "Şifre zorunlu."


def test_unknown_route_and_method_are_turkish(client):
    assert client.get("/api/v1/yok").json()["error"]["message"] == "Kayıt bulunamadı."
    assert client.get(f"{PREFIX}/login").json()["error"]["message"] == "Bu işlem desteklenmiyor."

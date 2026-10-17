import pytest

from app.core import security
from app.core.errors import AppError, ErrorCode
from app.services import auth_service
from tests.conftest import DEFAULT_PASSWORD


def test_password_hash_roundtrip():
    password_hash = security.hash_password("gizli-parola")
    assert password_hash != "gizli-parola"
    assert security.verify_password("gizli-parola", password_hash)
    assert not security.verify_password("yanlis", password_hash)


def test_authenticate_success_is_case_insensitive(make_user, db):
    user = make_user(email="kisi@test.local")
    assert auth_service.authenticate(db, " KISI@test.local ", DEFAULT_PASSWORD).id == user.id


@pytest.mark.parametrize(
    ("email", "password"),
    [("kisi@test.local", "yanlis-parola"), ("yok@test.local", DEFAULT_PASSWORD)],
)
def test_authenticate_rejects_bad_credentials(make_user, db, email, password):
    make_user(email="kisi@test.local")
    with pytest.raises(AppError) as exc_info:
        auth_service.authenticate(db, email, password)
    assert exc_info.value.code == ErrorCode.INVALID_CREDENTIALS
    assert exc_info.value.status_code == 401


def test_authenticate_rejects_inactive_user(make_user, db):
    make_user(email="pasif@test.local", is_active=False)
    with pytest.raises(AppError) as exc_info:
        auth_service.authenticate(db, "pasif@test.local", DEFAULT_PASSWORD)
    assert exc_info.value.code == ErrorCode.USER_INACTIVE


def test_login_issues_tokens_of_correct_type(make_user, db):
    user = make_user(email="kisi@test.local")
    tokens = auth_service.login(db, "kisi@test.local", DEFAULT_PASSWORD)

    assert security.decode_token(tokens.access_token, security.ACCESS) == user.id
    assert security.decode_token(tokens.refresh_token, security.REFRESH) == user.id


def test_refresh_rejects_access_token(make_user, db):
    tokens = auth_service.issue_tokens(make_user())
    with pytest.raises(AppError) as exc_info:
        auth_service.refresh(db, tokens.access_token)
    assert exc_info.value.code == ErrorCode.INVALID_TOKEN


def test_refresh_returns_new_pair(make_user, db):
    user = make_user()
    tokens = auth_service.refresh(db, auth_service.issue_tokens(user).refresh_token)
    assert security.decode_token(tokens.access_token, security.ACCESS) == user.id


def test_refresh_rejects_deactivated_user(make_user, db):
    user = make_user()
    refresh_token = auth_service.issue_tokens(user).refresh_token
    user.is_active = False
    db.commit()

    with pytest.raises(AppError) as exc_info:
        auth_service.refresh(db, refresh_token)
    assert exc_info.value.code == ErrorCode.USER_INACTIVE


def test_get_user_from_access_token(make_user, db):
    user = make_user()
    token = auth_service.issue_tokens(user).access_token
    assert auth_service.get_user_from_access_token(db, token).id == user.id


def test_get_user_rejects_garbage_token(db):
    with pytest.raises(AppError) as exc_info:
        auth_service.get_user_from_access_token(db, "bozuk.token.degeri")
    assert exc_info.value.code == ErrorCode.INVALID_TOKEN


def test_change_password(make_user, db):
    user = make_user(email="kisi@test.local")
    auth_service.change_password(db, user, DEFAULT_PASSWORD, "YeniParola456!")

    assert auth_service.authenticate(db, "kisi@test.local", "YeniParola456!").id == user.id


def test_change_password_requires_current_password(make_user, db):
    user = make_user()
    with pytest.raises(AppError) as exc_info:
        auth_service.change_password(db, user, "yanlis", "YeniParola456!")
    assert exc_info.value.code == ErrorCode.WRONG_PASSWORD

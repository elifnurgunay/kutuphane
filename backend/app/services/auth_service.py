from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import security
from app.core.errors import AppError, ErrorCode
from app.models import User


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


def _ensure_active(user: User | None) -> User:
    if user is None:
        raise AppError(ErrorCode.INVALID_TOKEN, "Oturum geçersiz veya süresi dolmuş.", 401)
    if not user.is_active:
        raise AppError(ErrorCode.USER_INACTIVE, "Hesabınız pasif durumda.", 403)
    return user


def issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=security.create_access_token(user.id),
        refresh_token=security.create_refresh_token(user.id),
    )


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not security.verify_password(password, user.password_hash):
        raise AppError(ErrorCode.INVALID_CREDENTIALS, "E-posta veya şifre hatalı.", 401)
    return _ensure_active(user)


def login(db: Session, email: str, password: str) -> TokenPair:
    return issue_tokens(authenticate(db, email, password))


def refresh(db: Session, refresh_token: str) -> TokenPair:
    user_id = security.decode_token(refresh_token, security.REFRESH)
    return issue_tokens(_ensure_active(db.get(User, user_id)))


def get_user_from_access_token(db: Session, access_token: str) -> User:
    user_id = security.decode_token(access_token, security.ACCESS)
    return _ensure_active(db.get(User, user_id))


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not security.verify_password(current_password, user.password_hash):
        raise AppError(ErrorCode.WRONG_PASSWORD, "Mevcut şifre hatalı.", 400)
    user.password_hash = security.hash_password(new_password)
    db.commit()

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import AppError, ErrorCode

ACCESS = "access"
REFRESH = "refresh"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _create_token(user_id: int, token_type: str, lifetime: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "type": token_type, "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(user_id, ACCESS, timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, REFRESH, timedelta(days=settings.refresh_token_days))


def decode_token(token: str, expected_type: str) -> int:
    """Token'ı doğrular ve kullanıcı id'sini döner."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise AppError(ErrorCode.INVALID_TOKEN, "Oturum geçersiz veya süresi dolmuş.", 401) from exc
    if payload.get("type") != expected_type:
        raise AppError(ErrorCode.INVALID_TOKEN, "Oturum geçersiz veya süresi dolmuş.", 401)
    return int(payload["sub"])

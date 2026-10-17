from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError, ErrorCode
from app.models import User
from app.models.enums import UserRole
from app.services import auth_service

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise AppError(ErrorCode.NOT_AUTHENTICATED, "Oturum açmanız gerekiyor.", 401)
    return auth_service.get_user_from_access_token(db, credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Yalnızca verilen rollere izin veren dependency üretir."""

    def _check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise AppError(ErrorCode.FORBIDDEN, "Bu işlem için yetkiniz yok.", 403)
        return user

    return _check


STAFF_ROLES = (UserRole.ADMIN, UserRole.LIBRARIAN)

"""Personel (yönetici / görevli) hesap yönetimi — yalnız admin."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.core.security import hash_password
from app.models import User
from app.models.enums import UserRole
from app.schemas.staff import StaffCreate, StaffUpdate

STAFF_ROLES = (UserRole.ADMIN, UserRole.LIBRARIAN)


def list_staff(db: Session) -> list[User]:
    stmt = select(User).where(User.role.in_(STAFF_ROLES)).order_by(User.role, User.full_name)
    return list(db.scalars(stmt))


def get_staff(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or user.role not in STAFF_ROLES:
        raise AppError(ErrorCode.NOT_FOUND, "Personel bulunamadı.", 404)
    return user


def _email(db: Session, email: str, exclude_id: int | None = None) -> str:
    normalized = email.strip().lower()
    stmt = select(User.id).where(func.lower(User.email) == normalized)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise AppError(ErrorCode.EMAIL_EXISTS, "Bu e-posta adresi zaten kayıtlı.", 409)
    return normalized


def _active_admin_count(db: Session) -> int:
    return db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN, User.is_active.is_(True))
    )


def create_staff(db: Session, data: StaffCreate) -> User:
    user = User(
        email=_email(db, data.email),
        full_name=data.full_name.strip(),
        role=UserRole(data.role),
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def update_staff(db: Session, user_id: int, data: StaffUpdate, acting: User) -> User:
    user = get_staff(db, user_id)
    losing_admin = user.role == UserRole.ADMIN and (
        data.role != UserRole.ADMIN or not data.is_active
    )
    if losing_admin and user.id == acting.id:
        raise AppError(
            ErrorCode.FORBIDDEN,
            "Kendi yönetici yetkinizi kaldıramaz veya hesabınızı kapatamazsınız.",
            403,
        )
    if losing_admin and user.is_active and _active_admin_count(db) <= 1:
        raise AppError(ErrorCode.FORBIDDEN, "Sistemde en az bir aktif yönetici kalmalı.", 403)
    user.email = _email(db, data.email, exclude_id=user.id)
    user.full_name = data.full_name.strip()
    user.role = UserRole(data.role)
    user.is_active = data.is_active
    db.commit()
    return user


def reset_password(db: Session, user_id: int, new_password: str) -> None:
    user = get_staff(db, user_id)
    user.password_hash = hash_password(new_password)
    db.commit()

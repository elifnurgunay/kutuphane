"""Yönetici uç noktaları: sistem ayarları, personel ve işlem kayıtları."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import STAFF_ROLES, DbSession, require_roles
from app.models import User
from app.models.enums import UserRole
from app.schemas.common import Page
from app.schemas.staff import AuditLogOut, PasswordReset, StaffCreate, StaffOut, StaffUpdate
from app.services import audit_service, settings_service, staff_service

Staff = Annotated[User, Depends(require_roles(*STAFF_ROLES))]
Admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]

settings = APIRouter(prefix="/settings", tags=["settings"])
staff = APIRouter(prefix="/staff", tags=["staff"])
audit_logs = APIRouter(prefix="/audit-logs", tags=["audit"])


@settings.get("", response_model=dict[str, str])
def get_settings(db: DbSession, _user: Staff):
    return settings_service.get_all(db)


@settings.put("", response_model=dict[str, str])
def update_settings(body: dict[str, str], db: DbSession, _admin: Admin):
    return settings_service.update_settings(db, body)


@staff.get("", response_model=list[StaffOut])
def list_staff(db: DbSession, _admin: Admin):
    return staff_service.list_staff(db)


@staff.post("", response_model=StaffOut, status_code=status.HTTP_201_CREATED)
def create_staff(body: StaffCreate, db: DbSession, _admin: Admin):
    return staff_service.create_staff(db, body)


@staff.put("/{user_id}", response_model=StaffOut)
def update_staff(user_id: int, body: StaffUpdate, db: DbSession, admin: Admin):
    return staff_service.update_staff(db, user_id, body, admin)


@staff.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(user_id: int, body: PasswordReset, db: DbSession, _admin: Admin) -> None:
    staff_service.reset_password(db, user_id, body.new_password)


@audit_logs.get("", response_model=Page[AuditLogOut])
def list_audit_logs(
    db: DbSession,
    _admin: Admin,
    entity: str | None = None,
    user_id: int | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 50,
):
    rows, total = audit_service.search_logs(db, entity, user_id, page, size)
    items = [
        AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            user_name=name,
            action=log.action,
            entity=log.entity,
            entity_id=log.entity_id,
            details=log.details,
            created_at=log.created_at,
        )
        for log, name in rows
    ]
    return Page(items=items, total=total, page=page, size=size)

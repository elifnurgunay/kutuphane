from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

StaffRole = Literal["admin", "librarian"]


class StaffUpdate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=150)
    role: StaffRole
    is_active: bool = True


class StaffCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=150)
    role: StaffRole
    password: str = Field(min_length=8, max_length=72)


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=8, max_length=72)


class StaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    user_name: str | None
    action: str
    entity: str
    entity_id: str | None
    details: dict[str, Any] | None
    created_at: datetime

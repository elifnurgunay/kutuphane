from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, enum_column
from app.models.enums import MemberStatus, MemberType

if TYPE_CHECKING:
    from app.models.user import User


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    member_no: Mapped[str] = mapped_column(String(20), unique=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(Text)
    member_type: Mapped[MemberType] = mapped_column(enum_column(MemberType))
    membership_start: Mapped[date]
    membership_end: Mapped[date]
    status: Mapped[MemberStatus] = mapped_column(
        enum_column(MemberStatus), default=MemberStatus.ACTIVE
    )

    user: Mapped[User] = relationship(back_populates="member")

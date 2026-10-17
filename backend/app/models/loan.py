from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, enum_column
from app.models.catalog import BookCopy
from app.models.enums import LoanStatus
from app.models.member import Member


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        Index("ix_loans_member_id_status", "member_id", "status"),
        Index(
            "ix_loans_due_date_active",
            "due_date",
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    copy_id: Mapped[int] = mapped_column(ForeignKey("book_copies.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    issued_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    loan_date: Mapped[date]
    due_date: Mapped[date]
    return_date: Mapped[date | None]
    returned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    renew_count: Mapped[int] = mapped_column(default=0, server_default="0")
    status: Mapped[LoanStatus] = mapped_column(enum_column(LoanStatus), default=LoanStatus.ACTIVE)

    copy: Mapped[BookCopy] = relationship()
    member: Mapped[Member] = relationship()

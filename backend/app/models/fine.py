from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, enum_column
from app.models.enums import FineReason, FineStatus
from app.models.loan import Loan
from app.models.member import Member


class Fine(Base):
    __tablename__ = "fines"

    id: Mapped[int] = mapped_column(primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    reason: Mapped[FineReason] = mapped_column(enum_column(FineReason))
    status: Mapped[FineStatus] = mapped_column(enum_column(FineStatus), default=FineStatus.UNPAID)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    loan: Mapped[Loan] = relationship()
    member: Mapped[Member] = relationship()

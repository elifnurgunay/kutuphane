from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, enum_column
from app.models.catalog import Book, BookCopy
from app.models.enums import ReservationStatus
from app.models.member import Member


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        Index("ix_reservations_book_id_status_created_at", "book_id", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[ReservationStatus] = mapped_column(
        enum_column(ReservationStatus), default=ReservationStatus.WAITING
    )
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_copy_id: Mapped[int | None] = mapped_column(ForeignKey("book_copies.id"))

    book: Mapped[Book] = relationship()
    member: Mapped[Member] = relationship()
    assigned_copy: Mapped[BookCopy | None] = relationship()

from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import BookCopy, Loan, Member, Reservation
from app.models.enums import CopyStatus, ReservationStatus
from app.repositories.member_repository import OPEN_LOAN_STATUSES
from app.repositories.pagination import paginate

ACTIVE_STATUSES = (ReservationStatus.WAITING, ReservationStatus.READY)


def lock(db: Session, reservation_id: int) -> Reservation | None:
    return db.scalar(select(Reservation).where(Reservation.id == reservation_id).with_for_update())


def available_copy_count(db: Session, book_id: int) -> int:
    return db.scalar(
        select(func.count(BookCopy.id)).where(
            BookCopy.book_id == book_id, BookCopy.status == CopyStatus.AVAILABLE
        )
    )


def has_active_reservation(db: Session, book_id: int, member_id: int) -> bool:
    stmt = select(Reservation.id).where(
        Reservation.book_id == book_id,
        Reservation.member_id == member_id,
        Reservation.status.in_(ACTIVE_STATUSES),
    )
    return db.scalar(stmt.limit(1)) is not None


def has_open_loan_of_book(db: Session, book_id: int, member_id: int) -> bool:
    stmt = (
        select(Loan.id)
        .join(Loan.copy)
        .where(
            BookCopy.book_id == book_id,
            Loan.member_id == member_id,
            Loan.status.in_(OPEN_LOAN_STATUSES),
        )
    )
    return db.scalar(stmt.limit(1)) is not None


def ready_reservations(db: Session) -> list[Reservation]:
    stmt = select(Reservation).where(Reservation.status == ReservationStatus.READY)
    return list(db.scalars(stmt.with_for_update()))


def queue_position(db: Session, reservation: Reservation) -> int | None:
    """Sıradaki konumu (1 = ilk). Yalnızca bekleyen rezervasyonlar için."""
    if reservation.status != ReservationStatus.WAITING:
        return None
    ahead = db.scalar(
        select(func.count(Reservation.id)).where(
            Reservation.book_id == reservation.book_id,
            Reservation.status == ReservationStatus.WAITING,
            (Reservation.created_at < reservation.created_at)
            | (
                (Reservation.created_at == reservation.created_at)
                & (Reservation.id < reservation.id)
            ),
        )
    )
    return ahead + 1


def _list_query() -> Select[Any]:
    return select(Reservation).options(
        joinedload(Reservation.book),
        joinedload(Reservation.member).joinedload(Member.user),
        joinedload(Reservation.assigned_copy),
    )


def search(
    db: Session,
    book_id: int | None,
    member_id: int | None,
    status: ReservationStatus | None,
    page: int,
    size: int,
) -> tuple[list[Reservation], int]:
    stmt = _list_query()
    if book_id is not None:
        stmt = stmt.where(Reservation.book_id == book_id)
    if member_id is not None:
        stmt = stmt.where(Reservation.member_id == member_id)
    if status is not None:
        stmt = stmt.where(Reservation.status == status)
    stmt = stmt.order_by(Reservation.created_at, Reservation.id)
    rows, total = paginate(db, stmt, page, size)
    return [row[0] for row in rows], total


def get_with_details(db: Session, reservation_id: int) -> Reservation | None:
    return db.scalar(_list_query().where(Reservation.id == reservation_id))

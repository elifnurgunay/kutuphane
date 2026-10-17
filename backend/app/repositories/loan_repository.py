from datetime import date
from typing import Any

from sqlalchemy import Select, and_, func, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.models import BookCopy, Loan, Member, Reservation
from app.models.enums import CopyStatus, LoanStatus, ReservationStatus
from app.repositories.member_repository import OPEN_LOAN_STATUSES
from app.repositories.pagination import paginate


def lock_copy_by_barcode(db: Session, barcode: str) -> BookCopy | None:
    """Nüsha satırını kilitler (PostgreSQL: SELECT ... FOR UPDATE)."""
    return db.scalar(
        select(BookCopy).where(BookCopy.barcode == barcode.strip().upper()).with_for_update()
    )


def lock_loan(db: Session, loan_id: int) -> Loan | None:
    return db.scalar(select(Loan).where(Loan.id == loan_id).with_for_update())


def lock_member(db: Session, member_id: int) -> Member | None:
    return db.scalar(select(Member).where(Member.id == member_id).with_for_update())


def claim_copy(db: Session, copy_id: int, expected: CopyStatus, new: CopyStatus) -> bool:
    """Nüsha durumunu yalnızca beklenen durumdaysa değiştirir (karşılaştır-ve-yaz).

    Satır kilidini desteklemeyen veritabanlarında da aynı nüshanın iki kez
    verilmesini engeller.
    """
    result = db.execute(
        update(BookCopy)
        .where(BookCopy.id == copy_id, BookCopy.status == expected)
        .values(status=new)
    )
    return result.rowcount == 1


def is_overdue(today: date) -> Any:
    """Gecikmiş ödünç koşulu: günlük görev işaretlemiş ya da vadesi geçmiş."""
    return or_(
        Loan.status == LoanStatus.OVERDUE,
        and_(Loan.status == LoanStatus.ACTIVE, Loan.due_date < today),
    )


def count_open_loans(db: Session, member_id: int) -> int:
    return db.scalar(
        select(func.count(Loan.id)).where(
            Loan.member_id == member_id, Loan.status.in_(OPEN_LOAN_STATUSES)
        )
    )


def count_overdue_loans(db: Session, member_id: int, today: date) -> int:
    return db.scalar(
        select(func.count(Loan.id)).where(Loan.member_id == member_id, is_overdue(today))
    )


def open_loan_for_copy(db: Session, copy_id: int) -> Loan | None:
    return db.scalar(
        select(Loan).where(Loan.copy_id == copy_id, Loan.status.in_(OPEN_LOAN_STATUSES))
    )


def ready_reservation_for_copy(db: Session, copy_id: int) -> Reservation | None:
    return db.scalar(
        select(Reservation).where(
            Reservation.assigned_copy_id == copy_id,
            Reservation.status == ReservationStatus.READY,
        )
    )


def has_pending_reservation(db: Session, book_id: int) -> bool:
    return (
        db.scalar(
            select(Reservation.id)
            .where(
                Reservation.book_id == book_id,
                Reservation.status.in_((ReservationStatus.WAITING, ReservationStatus.READY)),
            )
            .limit(1)
        )
        is not None
    )


def next_waiting_reservation(db: Session, book_id: int) -> Reservation | None:
    return db.scalar(
        select(Reservation)
        .where(Reservation.book_id == book_id, Reservation.status == ReservationStatus.WAITING)
        .order_by(Reservation.created_at, Reservation.id)
        .limit(1)
        .with_for_update()
    )


def _list_query() -> Select[Any]:
    return select(Loan).options(
        joinedload(Loan.copy).joinedload(BookCopy.book),
        joinedload(Loan.member).joinedload(Member.user),
    )


def search(
    db: Session,
    status: str | None,
    member_id: int | None,
    barcode: str | None,
    today: date,
    page: int,
    size: int,
) -> tuple[list[Loan], int]:
    stmt = _list_query()
    if status == "active":
        stmt = stmt.where(Loan.status == LoanStatus.ACTIVE, Loan.due_date >= today)
    elif status == "overdue":
        stmt = stmt.where(is_overdue(today))
    elif status == "open":
        stmt = stmt.where(Loan.status.in_(OPEN_LOAN_STATUSES))
    elif status is not None:
        stmt = stmt.where(Loan.status == LoanStatus(status))
    if member_id is not None:
        stmt = stmt.where(Loan.member_id == member_id)
    if barcode:
        stmt = stmt.join(Loan.copy).where(BookCopy.barcode == barcode.strip().upper())
    order = Loan.due_date.asc() if status in ("active", "overdue", "open") else Loan.id.desc()
    rows, total = paginate(db, stmt.order_by(order, Loan.id), page, size)
    return [row[0] for row in rows], total


def get_with_details(db: Session, loan_id: int) -> Loan | None:
    return db.scalar(_list_query().where(Loan.id == loan_id))

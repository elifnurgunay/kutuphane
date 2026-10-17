from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import BookCopy, Fine, Loan, Member, Reservation, User
from app.models.enums import FineStatus, LoanStatus, MemberStatus
from app.repositories.pagination import paginate

# Üyenin elindeki (henüz iade edilmemiş) ödünçler
OPEN_LOAN_STATUSES = (LoanStatus.ACTIVE, LoanStatus.OVERDUE)

active_loan_count = (
    select(func.count(Loan.id))
    .where(Loan.member_id == Member.id, Loan.status.in_(OPEN_LOAN_STATUSES))
    .correlate(Member)
    .scalar_subquery()
    .label("active_loan_count")
)


@dataclass(frozen=True)
class MemberRow:
    member: Member
    active_loan_count: int


def _base_query() -> Select[Any]:
    return select(Member, active_loan_count).join(Member.user).options(selectinload(Member.user))


def search(
    db: Session, q: str | None, status: MemberStatus | None, page: int, size: int
) -> tuple[list[MemberRow], int]:
    stmt = _base_query()
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
                Member.member_no.ilike(pattern),
                Member.phone.ilike(pattern),
            )
        )
    if status is not None:
        stmt = stmt.where(Member.status == status)
    rows, total = paginate(db, stmt.order_by(Member.member_no), page, size)
    return [MemberRow(*row) for row in rows], total


def get_row(db: Session, member_id: int) -> MemberRow | None:
    row = db.execute(_base_query().where(Member.id == member_id)).first()
    return MemberRow(*row) if row else None


def unpaid_fine_total(db: Session, member_id: int) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(Fine.amount), 0)).where(
            Fine.member_id == member_id, Fine.status == FineStatus.UNPAID
        )
    )
    return Decimal(total).quantize(Decimal("0.01"))


def loans(db: Session, member_id: int, status: LoanStatus | None) -> list[Loan]:
    stmt = (
        select(Loan)
        .where(Loan.member_id == member_id)
        .options(joinedload(Loan.copy).joinedload(BookCopy.book))
        .order_by(Loan.loan_date.desc(), Loan.id.desc())
    )
    if status is not None:
        stmt = stmt.where(Loan.status == status)
    return list(db.scalars(stmt))


def fines(db: Session, member_id: int) -> list[Fine]:
    stmt = select(Fine).where(Fine.member_id == member_id).order_by(Fine.created_at.desc())
    return list(db.scalars(stmt))


def reservations(db: Session, member_id: int) -> list[Reservation]:
    stmt = (
        select(Reservation)
        .where(Reservation.member_id == member_id)
        .options(joinedload(Reservation.book))
        .order_by(Reservation.created_at.desc())
    )
    return list(db.scalars(stmt))

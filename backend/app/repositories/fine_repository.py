from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import BookCopy, Fine, Loan, Member
from app.models.enums import FineStatus
from app.repositories.pagination import paginate


def lock(db: Session, fine_id: int) -> Fine | None:
    return db.scalar(select(Fine).where(Fine.id == fine_id).with_for_update())


def _list_query():
    return select(Fine).options(
        joinedload(Fine.member).joinedload(Member.user),
        joinedload(Fine.loan).joinedload(Loan.copy).joinedload(BookCopy.book),
    )


def search(
    db: Session, status: FineStatus | None, member_id: int | None, page: int, size: int
) -> tuple[list[Fine], int, Decimal]:
    """(cezalar, toplam kayıt, filtreye uyan cezaların toplam tutarı)"""
    conditions = []
    if status is not None:
        conditions.append(Fine.status == status)
    if member_id is not None:
        conditions.append(Fine.member_id == member_id)
    stmt = _list_query().where(*conditions).order_by(Fine.created_at.desc(), Fine.id.desc())
    rows, total = paginate(db, stmt, page, size)
    amount = db.scalar(select(func.coalesce(func.sum(Fine.amount), 0)).where(*conditions))
    return [row[0] for row in rows], total, Decimal(amount).quantize(Decimal("0.01"))


def get_with_details(db: Session, fine_id: int) -> Fine | None:
    return db.scalar(_list_query().where(Fine.id == fine_id))

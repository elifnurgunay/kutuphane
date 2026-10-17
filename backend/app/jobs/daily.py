"""Günde bir çalışan bakım görevi.

Elle çalıştırma:  python -m app.jobs.daily
Backend içinde:   RUN_DAILY_JOBS=true ise her gece otomatik (app/jobs/scheduler.py).
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import Loan, Member
from app.models.enums import LoanStatus, MemberStatus
from app.services import reservation_service


@dataclass(frozen=True)
class DailyResult:
    overdue_loans: int
    expired_reservations: int
    expired_memberships: int


def mark_overdue_loans(db: Session, today: date) -> int:
    result = db.execute(
        update(Loan)
        .where(Loan.status == LoanStatus.ACTIVE, Loan.due_date < today)
        .values(status=LoanStatus.OVERDUE)
    )
    db.commit()
    return result.rowcount


def expire_memberships(db: Session, today: date) -> int:
    result = db.execute(
        update(Member)
        .where(Member.status == MemberStatus.ACTIVE, Member.membership_end < today)
        .values(status=MemberStatus.EXPIRED)
    )
    db.commit()
    return result.rowcount


def run(db: Session, today: date | None = None, now: datetime | None = None) -> DailyResult:
    """Görevler tekrar çalıştırılsa da güvenlidir (idempotent)."""
    today = today or date.today()
    now = now or datetime.now(UTC)
    return DailyResult(
        overdue_loans=mark_overdue_loans(db, today),
        expired_reservations=reservation_service.expire_ready_reservations(db, now),
        expired_memberships=expire_memberships(db, today),
    )


def main() -> None:
    with SessionLocal() as db:
        result = run(db)
    print(
        f"Günlük görev: {result.overdue_loans} ödünç gecikmiş, "
        f"{result.expired_reservations} rezervasyon süresi doldu, "
        f"{result.expired_memberships} üyelik bitti."
    )


if __name__ == "__main__":
    main()

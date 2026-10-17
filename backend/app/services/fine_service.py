"""Ceza hesaplama ve oluşturma (ödeme / affetme Faz 5'te)."""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Fine, Loan
from app.models.enums import FineReason, FineStatus
from app.services import settings_service


def overdue_days(due_date: date, return_date: date) -> int:
    return max((return_date - due_date).days, 0)


def calculate_overdue_fine(due_date: date, return_date: date, daily_fine: Decimal) -> Decimal:
    """Gecikme cezası: gecikme_gün × daily_fine."""
    return (daily_fine * overdue_days(due_date, return_date)).quantize(Decimal("0.01"))


def _add_fine(db: Session, loan: Loan, amount: Decimal, reason: FineReason) -> Fine:
    fine = Fine(
        loan_id=loan.id,
        member_id=loan.member_id,
        amount=amount,
        reason=reason,
        status=FineStatus.UNPAID,
    )
    db.add(fine)
    return fine


def create_overdue_fine(db: Session, loan: Loan, return_date: date) -> Fine | None:
    """Gecikme varsa ceza kaydı ekler (commit etmez; çağıran işlemin parçasıdır)."""
    amount = calculate_overdue_fine(
        loan.due_date, return_date, settings_service.get_decimal(db, "daily_fine")
    )
    if amount <= 0:
        return None
    return _add_fine(db, loan, amount, FineReason.OVERDUE)


def create_lost_fine(db: Session, loan: Loan) -> Fine:
    amount = settings_service.get_decimal(db, "lost_book_fine")
    return _add_fine(db, loan, amount, FineReason.LOST)


def create_damage_fine(db: Session, loan: Loan, amount: Decimal) -> Fine | None:
    if amount <= 0:
        return None
    return _add_fine(db, loan, amount.quantize(Decimal("0.01")), FineReason.DAMAGED)

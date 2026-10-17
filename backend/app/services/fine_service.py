"""Ceza hesaplama, oluşturma, tahsilat ve affetme."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.models import Fine, Loan, User
from app.models.enums import FineReason, FineStatus
from app.repositories import fine_repository
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


# --- Tahsilat / affetme ---


def get_fine(db: Session, fine_id: int) -> Fine:
    fine = fine_repository.get_with_details(db, fine_id)
    if fine is None:
        raise AppError(ErrorCode.NOT_FOUND, "Ceza bulunamadı.", 404)
    return fine


def _close_fine(
    db: Session, fine_id: int, staff: User, status: FineStatus, now: datetime | None
) -> Fine:
    try:
        fine = fine_repository.lock(db, fine_id)
        if fine is None:
            raise AppError(ErrorCode.NOT_FOUND, "Ceza bulunamadı.", 404)
        if fine.status != FineStatus.UNPAID:
            raise AppError(ErrorCode.FINE_NOT_UNPAID, "Bu ceza zaten kapatılmış.", 409)
        fine.status = status
        fine.paid_at = now or datetime.now(UTC)
        fine.collected_by = staff.id
        db.commit()
        return fine
    except Exception:
        db.rollback()
        raise


def pay_fine(db: Session, fine_id: int, staff: User, now: datetime | None = None) -> Fine:
    """Görevli tahsilatı kaydeder (online ödeme kapsam dışı)."""
    return _close_fine(db, fine_id, staff, FineStatus.PAID, now)


def waive_fine(db: Session, fine_id: int, admin: User, now: datetime | None = None) -> Fine:
    """Cezayı affeder; yetki kontrolü (yalnız admin) uç noktadadır."""
    return _close_fine(db, fine_id, admin, FineStatus.WAIVED, now)


def search_fines(
    db: Session, status: FineStatus | None, member_id: int | None, page: int, size: int
) -> tuple[list[Fine], int, Decimal]:
    return fine_repository.search(db, status, member_id, page, size)

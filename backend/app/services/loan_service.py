"""Ödünç verme, iade, süre uzatma ve kayıp işaretleme.

Her işlem tek veritabanı işleminde (transaction) yapılır: hata olursa hiçbir
değişiklik kalıcı olmaz.
"""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.models import Fine, Loan, Member, Reservation, User
from app.models.enums import CopyStatus, LoanStatus, MemberStatus, ReservationStatus
from app.repositories import loan_repository as repo
from app.repositories import member_repository
from app.repositories.member_repository import OPEN_LOAN_STATUSES
from app.services import fine_service, reservation_service, settings_service

# --- Uygunluk (ödünç kuralları 1-4) ---


@dataclass(frozen=True)
class Problem:
    code: ErrorCode
    message: str


@dataclass(frozen=True)
class Eligibility:
    active_loan_count: int
    loan_limit: int
    unpaid_fine_total: Decimal
    max_unpaid_fine: Decimal
    overdue_count: int
    problems: list[Problem] = field(default_factory=list)

    @property
    def can_borrow(self) -> bool:
        return not self.problems


def loan_limit_for(db: Session, member: Member) -> int:
    return settings_service.get_int(db, f"max_loans_{member.member_type.value}")


def check_eligibility(db: Session, member: Member, today: date) -> Eligibility:
    """Üyenin yeni kitap alıp alamayacağını ve nedenlerini döner."""
    problems: list[Problem] = []
    if member.status != MemberStatus.ACTIVE:
        problems.append(Problem(ErrorCode.MEMBER_INACTIVE, "Üye aktif değil."))
    elif member.membership_end < today:
        problems.append(Problem(ErrorCode.MEMBER_INACTIVE, "Üyelik süresi dolmuş."))

    active = repo.count_open_loans(db, member.id)
    limit = loan_limit_for(db, member)
    if active >= limit:
        problems.append(
            Problem(
                ErrorCode.LOAN_LIMIT_EXCEEDED,
                f"Üye ödünç limitine ulaştı ({active}/{limit}).",
            )
        )

    unpaid = member_repository.unpaid_fine_total(db, member.id)
    max_unpaid = settings_service.get_decimal(db, "max_unpaid_fine")
    if unpaid >= max_unpaid:
        problems.append(
            Problem(
                ErrorCode.UNPAID_FINES,
                f"Ödenmemiş ceza toplamı {unpaid} TL (sınır {max_unpaid} TL).",
            )
        )

    overdue = repo.count_overdue_loans(db, member.id, today)
    if overdue:
        problems.append(Problem(ErrorCode.HAS_OVERDUE, "Üyenin gecikmiş ödüncü var."))

    return Eligibility(
        active_loan_count=active,
        loan_limit=limit,
        unpaid_fine_total=unpaid,
        max_unpaid_fine=max_unpaid,
        overdue_count=overdue,
        problems=problems,
    )


def get_eligibility(db: Session, member_id: int, today: date | None = None) -> Eligibility:
    member = db.get(Member, member_id)
    if member is None:
        raise AppError(ErrorCode.NOT_FOUND, "Üye bulunamadı.", 404)
    return check_eligibility(db, member, today or date.today())


# --- Ödünç verme ---


def issue_loan(
    db: Session, member_id: int, barcode: str, staff: User, today: date | None = None
) -> Loan:
    today = today or date.today()
    try:
        member = repo.lock_member(db, member_id)
        if member is None:
            raise AppError(ErrorCode.NOT_FOUND, "Üye bulunamadı.", 404)
        eligibility = check_eligibility(db, member, today)
        if eligibility.problems:
            first = eligibility.problems[0]
            raise AppError(first.code, first.message, 409)

        copy = repo.lock_copy_by_barcode(db, barcode)
        if copy is None:
            raise AppError(ErrorCode.NOT_FOUND, "Bu barkodla nüsha bulunamadı.", 404)

        reservation: Reservation | None = None
        if copy.status == CopyStatus.RESERVED:
            reservation = repo.ready_reservation_for_copy(db, copy.id)
            if reservation is None or reservation.member_id != member.id:
                raise AppError(
                    ErrorCode.COPY_NOT_AVAILABLE, "Nüsha başka bir üye için ayrıldı.", 409
                )
        elif copy.status != CopyStatus.AVAILABLE:
            raise AppError(ErrorCode.COPY_NOT_AVAILABLE, "Nüsha ödünç verilebilir değil.", 409)

        # Kilit olmayan veritabanlarında da çift ödünçü engelleyen koşullu güncelleme
        if not repo.claim_copy(db, copy.id, copy.status, CopyStatus.LOANED):
            raise AppError(
                ErrorCode.COPY_NOT_AVAILABLE, "Nüsha az önce başka işlemde kullanıldı.", 409
            )

        loan_days = settings_service.get_int(db, "loan_days")
        loan = Loan(
            copy_id=copy.id,
            member_id=member.id,
            issued_by=staff.id,
            loan_date=today,
            due_date=today + timedelta(days=loan_days),
            status=LoanStatus.ACTIVE,
        )
        db.add(loan)
        if reservation is not None:
            reservation.status = ReservationStatus.FULFILLED
        db.commit()
        return loan
    except Exception:
        db.rollback()
        raise


# --- İade ---


@dataclass
class ReturnResult:
    loan: Loan
    fines: list[Fine]
    reservation: Reservation | None


def _get_open_loan(db: Session, loan_id: int, member_id: int | None = None) -> Loan:
    loan = repo.lock_loan(db, loan_id)
    if loan is None:
        raise AppError(ErrorCode.NOT_FOUND, "Ödünç kaydı bulunamadı.", 404)
    if member_id is not None and loan.member_id != member_id:
        raise AppError(ErrorCode.FORBIDDEN, "Bu ödünç kaydı size ait değil.", 403)
    if loan.status not in OPEN_LOAN_STATUSES:
        raise AppError(ErrorCode.LOAN_NOT_ACTIVE, "Bu ödünç zaten kapanmış.", 409)
    return loan


def return_loan(
    db: Session,
    loan_id: int,
    staff: User,
    damaged: bool = False,
    damage_fine: Decimal | None = None,
    notes: str | None = None,
    today: date | None = None,
    now: datetime | None = None,
) -> ReturnResult:
    today = today or date.today()
    now = now or datetime.now(UTC)
    try:
        loan = _get_open_loan(db, loan_id)
        copy = loan.copy
        db.refresh(copy, with_for_update=True)

        loan.return_date = today
        loan.returned_to = staff.id
        loan.status = LoanStatus.RETURNED

        fines = [f for f in [fine_service.create_overdue_fine(db, loan, today)] if f]
        if notes:
            copy.notes = f"{copy.notes}\n{notes}" if copy.notes else notes

        reservation = None
        if damaged:
            copy.status = CopyStatus.DAMAGED
            damage = fine_service.create_damage_fine(db, loan, damage_fine or Decimal("0"))
            if damage:
                fines.append(damage)
        else:
            reservation = reservation_service.assign_copy_to_next(db, copy, now)
        db.commit()
        return ReturnResult(loan=loan, fines=fines, reservation=reservation)
    except Exception:
        db.rollback()
        raise


# --- Süre uzatma ---


def renew_loan(
    db: Session, loan_id: int, today: date | None = None, member_id: int | None = None
) -> Loan:
    """member_id verilirse (üye paneli) yalnızca o üyenin ödüncü uzatılabilir."""
    today = today or date.today()
    try:
        loan = _get_open_loan(db, loan_id, member_id)
        if loan.status == LoanStatus.OVERDUE or loan.due_date < today:
            raise AppError(ErrorCode.LOAN_OVERDUE, "Gecikmiş ödünç uzatılamaz.", 409)
        max_renewals = settings_service.get_int(db, "max_renewals")
        if loan.renew_count >= max_renewals:
            raise AppError(
                ErrorCode.RENEW_LIMIT,
                f"Uzatma hakkı doldu ({loan.renew_count}/{max_renewals}).",
                409,
            )
        if repo.has_pending_reservation(db, loan.copy.book_id):
            raise AppError(
                ErrorCode.RESERVATION_PENDING,
                "Bu kitap için bekleyen rezervasyon olduğundan süre uzatılamaz.",
                409,
            )
        loan.due_date = today + timedelta(days=settings_service.get_int(db, "loan_days"))
        loan.renew_count += 1
        db.commit()
        return loan
    except Exception:
        db.rollback()
        raise


# --- Kayıp ---


def mark_lost(db: Session, loan_id: int) -> tuple[Loan, Fine]:
    try:
        loan = _get_open_loan(db, loan_id)
        loan.status = LoanStatus.LOST
        loan.copy.status = CopyStatus.LOST
        fine = fine_service.create_lost_fine(db, loan)
        db.commit()
        return loan, fine
    except Exception:
        db.rollback()
        raise


# --- Listeleme ---


def search_loans(
    db: Session,
    status: str | None,
    member_id: int | None,
    barcode: str | None,
    page: int,
    size: int,
    today: date | None = None,
) -> tuple[list[Loan], int]:
    return repo.search(db, status, member_id, barcode, today or date.today(), page, size)


def get_loan(db: Session, loan_id: int) -> Loan:
    loan = repo.get_with_details(db, loan_id)
    if loan is None:
        raise AppError(ErrorCode.NOT_FOUND, "Ödünç kaydı bulunamadı.", 404)
    return loan

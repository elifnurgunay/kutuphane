"""Üye yönetimi."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.core.security import hash_password
from app.models import Fine, Loan, Member, Reservation, User
from app.models.enums import LoanStatus, MemberStatus, UserRole
from app.repositories import member_repository
from app.repositories.member_repository import MemberRow
from app.schemas.member import MemberCreate, MemberUpdate

MEMBER_NO_PREFIX = "UYE-"


def _not_found() -> AppError:
    return AppError(ErrorCode.NOT_FOUND, "Üye bulunamadı.", 404)


def get_member(db: Session, member_id: int) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise _not_found()
    return member


def get_member_row(db: Session, member_id: int) -> MemberRow:
    row = member_repository.get_row(db, member_id)
    if row is None:
        raise _not_found()
    return row


def unpaid_fine_total(db: Session, member_id: int) -> Decimal:
    return member_repository.unpaid_fine_total(db, member_id)


def search_members(
    db: Session, q: str | None, status: MemberStatus | None, page: int, size: int
) -> tuple[list[MemberRow], int]:
    return member_repository.search(db, q, status, page, size)


def next_member_no(db: Session) -> str:
    """UYE-000123 biçiminde bir sonraki üye numarasını üretir."""
    numbers = db.scalars(
        select(Member.member_no).where(Member.member_no.startswith(MEMBER_NO_PREFIX))
    )
    used = [
        int(no[len(MEMBER_NO_PREFIX) :]) for no in numbers if no[len(MEMBER_NO_PREFIX) :].isdigit()
    ]
    return f"{MEMBER_NO_PREFIX}{max(used, default=0) + 1:06d}"


def _normalize_email(db: Session, email: str, exclude_user_id: int | None = None) -> str:
    normalized = email.strip().lower()
    stmt = select(User.id).where(func.lower(User.email) == normalized)
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    if db.scalar(stmt) is not None:
        raise AppError(ErrorCode.EMAIL_EXISTS, "Bu e-posta adresi zaten kayıtlı.", 409)
    return normalized


def _check_dates(data: MemberUpdate) -> None:
    if data.membership_end < data.membership_start:
        raise AppError(
            ErrorCode.INVALID_DATE_RANGE,
            "Üyelik bitiş tarihi başlangıçtan önce olamaz.",
            400,
        )


def create_member(db: Session, data: MemberCreate) -> Member:
    _check_dates(data)
    user = User(
        email=_normalize_email(db, data.email),
        password_hash=hash_password(data.password),
        full_name=data.full_name.strip(),
        role=UserRole.MEMBER,
    )
    member = Member(
        user=user,
        member_no=next_member_no(db),
        phone=data.phone,
        address=data.address,
        member_type=data.member_type,
        membership_start=data.membership_start,
        membership_end=data.membership_end,
        status=MemberStatus.ACTIVE,
    )
    db.add(member)
    db.commit()
    return member


def update_member(db: Session, member_id: int, data: MemberUpdate) -> Member:
    member = get_member(db, member_id)
    _check_dates(data)
    member.user.email = _normalize_email(db, data.email, exclude_user_id=member.user_id)
    member.user.full_name = data.full_name.strip()
    member.phone = data.phone
    member.address = data.address
    member.member_type = data.member_type
    member.membership_start = data.membership_start
    member.membership_end = data.membership_end
    db.commit()
    return member


def suspend_member(db: Session, member_id: int) -> Member:
    member = get_member(db, member_id)
    member.status = MemberStatus.SUSPENDED
    db.commit()
    return member


def activate_member(db: Session, member_id: int, today: date | None = None) -> Member:
    member = get_member(db, member_id)
    if member.membership_end < (today or date.today()):
        raise AppError(
            ErrorCode.MEMBERSHIP_EXPIRED,
            "Üyelik süresi dolmuş; önce bitiş tarihini uzatın.",
            400,
        )
    member.status = MemberStatus.ACTIVE
    db.commit()
    return member


def member_loans(db: Session, member_id: int, status: LoanStatus | None = None) -> list[Loan]:
    get_member(db, member_id)
    return member_repository.loans(db, member_id, status)


def member_fines(db: Session, member_id: int) -> list[Fine]:
    get_member(db, member_id)
    return member_repository.fines(db, member_id)


def member_reservations(db: Session, member_id: int) -> list[Reservation]:
    get_member(db, member_id)
    return member_repository.reservations(db, member_id)


def get_member_for_user(db: Session, user: User) -> Member:
    """Üye paneli: giriş yapan kullanıcının kendi üye kaydı."""
    if user.role != UserRole.MEMBER:
        raise AppError(ErrorCode.FORBIDDEN, "Bu sayfa yalnızca üyeler içindir.", 403)
    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if member is None:
        raise AppError(ErrorCode.NOT_FOUND, "Üye kaydınız bulunamadı.", 404)
    return member

"""Rezervasyon ve kuyruk yönetimi."""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.models import Book, BookCopy, Member, Reservation
from app.models.enums import CopyStatus, MemberStatus, ReservationStatus
from app.repositories import loan_repository
from app.repositories import reservation_repository as repo
from app.services import settings_service


def _as_utc(value: datetime) -> datetime:
    # SQLite saat dilimini saklamaz; tüm zamanlar UTC yazılır.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def assign_copy_to_next(db: Session, copy: BookCopy, now: datetime) -> Reservation | None:
    """Boşalan nüshayı kuyruktaki ilk üyeye ayırır; kuyruk boşsa rafa döner.

    Commit etmez; çağıran işlemin (iade, iptal, süre dolumu) parçasıdır.
    """
    reservation = loan_repository.next_waiting_reservation(db, copy.book_id)
    if reservation is None:
        copy.status = CopyStatus.AVAILABLE
        return None
    hold_days = settings_service.get_int(db, "reservation_hold_days")
    reservation.status = ReservationStatus.READY
    reservation.ready_at = now
    reservation.expires_at = now + timedelta(days=hold_days)
    reservation.assigned_copy_id = copy.id
    copy.status = CopyStatus.RESERVED
    # Üyeye bildirim: e-posta altyapısı henüz yok.
    return reservation


def create_reservation(
    db: Session,
    book_id: int,
    member_id: int,
    today: date | None = None,
    now: datetime | None = None,
) -> Reservation:
    today = today or date.today()
    now = now or datetime.now(UTC)
    if db.get(Book, book_id) is None:
        raise AppError(ErrorCode.NOT_FOUND, "Kitap bulunamadı.", 404)
    member = db.get(Member, member_id)
    if member is None:
        raise AppError(ErrorCode.NOT_FOUND, "Üye bulunamadı.", 404)
    if member.status != MemberStatus.ACTIVE or member.membership_end < today:
        raise AppError(ErrorCode.MEMBER_INACTIVE, "Üye aktif değil.", 409)
    if repo.available_copy_count(db, book_id) > 0:
        raise AppError(
            ErrorCode.BOOK_AVAILABLE_NO_RESERVATION,
            "Kitabın müsait nüshası var; rezervasyon yerine ödünç alınabilir.",
            409,
        )
    if repo.has_active_reservation(db, book_id, member_id):
        raise AppError(
            ErrorCode.RESERVATION_EXISTS, "Üyenin bu kitap için zaten rezervasyonu var.", 409
        )
    if repo.has_open_loan_of_book(db, book_id, member_id):
        raise AppError(ErrorCode.ALREADY_BORROWED, "Bu kitap zaten üyenin elinde.", 409)

    reservation = Reservation(
        book_id=book_id,
        member_id=member_id,
        created_at=now,
        status=ReservationStatus.WAITING,
    )
    db.add(reservation)
    db.commit()
    return reservation


def cancel_reservation(
    db: Session, reservation_id: int, now: datetime | None = None
) -> Reservation:
    now = now or datetime.now(UTC)
    try:
        reservation = repo.lock(db, reservation_id)
        if reservation is None:
            raise AppError(ErrorCode.NOT_FOUND, "Rezervasyon bulunamadı.", 404)
        if reservation.status not in repo.ACTIVE_STATUSES:
            raise AppError(ErrorCode.RESERVATION_NOT_ACTIVE, "Rezervasyon zaten kapanmış.", 409)
        released = (
            reservation.assigned_copy if reservation.status == ReservationStatus.READY else None
        )
        reservation.status = ReservationStatus.CANCELLED
        if released is not None:
            assign_copy_to_next(db, released, now)
        db.commit()
        return reservation
    except Exception:
        db.rollback()
        raise


def expire_ready_reservations(db: Session, now: datetime | None = None) -> int:
    """Teslim alınmayan hazır rezervasyonları düşürür ve nüshayı sıradakine geçirir."""
    now = now or datetime.now(UTC)
    expired = 0
    try:
        for reservation in repo.ready_reservations(db):
            if reservation.expires_at is None or _as_utc(reservation.expires_at) >= now:
                continue
            reservation.status = ReservationStatus.EXPIRED
            if reservation.assigned_copy is not None:
                assign_copy_to_next(db, reservation.assigned_copy, now)
            expired += 1
        db.commit()
        return expired
    except Exception:
        db.rollback()
        raise


def queue_position(db: Session, reservation: Reservation) -> int | None:
    return repo.queue_position(db, reservation)


def search_reservations(
    db: Session,
    book_id: int | None,
    member_id: int | None,
    status: ReservationStatus | None,
    page: int,
    size: int,
) -> tuple[list[Reservation], int]:
    return repo.search(db, book_id, member_id, status, page, size)


def get_reservation(db: Session, reservation_id: int) -> Reservation:
    reservation = repo.get_with_details(db, reservation_id)
    if reservation is None:
        raise AppError(ErrorCode.NOT_FOUND, "Rezervasyon bulunamadı.", 404)
    return reservation

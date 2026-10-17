"""Rezervasyon ve ceza uç noktaları (personel)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import STAFF_ROLES, DbSession, require_roles
from app.models import Fine, Reservation, User
from app.models.enums import FineStatus, ReservationStatus, UserRole
from app.schemas.common import Page
from app.schemas.reservation import FineDetail, FinePage, ReservationCreate, ReservationOut
from app.services import fine_service, reservation_service

Staff = Annotated[User, Depends(require_roles(*STAFF_ROLES))]
Admin = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
PageNo = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]

reservations = APIRouter(prefix="/reservations", tags=["reservations"])
fines = APIRouter(prefix="/fines", tags=["fines"])


def reservation_out(db: Session, reservation: Reservation) -> ReservationOut:
    return ReservationOut(
        id=reservation.id,
        book_id=reservation.book_id,
        book_title=reservation.book.title,
        member_id=reservation.member_id,
        member_no=reservation.member.member_no,
        member_name=reservation.member.user.full_name,
        status=reservation.status,
        queue_position=reservation_service.queue_position(db, reservation),
        created_at=reservation.created_at,
        ready_at=reservation.ready_at,
        expires_at=reservation.expires_at,
        assigned_barcode=reservation.assigned_copy.barcode if reservation.assigned_copy else None,
    )


def fine_detail(fine: Fine) -> FineDetail:
    return FineDetail(
        id=fine.id,
        loan_id=fine.loan_id,
        member_id=fine.member_id,
        member_no=fine.member.member_no,
        member_name=fine.member.user.full_name,
        book_title=fine.loan.copy.book.title,
        barcode=fine.loan.copy.barcode,
        amount=fine.amount,
        reason=fine.reason,
        status=fine.status,
        created_at=fine.created_at,
        paid_at=fine.paid_at,
    )


# --- Rezervasyon ---


@reservations.get("", response_model=Page[ReservationOut])
def list_reservations(
    db: DbSession,
    _staff: Staff,
    book_id: int | None = None,
    member_id: int | None = None,
    status: ReservationStatus | None = None,
    page: PageNo = 1,
    size: PageSize = 20,
):
    items, total = reservation_service.search_reservations(
        db, book_id, member_id, status, page, size
    )
    return Page(items=[reservation_out(db, r) for r in items], total=total, page=page, size=size)


@reservations.post("", response_model=ReservationOut, status_code=201)
def create_reservation(body: ReservationCreate, db: DbSession, _staff: Staff):
    reservation = reservation_service.create_reservation(db, body.book_id, body.member_id)
    return reservation_out(db, reservation_service.get_reservation(db, reservation.id))


@reservations.delete("/{reservation_id}", response_model=ReservationOut)
def cancel_reservation(reservation_id: int, db: DbSession, _staff: Staff):
    reservation_service.cancel_reservation(db, reservation_id)
    return reservation_out(db, reservation_service.get_reservation(db, reservation_id))


# --- Ceza ---


@fines.get("", response_model=FinePage)
def list_fines(
    db: DbSession,
    _staff: Staff,
    status: FineStatus | None = None,
    member_id: int | None = None,
    page: PageNo = 1,
    size: PageSize = 20,
):
    items, total, amount = fine_service.search_fines(db, status, member_id, page, size)
    return FinePage(
        items=[fine_detail(f) for f in items],
        total=total,
        page=page,
        size=size,
        total_amount=amount,
    )


@fines.post("/{fine_id}/pay", response_model=FineDetail)
def pay_fine(fine_id: int, db: DbSession, staff: Staff):
    fine_service.pay_fine(db, fine_id, staff)
    return fine_detail(fine_service.get_fine(db, fine_id))


@fines.post("/{fine_id}/waive", response_model=FineDetail)
def waive_fine(fine_id: int, db: DbSession, admin: Admin):
    fine_service.waive_fine(db, fine_id, admin)
    return fine_detail(fine_service.get_fine(db, fine_id))

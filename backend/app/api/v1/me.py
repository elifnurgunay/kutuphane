"""Üye paneli (self-servis) uç noktaları: üye yalnızca kendi verisini görür."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession
from app.api.v1.members import member_detail, member_loan_out
from app.api.v1.reservations import reservation_out
from app.models import Member
from app.models.enums import LoanStatus
from app.schemas.member import MemberDetail, MemberFineOut, MemberLoanOut
from app.schemas.reservation import MyReservationCreate, ReservationOut
from app.services import loan_service, member_service, reservation_service

router = APIRouter(prefix="/me", tags=["me"])


def current_member(db: DbSession, user: CurrentUser) -> Member:
    return member_service.get_member_for_user(db, user)


Me = Annotated[Member, Depends(current_member)]


@router.get("/profile", response_model=MemberDetail)
def profile(db: DbSession, member: Me):
    return member_detail(db, member.id)


@router.get("/loans", response_model=list[MemberLoanOut])
def my_loans(db: DbSession, member: Me, status: LoanStatus | None = None):
    return [member_loan_out(loan) for loan in member_service.member_loans(db, member.id, status)]


@router.post("/loans/{loan_id}/renew", response_model=MemberLoanOut)
def renew_my_loan(loan_id: int, db: DbSession, member: Me):
    loan_service.renew_loan(db, loan_id, member_id=member.id)
    return member_loan_out(loan_service.get_loan(db, loan_id))


@router.get("/fines", response_model=list[MemberFineOut])
def my_fines(db: DbSession, member: Me):
    return member_service.member_fines(db, member.id)


@router.get("/reservations", response_model=list[ReservationOut])
def my_reservations(db: DbSession, member: Me):
    return [reservation_out(db, r) for r in member_service.member_reservations(db, member.id)]


@router.post("/reservations", response_model=ReservationOut, status_code=status.HTTP_201_CREATED)
def reserve(body: MyReservationCreate, db: DbSession, member: Me):
    reservation = reservation_service.create_reservation(db, body.book_id, member.id)
    return reservation_out(db, reservation_service.get_reservation(db, reservation.id))


@router.delete("/reservations/{reservation_id}", response_model=ReservationOut)
def cancel_my_reservation(reservation_id: int, db: DbSession, member: Me):
    reservation_service.cancel_reservation(db, reservation_id, member_id=member.id)
    return reservation_out(db, reservation_service.get_reservation(db, reservation_id))

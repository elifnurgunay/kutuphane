"""Üye uç noktaları (yalnız personel)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import STAFF_ROLES, DbSession, require_roles
from app.models import Loan, Reservation
from app.models.enums import LoanStatus, MemberStatus
from app.repositories.member_repository import MemberRow
from app.schemas.common import Page
from app.schemas.member import (
    MemberCreate,
    MemberDetail,
    MemberFineOut,
    MemberLoanOut,
    MemberReservationOut,
    MemberSummary,
    MemberUpdate,
)
from app.services import member_service as svc

router = APIRouter(
    prefix="/members", tags=["members"], dependencies=[Depends(require_roles(*STAFF_ROLES))]
)


def summary_fields(row: MemberRow) -> dict:
    member = row.member
    return {
        "id": member.id,
        "member_no": member.member_no,
        "full_name": member.user.full_name,
        "email": member.user.email,
        "phone": member.phone,
        "member_type": member.member_type,
        "status": member.status,
        "membership_end": member.membership_end,
        "active_loan_count": row.active_loan_count,
    }


def member_detail(db: Session, member_id: int) -> MemberDetail:
    row = svc.get_member_row(db, member_id)
    return MemberDetail(
        **summary_fields(row),
        user_id=row.member.user_id,
        address=row.member.address,
        membership_start=row.member.membership_start,
        unpaid_fine_total=svc.unpaid_fine_total(db, member_id),
    )


def member_loan_out(loan: Loan) -> MemberLoanOut:
    return MemberLoanOut(
        id=loan.id,
        book_id=loan.copy.book_id,
        book_title=loan.copy.book.title,
        barcode=loan.copy.barcode,
        loan_date=loan.loan_date,
        due_date=loan.due_date,
        return_date=loan.return_date,
        renew_count=loan.renew_count,
        status=loan.status,
    )


def member_reservation_out(reservation: Reservation) -> MemberReservationOut:
    return MemberReservationOut(
        id=reservation.id,
        book_id=reservation.book_id,
        book_title=reservation.book.title,
        status=reservation.status,
        created_at=reservation.created_at,
        ready_at=reservation.ready_at,
        expires_at=reservation.expires_at,
    )


@router.get("", response_model=Page[MemberSummary])
def list_members(
    db: DbSession,
    q: str | None = None,
    status: MemberStatus | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    rows, total = svc.search_members(db, q, status, page, size)
    items = [MemberSummary(**summary_fields(row)) for row in rows]
    return Page(items=items, total=total, page=page, size=size)


@router.get("/{member_id}", response_model=MemberDetail)
def get_member(member_id: int, db: DbSession):
    return member_detail(db, member_id)


@router.post("", response_model=MemberDetail, status_code=201)
def create_member(body: MemberCreate, db: DbSession):
    return member_detail(db, svc.create_member(db, body).id)


@router.put("/{member_id}", response_model=MemberDetail)
def update_member(member_id: int, body: MemberUpdate, db: DbSession):
    svc.update_member(db, member_id, body)
    return member_detail(db, member_id)


@router.post("/{member_id}/suspend", response_model=MemberDetail)
def suspend_member(member_id: int, db: DbSession):
    svc.suspend_member(db, member_id)
    return member_detail(db, member_id)


@router.post("/{member_id}/activate", response_model=MemberDetail)
def activate_member(member_id: int, db: DbSession):
    svc.activate_member(db, member_id)
    return member_detail(db, member_id)


@router.get("/{member_id}/loans", response_model=list[MemberLoanOut])
def member_loans(member_id: int, db: DbSession, status: LoanStatus | None = None):
    return [member_loan_out(loan) for loan in svc.member_loans(db, member_id, status)]


@router.get("/{member_id}/fines", response_model=list[MemberFineOut])
def member_fines(member_id: int, db: DbSession):
    return svc.member_fines(db, member_id)


@router.get("/{member_id}/reservations", response_model=list[MemberReservationOut])
def member_reservations(member_id: int, db: DbSession):
    return [member_reservation_out(r) for r in svc.member_reservations(db, member_id)]

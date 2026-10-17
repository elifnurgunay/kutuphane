"""Ödünç, iade, uzatma ve kayıp uç noktaları (yalnız personel)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import STAFF_ROLES, DbSession, require_roles
from app.models import Fine, Loan, User
from app.schemas.common import Page
from app.schemas.loan import (
    EligibilityOut,
    FineOut,
    IssueRequest,
    LoanOut,
    LostResponse,
    ProblemOut,
    ReservedFor,
    ReturnRequest,
    ReturnResponse,
)
from app.services import loan_service as svc

router = APIRouter(prefix="/loans", tags=["loans"])
Staff = Annotated[User, Depends(require_roles(*STAFF_ROLES))]
LoanFilter = Literal["open", "active", "overdue", "returned", "lost"]


def loan_out(loan: Loan) -> LoanOut:
    return LoanOut(
        id=loan.id,
        copy_id=loan.copy_id,
        barcode=loan.copy.barcode,
        book_id=loan.copy.book_id,
        book_title=loan.copy.book.title,
        member_id=loan.member_id,
        member_no=loan.member.member_no,
        member_name=loan.member.user.full_name,
        loan_date=loan.loan_date,
        due_date=loan.due_date,
        return_date=loan.return_date,
        renew_count=loan.renew_count,
        status=loan.status,
    )


def fine_out(fine: Fine) -> FineOut:
    return FineOut(
        id=fine.id,
        amount=fine.amount,
        reason=fine.reason,
        status=fine.status,
        created_at=fine.created_at,
    )


def _reload(db: Session, loan_id: int) -> LoanOut:
    return loan_out(svc.get_loan(db, loan_id))


@router.get("", response_model=Page[LoanOut])
def list_loans(
    db: DbSession,
    _staff: Staff,
    status: LoanFilter | None = None,
    member_id: int | None = None,
    barcode: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    loans, total = svc.search_loans(db, status, member_id, barcode, page, size)
    return Page(items=[loan_out(loan) for loan in loans], total=total, page=page, size=size)


@router.get("/eligibility/{member_id}", response_model=EligibilityOut)
def eligibility(member_id: int, db: DbSession, _staff: Staff):
    result = svc.get_eligibility(db, member_id)
    return EligibilityOut(
        can_borrow=result.can_borrow,
        problems=[ProblemOut(code=p.code, message=p.message) for p in result.problems],
        active_loan_count=result.active_loan_count,
        loan_limit=result.loan_limit,
        unpaid_fine_total=result.unpaid_fine_total,
        max_unpaid_fine=result.max_unpaid_fine,
        overdue_count=result.overdue_count,
    )


@router.get("/{loan_id}", response_model=LoanOut)
def get_loan(loan_id: int, db: DbSession, _staff: Staff):
    return _reload(db, loan_id)


@router.post("", response_model=LoanOut, status_code=201)
def issue_loan(body: IssueRequest, db: DbSession, staff: Staff):
    loan = svc.issue_loan(db, body.member_id, body.barcode, staff)
    return _reload(db, loan.id)


@router.post("/{loan_id}/return", response_model=ReturnResponse)
def return_loan(loan_id: int, db: DbSession, staff: Staff, body: ReturnRequest | None = None):
    body = body or ReturnRequest()
    result = svc.return_loan(
        db, loan_id, staff, damaged=body.damaged, damage_fine=body.damage_fine, notes=body.notes
    )
    reserved_for = None
    if result.reservation is not None:
        member = result.reservation.member
        reserved_for = ReservedFor(
            reservation_id=result.reservation.id,
            member_id=member.id,
            member_no=member.member_no,
            member_name=member.user.full_name,
            expires_at=result.reservation.expires_at,
        )
    return ReturnResponse(
        loan=_reload(db, loan_id),
        fines=[fine_out(f) for f in result.fines],
        reserved_for=reserved_for,
    )


@router.post("/{loan_id}/renew", response_model=LoanOut)
def renew_loan(loan_id: int, db: DbSession, _staff: Staff):
    svc.renew_loan(db, loan_id)
    return _reload(db, loan_id)


@router.post("/{loan_id}/mark-lost", response_model=LostResponse)
def mark_lost(loan_id: int, db: DbSession, _staff: Staff):
    _, fine = svc.mark_lost(db, loan_id)
    return LostResponse(loan=_reload(db, loan_id), fine=fine_out(fine))

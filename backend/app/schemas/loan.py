from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import FineReason, FineStatus, LoanStatus


class IssueRequest(BaseModel):
    member_id: int
    barcode: str = Field(min_length=1, max_length=50)


class ReturnRequest(BaseModel):
    damaged: bool = False
    # Hasar işaretlenirse görevlinin girdiği ceza tutarı (opsiyonel)
    damage_fine: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class LoanOut(BaseModel):
    id: int
    copy_id: int
    barcode: str
    book_id: int
    book_title: str
    member_id: int
    member_no: str
    member_name: str
    loan_date: date
    due_date: date
    return_date: date | None
    renew_count: int
    status: LoanStatus


class FineOut(BaseModel):
    id: int
    amount: Decimal
    reason: FineReason
    status: FineStatus
    created_at: datetime | None


class ReservedFor(BaseModel):
    reservation_id: int
    member_id: int
    member_no: str
    member_name: str
    expires_at: datetime | None


class ReturnResponse(BaseModel):
    loan: LoanOut
    fines: list[FineOut]
    reserved_for: ReservedFor | None


class LostResponse(BaseModel):
    loan: LoanOut
    fine: FineOut


class ProblemOut(BaseModel):
    code: str
    message: str


class EligibilityOut(BaseModel):
    can_borrow: bool
    problems: list[ProblemOut]
    active_loan_count: int
    loan_limit: int
    unpaid_fine_total: Decimal
    max_unpaid_fine: Decimal
    overdue_count: int

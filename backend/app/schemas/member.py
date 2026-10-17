from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    FineReason,
    FineStatus,
    LoanStatus,
    MemberStatus,
    MemberType,
    ReservationStatus,
)


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MemberUpdate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = None
    member_type: MemberType
    membership_start: date
    membership_end: date


class MemberCreate(MemberUpdate):
    # Üyenin ilk şifresi; üye daha sonra kendisi değiştirebilir.
    password: str = Field(min_length=8, max_length=72)


class MemberSummary(BaseModel):
    id: int
    member_no: str
    full_name: str
    email: str
    phone: str | None
    member_type: MemberType
    status: MemberStatus
    membership_end: date
    active_loan_count: int


class MemberDetail(MemberSummary):
    user_id: int
    address: str | None
    membership_start: date
    unpaid_fine_total: Decimal


class MemberLoanOut(_Orm):
    id: int
    book_id: int
    book_title: str
    barcode: str
    loan_date: date
    due_date: date
    return_date: date | None
    renew_count: int
    status: LoanStatus


class MemberFineOut(_Orm):
    id: int
    loan_id: int
    amount: Decimal
    reason: FineReason
    status: FineStatus
    created_at: datetime
    paid_at: datetime | None


class MemberReservationOut(_Orm):
    id: int
    book_id: int
    book_title: str
    status: ReservationStatus
    created_at: datetime
    ready_at: datetime | None
    expires_at: datetime | None

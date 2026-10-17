from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class ActivityOut(BaseModel):
    kind: Literal["loan", "return"]
    day: date
    loan_id: int
    book_title: str
    member_name: str
    member_no: str


class DashboardOut(BaseModel):
    total_books: int
    total_copies: int
    available_copies: int
    active_members: int
    open_loans: int
    overdue_loans: int
    loans_today: int
    returns_today: int
    unpaid_fine_total: Decimal
    recent_activity: list[ActivityOut]


class PopularBookOut(BaseModel):
    book_id: int
    title: str
    authors: str
    loan_count: int


class OverdueItemOut(BaseModel):
    loan_id: int
    book_title: str
    barcode: str
    member_id: int
    member_no: str
    member_name: str
    phone: str | None
    due_date: date
    days_late: int
    estimated_fine: Decimal


class ActiveMemberOut(BaseModel):
    member_id: int
    member_no: str
    full_name: str
    loan_count: int


class CategoryStatOut(BaseModel):
    category_id: int
    name: str
    book_count: int
    copy_count: int
    loan_count: int

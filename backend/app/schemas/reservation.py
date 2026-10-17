from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import FineReason, FineStatus, ReservationStatus
from app.schemas.common import Page


class ReservationCreate(BaseModel):
    book_id: int
    member_id: int


class ReservationOut(BaseModel):
    id: int
    book_id: int
    book_title: str
    member_id: int
    member_no: str
    member_name: str
    status: ReservationStatus
    queue_position: int | None
    created_at: datetime
    ready_at: datetime | None
    expires_at: datetime | None
    assigned_barcode: str | None


class FineDetail(BaseModel):
    id: int
    loan_id: int
    member_id: int
    member_no: str
    member_name: str
    book_title: str
    barcode: str
    amount: Decimal
    reason: FineReason
    status: FineStatus
    created_at: datetime
    paid_at: datetime | None


class FinePage(Page[FineDetail]):
    # Filtreye uyan tüm cezaların toplam tutarı (yalnız bu sayfa değil)
    total_amount: Decimal

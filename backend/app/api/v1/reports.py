"""Rapor uç noktaları; liste raporları ?format=csv ile dışa aktarılır."""

import csv
import io
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import STAFF_ROLES, DbSession, require_roles
from app.core.errors import AppError, ErrorCode
from app.schemas.report import (
    ActiveMemberOut,
    CategoryStatOut,
    DashboardOut,
    OverdueItemOut,
    PopularBookOut,
)
from app.services import report_service as svc

router = APIRouter(
    prefix="/reports", tags=["reports"], dependencies=[Depends(require_roles(*STAFF_ROLES))]
)

Format = Literal["json", "csv"]
Limit = Annotated[int, Query(ge=1, le=100)]


def _period(start: date | None, end: date | None) -> svc.DateRange:
    if start and end and end < start:
        raise AppError(ErrorCode.INVALID_DATE_RANGE, "Bitiş tarihi başlangıçtan önce olamaz.", 400)
    return svc.DateRange(start, end)


def _cell(value: Any) -> str:
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, Decimal):
        return f"{value:.2f}".replace(".", ",")
    return "" if value is None else str(value)


def _csv(filename: str, columns: list[tuple[str, str]], rows: list[Any]) -> Response:
    """Excel'in Türkçe ayarlarıyla açılabilen CSV (UTF-8 BOM, noktalı virgül)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([header for _, header in columns])
    for row in rows:
        data = asdict(row)
        writer.writerow([_cell(data[key]) for key, _ in columns])
    return Response(
        content="﻿" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: DbSession):
    return asdict(svc.dashboard(db))


@router.get("/popular-books", response_model=list[PopularBookOut])
def popular_books(
    db: DbSession,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
    limit: Limit = 10,
    format: Format = "json",
):
    rows = svc.popular_books(db, _period(start, end), limit)
    if format == "csv":
        columns = [("title", "Kitap"), ("authors", "Yazar"), ("loan_count", "Ödünç sayısı")]
        return _csv("populer-kitaplar", columns, rows)
    return [asdict(r) for r in rows]


@router.get("/overdue", response_model=list[OverdueItemOut])
def overdue(db: DbSession, format: Format = "json"):
    rows = svc.overdue(db)
    if format == "csv":
        columns = [
            ("member_no", "Üye no"),
            ("member_name", "Üye"),
            ("phone", "Telefon"),
            ("book_title", "Kitap"),
            ("barcode", "Barkod"),
            ("due_date", "Son teslim"),
            ("days_late", "Gecikme (gün)"),
            ("estimated_fine", "Tahmini ceza (TL)"),
        ]
        return _csv("gecikmis-oduncler", columns, rows)
    return [asdict(r) for r in rows]


@router.get("/active-members", response_model=list[ActiveMemberOut])
def active_members(
    db: DbSession,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
    limit: Limit = 10,
    format: Format = "json",
):
    rows = svc.active_members(db, _period(start, end), limit)
    if format == "csv":
        columns = [("member_no", "Üye no"), ("full_name", "Üye"), ("loan_count", "Ödünç sayısı")]
        return _csv("aktif-uyeler", columns, rows)
    return [asdict(r) for r in rows]


@router.get("/category-stats", response_model=list[CategoryStatOut])
def category_stats(
    db: DbSession,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
    format: Format = "json",
):
    rows = svc.category_stats(db, _period(start, end))
    if format == "csv":
        columns = [
            ("name", "Kategori"),
            ("book_count", "Kitap"),
            ("copy_count", "Nüsha"),
            ("loan_count", "Ödünç"),
        ]
        return _csv("kategori-istatistikleri", columns, rows)
    return [asdict(r) for r in rows]

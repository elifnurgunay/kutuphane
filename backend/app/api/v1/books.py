"""Kitap ve nüsha uç noktaları."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import STAFF_ROLES, CurrentUser, DbSession, require_roles
from app.repositories.book_repository import BookFilters, BookRow
from app.schemas.catalog import (
    BookDetail,
    BookIn,
    BookSummary,
    CopyIn,
    CopyOut,
    CopyUpdate,
    CopyWithBook,
)
from app.schemas.common import Page
from app.services import book_service as svc

staff_only = [Depends(require_roles(*STAFF_ROLES))]
SortKey = Literal["title", "-title", "publish_year", "-publish_year", "created_at", "-created_at"]

books = APIRouter(prefix="/books", tags=["books"])
copies = APIRouter(prefix="/copies", tags=["copies"], dependencies=staff_only)


def _summary(row: BookRow, schema: type[BookSummary] = BookSummary) -> BookSummary:
    counts = {"copy_count": row.copy_count, "available_count": row.available_count}
    fields = {name: getattr(row.book, name) for name in schema.model_fields if name not in counts}
    return schema.model_validate(fields | counts, from_attributes=True)


@books.get("", response_model=Page[BookSummary])
def list_books(
    db: DbSession,
    _user: CurrentUser,
    q: str | None = None,
    category: int | None = None,
    author: int | None = None,
    available: bool | None = None,
    sort: SortKey = "title",
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    filters = BookFilters(
        q=q, category_id=category, author_id=author, available=available, sort=sort
    )
    rows, total = svc.search_books(db, filters, page, size)
    return Page(items=[_summary(row) for row in rows], total=total, page=page, size=size)


@books.get("/{book_id}", response_model=BookDetail)
def get_book(book_id: int, db: DbSession, _user: CurrentUser):
    return _summary(svc.get_book_row(db, book_id), BookDetail)


@books.post("", response_model=BookDetail, status_code=201, dependencies=staff_only)
def create_book(body: BookIn, db: DbSession):
    book = svc.create_book(db, body)
    return _summary(svc.get_book_row(db, book.id), BookDetail)


@books.put("/{book_id}", response_model=BookDetail, dependencies=staff_only)
def update_book(book_id: int, body: BookIn, db: DbSession):
    svc.update_book(db, book_id, body)
    return _summary(svc.get_book_row(db, book_id), BookDetail)


@books.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=staff_only)
def delete_book(book_id: int, db: DbSession) -> None:
    svc.delete_book(db, book_id)


@books.get("/{book_id}/copies", response_model=list[CopyOut], dependencies=staff_only)
def list_copies(book_id: int, db: DbSession):
    return svc.list_copies(db, book_id)


@books.post("/{book_id}/copies", response_model=CopyOut, status_code=201, dependencies=staff_only)
def add_copy(book_id: int, body: CopyIn, db: DbSession):
    return svc.add_copy(db, book_id, body)


@copies.get("/barcode/{barcode}", response_model=CopyWithBook)
def get_copy_by_barcode(barcode: str, db: DbSession):
    return svc.get_copy_by_barcode(db, barcode)


@copies.put("/{copy_id}", response_model=CopyOut)
def update_copy(copy_id: int, body: CopyUpdate, db: DbSession):
    return svc.update_copy(db, copy_id, body)

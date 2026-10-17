from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CopyStatus


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Yazar / Yayınevi / Kategori ---


class AuthorIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    birth_year: int | None = Field(default=None, ge=0, le=2100)
    bio: str | None = None


class AuthorOut(_Orm):
    id: int
    full_name: str
    birth_year: int | None
    bio: str | None


class PublisherIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class PublisherOut(_Orm):
    id: int
    name: str


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: int | None = None


class CategoryOut(_Orm):
    id: int
    name: str
    parent_id: int | None


# --- Kitap ---


class BookIn(BaseModel):
    isbn: str | None = Field(default=None, max_length=20)
    title: str = Field(min_length=1, max_length=255)
    subtitle: str | None = Field(default=None, max_length=255)
    publisher_id: int | None = None
    publish_year: int | None = Field(default=None, ge=0, le=2100)
    page_count: int | None = Field(default=None, ge=1)
    language: str | None = Field(default=None, max_length=30)
    description: str | None = None
    cover_url: str | None = Field(default=None, max_length=500)
    author_ids: list[int] = Field(min_length=1)
    category_ids: list[int] = Field(min_length=1)


class AuthorRef(_Orm):
    id: int
    full_name: str


class BookSummary(_Orm):
    id: int
    isbn: str | None
    title: str
    subtitle: str | None
    publish_year: int | None
    publisher: PublisherOut | None
    authors: list[AuthorRef]
    categories: list[CategoryOut]
    copy_count: int
    available_count: int


class BookDetail(BookSummary):
    page_count: int | None
    language: str | None
    description: str | None
    cover_url: str | None
    created_at: datetime


# --- Nüsha ---

ManualCopyStatus = Literal["available", "damaged", "maintenance", "lost"]


class CopyIn(BaseModel):
    shelf_location: str | None = Field(default=None, max_length=30)
    acquired_at: date | None = None
    notes: str | None = None


class CopyUpdate(CopyIn):
    # ödünçte/ayrılmış durumları yalnızca ödünç ve rezervasyon akışları değiştirir
    status: ManualCopyStatus | None = None


class BookRef(_Orm):
    id: int
    title: str


class CopyOut(_Orm):
    id: int
    book_id: int
    barcode: str
    shelf_location: str | None
    status: CopyStatus
    acquired_at: date | None
    notes: str | None


class CopyWithBook(CopyOut):
    book: BookRef

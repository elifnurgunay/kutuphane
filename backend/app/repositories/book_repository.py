from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Author, Book, BookCopy, Category
from app.models.enums import CopyStatus
from app.repositories.pagination import paginate

copy_count = (
    select(func.count(BookCopy.id))
    .where(BookCopy.book_id == Book.id)
    .correlate(Book)
    .scalar_subquery()
    .label("copy_count")
)
available_count = (
    select(func.count(BookCopy.id))
    .where(BookCopy.book_id == Book.id, BookCopy.status == CopyStatus.AVAILABLE)
    .correlate(Book)
    .scalar_subquery()
    .label("available_count")
)

SORTS: dict[str, Any] = {
    "title": Book.title.asc(),
    "-title": Book.title.desc(),
    "publish_year": Book.publish_year.asc(),
    "-publish_year": Book.publish_year.desc(),
    "created_at": Book.created_at.asc(),
    "-created_at": Book.created_at.desc(),
}


@dataclass(frozen=True)
class BookFilters:
    q: str | None = None
    category_id: int | None = None
    author_id: int | None = None
    available: bool | None = None
    sort: str = "title"


@dataclass(frozen=True)
class BookRow:
    book: Book
    copy_count: int
    available_count: int


def _base_query() -> Select[Any]:
    return select(Book, copy_count, available_count).options(
        selectinload(Book.authors), selectinload(Book.categories), selectinload(Book.publisher)
    )


def search(db: Session, filters: BookFilters, page: int, size: int) -> tuple[list[BookRow], int]:
    stmt = _base_query()
    if filters.q and filters.q.strip():
        term = filters.q.strip()
        conditions = [
            Book.title.ilike(f"%{term}%"),
            Book.subtitle.ilike(f"%{term}%"),
            Book.authors.any(Author.full_name.ilike(f"%{term}%")),
        ]
        isbn_digits = term.replace("-", "").replace(" ", "")
        if isbn_digits.isdigit():
            conditions.append(Book.isbn.like(f"%{isbn_digits}%"))
        stmt = stmt.where(or_(*conditions))
    if filters.category_id is not None:
        stmt = stmt.where(Book.categories.any(Category.id == filters.category_id))
    if filters.author_id is not None:
        stmt = stmt.where(Book.authors.any(Author.id == filters.author_id))
    if filters.available is True:
        stmt = stmt.where(available_count > 0)
    elif filters.available is False:
        stmt = stmt.where(available_count == 0)
    stmt = stmt.order_by(SORTS.get(filters.sort, SORTS["title"]), Book.id)

    rows, total = paginate(db, stmt, page, size)
    return [BookRow(*row) for row in rows], total


def get_row(db: Session, book_id: int) -> BookRow | None:
    row = db.execute(_base_query().where(Book.id == book_id)).first()
    return BookRow(*row) if row else None

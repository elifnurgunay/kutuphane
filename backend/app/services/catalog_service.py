"""Yazar, yayınevi ve kategori yönetimi."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.models import Author, Book, Category, Publisher
from app.models.catalog import book_authors, book_categories
from app.repositories.pagination import paginate
from app.schemas.catalog import AuthorIn, CategoryIn, PublisherIn


def _get_or_404(db: Session, model: type, entity_id: int, label: str) -> Any:
    obj = db.get(model, entity_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, f"{label} bulunamadı.", 404)
    return obj


def _in_use(label: str) -> AppError:
    return AppError(
        ErrorCode.ENTITY_IN_USE, f"{label} kitaplarda kullanıldığı için silinemez.", 409
    )


# --- Yazar ---


def get_author(db: Session, author_id: int) -> Author:
    return _get_or_404(db, Author, author_id, "Yazar")


def list_authors(db: Session, q: str | None, page: int, size: int) -> tuple[list[Author], int]:
    stmt = select(Author).order_by(Author.full_name)
    if q:
        stmt = stmt.where(Author.full_name.ilike(f"%{q.strip()}%"))
    rows, total = paginate(db, stmt, page, size)
    return [row[0] for row in rows], total


def create_author(db: Session, data: AuthorIn) -> Author:
    author = Author(**data.model_dump())
    db.add(author)
    db.commit()
    return author


def update_author(db: Session, author_id: int, data: AuthorIn) -> Author:
    author = get_author(db, author_id)
    for field, value in data.model_dump().items():
        setattr(author, field, value)
    db.commit()
    return author


def delete_author(db: Session, author_id: int) -> None:
    author = get_author(db, author_id)
    if db.scalar(select(book_authors.c.book_id).where(book_authors.c.author_id == author_id)):
        raise _in_use("Yazar")
    db.delete(author)
    db.commit()


# --- Yayınevi ---


def get_publisher(db: Session, publisher_id: int) -> Publisher:
    return _get_or_404(db, Publisher, publisher_id, "Yayınevi")


def _ensure_publisher_name_free(db: Session, name: str, exclude_id: int | None = None) -> None:
    stmt = select(Publisher.id).where(func.lower(Publisher.name) == name.strip().lower())
    if exclude_id is not None:
        stmt = stmt.where(Publisher.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise AppError(ErrorCode.NAME_EXISTS, "Bu adda bir yayınevi zaten var.", 409)


def list_publishers(
    db: Session, q: str | None, page: int, size: int
) -> tuple[list[Publisher], int]:
    stmt = select(Publisher).order_by(Publisher.name)
    if q:
        stmt = stmt.where(Publisher.name.ilike(f"%{q.strip()}%"))
    rows, total = paginate(db, stmt, page, size)
    return [row[0] for row in rows], total


def create_publisher(db: Session, data: PublisherIn) -> Publisher:
    _ensure_publisher_name_free(db, data.name)
    publisher = Publisher(name=data.name.strip())
    db.add(publisher)
    db.commit()
    return publisher


def update_publisher(db: Session, publisher_id: int, data: PublisherIn) -> Publisher:
    publisher = get_publisher(db, publisher_id)
    _ensure_publisher_name_free(db, data.name, exclude_id=publisher_id)
    publisher.name = data.name.strip()
    db.commit()
    return publisher


def delete_publisher(db: Session, publisher_id: int) -> None:
    publisher = get_publisher(db, publisher_id)
    if db.scalar(select(Book.id).where(Book.publisher_id == publisher_id).limit(1)):
        raise _in_use("Yayınevi")
    db.delete(publisher)
    db.commit()


# --- Kategori ---


def get_category(db: Session, category_id: int) -> Category:
    return _get_or_404(db, Category, category_id, "Kategori")


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


def _ensure_category_name_free(db: Session, name: str, exclude_id: int | None = None) -> None:
    stmt = select(Category.id).where(func.lower(Category.name) == name.strip().lower())
    if exclude_id is not None:
        stmt = stmt.where(Category.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise AppError(ErrorCode.NAME_EXISTS, "Bu adda bir kategori zaten var.", 409)


def _validate_parent(db: Session, parent_id: int | None, category_id: int | None) -> None:
    if parent_id is None:
        return
    parent = db.get(Category, parent_id)
    if parent is None:
        raise AppError(ErrorCode.INVALID_REFERENCE, "Üst kategori bulunamadı.", 400)
    # Üst kategori zinciri düzenlenen kategoriye geri dönmemeli.
    node: Category | None = parent
    while node is not None:
        if node.id == category_id:
            raise AppError(
                ErrorCode.CATEGORY_CYCLE, "Kategori kendi alt kategorisinin altına taşınamaz.", 400
            )
        node = node.parent


def create_category(db: Session, data: CategoryIn) -> Category:
    _ensure_category_name_free(db, data.name)
    _validate_parent(db, data.parent_id, None)
    category = Category(name=data.name.strip(), parent_id=data.parent_id)
    db.add(category)
    db.commit()
    return category


def update_category(db: Session, category_id: int, data: CategoryIn) -> Category:
    category = get_category(db, category_id)
    _ensure_category_name_free(db, data.name, exclude_id=category_id)
    _validate_parent(db, data.parent_id, category_id)
    category.name = data.name.strip()
    category.parent_id = data.parent_id
    db.commit()
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    if db.scalar(select(Category.id).where(Category.parent_id == category_id).limit(1)):
        raise AppError(ErrorCode.ENTITY_IN_USE, "Alt kategorisi olan kategori silinemez.", 409)
    if db.scalar(
        select(book_categories.c.book_id).where(book_categories.c.category_id == category_id)
    ):
        raise _in_use("Kategori")
    db.delete(category)
    db.commit()

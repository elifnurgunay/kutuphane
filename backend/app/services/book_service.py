"""Kitap (eser) ve nüsha yönetimi."""

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.models import Author, Book, BookCopy, Category, Loan, Publisher, Reservation
from app.models.enums import CopyStatus
from app.repositories import book_repository
from app.repositories.book_repository import BookFilters, BookRow
from app.schemas.catalog import BookIn, CopyIn, CopyUpdate
from app.services.isbn import normalize_isbn

BARCODE_PREFIX = "KTP"
# Ödünç/rezervasyon akışlarının yönettiği durumlar elle değiştirilemez.
FLOW_MANAGED_STATUSES = {CopyStatus.LOANED, CopyStatus.RESERVED}


def _book_not_found() -> AppError:
    return AppError(ErrorCode.NOT_FOUND, "Kitap bulunamadı.", 404)


def get_book(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise _book_not_found()
    return book


def get_book_row(db: Session, book_id: int) -> BookRow:
    row = book_repository.get_row(db, book_id)
    if row is None:
        raise _book_not_found()
    return row


def search_books(
    db: Session, filters: BookFilters, page: int, size: int
) -> tuple[list[BookRow], int]:
    return book_repository.search(db, filters, page, size)


def _load_all(db: Session, model: type, ids: list[int], label: str) -> list:
    unique_ids = list(dict.fromkeys(ids))
    items = list(db.scalars(select(model).where(model.id.in_(unique_ids))))
    if len(items) != len(unique_ids):
        raise AppError(ErrorCode.INVALID_REFERENCE, f"Seçilen {label} bulunamadı.", 400)
    order = {item_id: i for i, item_id in enumerate(unique_ids)}
    return sorted(items, key=lambda item: order[item.id])


def _apply(db: Session, book: Book, data: BookIn) -> None:
    isbn = normalize_isbn(data.isbn)
    if isbn is not None:
        duplicate = select(Book.id).where(Book.isbn == isbn, Book.id != (book.id or 0))
        if db.scalar(duplicate) is not None:
            raise AppError(ErrorCode.ISBN_EXISTS, "Bu ISBN ile kayıtlı bir kitap zaten var.", 409)
    if data.publisher_id is not None and db.get(Publisher, data.publisher_id) is None:
        raise AppError(ErrorCode.INVALID_REFERENCE, "Seçilen yayınevi bulunamadı.", 400)

    fields = data.model_dump(exclude={"isbn", "author_ids", "category_ids"})
    for field, value in fields.items():
        setattr(book, field, value)
    book.isbn = isbn
    book.authors = _load_all(db, Author, data.author_ids, "yazar")
    book.categories = _load_all(db, Category, data.category_ids, "kategori")


def create_book(db: Session, data: BookIn) -> Book:
    book = Book()
    _apply(db, book, data)
    db.add(book)
    db.commit()
    return book


def update_book(db: Session, book_id: int, data: BookIn) -> Book:
    book = get_book(db, book_id)
    _apply(db, book, data)
    db.commit()
    return book


def delete_book(db: Session, book_id: int) -> None:
    book = get_book(db, book_id)
    has_loans = db.scalar(
        select(exists().where(Loan.copy_id == BookCopy.id, BookCopy.book_id == book_id))
    )
    has_reservations = db.scalar(select(exists().where(Reservation.book_id == book_id)))
    if has_loans or has_reservations:
        raise AppError(
            ErrorCode.ENTITY_IN_USE,
            "Ödünç veya rezervasyon geçmişi olan kitap silinemez.",
            409,
        )
    db.delete(book)
    db.commit()


# --- Nüsha ---


def next_barcode(db: Session, book_id: int) -> str:
    """KTP-<kitap id>-<sıra> biçiminde, kitabın bir sonraki barkodunu üretir."""
    prefix = f"{BARCODE_PREFIX}-{book_id:04d}-"
    barcodes = db.scalars(select(BookCopy.barcode).where(BookCopy.barcode.startswith(prefix)))
    used = [int(code[len(prefix) :]) for code in barcodes if code[len(prefix) :].isdigit()]
    return f"{prefix}{max(used, default=0) + 1:02d}"


def list_copies(db: Session, book_id: int) -> list[BookCopy]:
    get_book(db, book_id)
    return list(
        db.scalars(select(BookCopy).where(BookCopy.book_id == book_id).order_by(BookCopy.barcode))
    )


def add_copy(db: Session, book_id: int, data: CopyIn) -> BookCopy:
    get_book(db, book_id)
    copy = BookCopy(
        book_id=book_id,
        barcode=next_barcode(db, book_id),
        status=CopyStatus.AVAILABLE,
        **data.model_dump(),
    )
    db.add(copy)
    db.commit()
    return copy


def _copy_not_found() -> AppError:
    return AppError(ErrorCode.NOT_FOUND, "Nüsha bulunamadı.", 404)


def get_copy(db: Session, copy_id: int) -> BookCopy:
    copy = db.get(BookCopy, copy_id)
    if copy is None:
        raise _copy_not_found()
    return copy


def get_copy_by_barcode(db: Session, barcode: str) -> BookCopy:
    copy = db.scalar(select(BookCopy).where(BookCopy.barcode == barcode.strip().upper()))
    if copy is None:
        raise _copy_not_found()
    return copy


def update_copy(db: Session, copy_id: int, data: CopyUpdate) -> BookCopy:
    copy = get_copy(db, copy_id)
    if data.status is not None and data.status != copy.status:
        if copy.status in FLOW_MANAGED_STATUSES:
            raise AppError(
                ErrorCode.COPY_STATUS_LOCKED,
                "Ödünçteki veya rezerve edilmiş nüshanın durumu elle değiştirilemez.",
                409,
            )
        copy.status = CopyStatus(data.status)
    copy.shelf_location = data.shelf_location
    copy.acquired_at = data.acquired_at
    copy.notes = data.notes
    db.commit()
    return copy

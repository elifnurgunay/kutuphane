from datetime import date

import pytest

from app.core.errors import AppError, ErrorCode
from app.models import Loan, Member, Reservation
from app.models.enums import CopyStatus, MemberType, UserRole
from app.repositories.book_repository import BookFilters
from app.schemas.catalog import AuthorIn, BookIn, CategoryIn, CopyIn, CopyUpdate, PublisherIn
from app.services import book_service as svc
from app.services import catalog_service
from app.services.isbn import normalize_isbn


def _error_code(fn, *args) -> ErrorCode:
    with pytest.raises(AppError) as exc_info:
        fn(*args)
    return exc_info.value.code


@pytest.fixture
def refs(db):
    return {
        "dostoyevski": catalog_service.create_author(db, AuthorIn(full_name="Fyodor Dostoyevski")),
        "pamuk": catalog_service.create_author(db, AuthorIn(full_name="Orhan Pamuk")),
        "roman": catalog_service.create_category(db, CategoryIn(name="Roman")),
        "siir": catalog_service.create_category(db, CategoryIn(name="Şiir")),
        "can": catalog_service.create_publisher(db, PublisherIn(name="Can Yayınları")),
    }


def _book_in(refs, **overrides) -> BookIn:
    data = {
        "title": "Suç ve Ceza",
        "isbn": "978-975-07-1938-7",
        "publisher_id": refs["can"].id,
        "author_ids": [refs["dostoyevski"].id],
        "category_ids": [refs["roman"].id],
    }
    return BookIn(**(data | overrides))


# --- ISBN ---


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("978-975-07-1938-7", "9789750719387"),
        ("0-306-40615-2", "0306406152"),
        ("080442957x", "080442957X"),
        ("  ", None),
        (None, None),
    ],
)
def test_normalize_isbn(raw, expected):
    assert normalize_isbn(raw) == expected


@pytest.mark.parametrize("raw", ["9789750719388", "12345", "0-306-40615-3", "ABCDEFGHIJ"])
def test_normalize_isbn_rejects_invalid(raw):
    assert _error_code(normalize_isbn, raw) == ErrorCode.INVALID_ISBN


# --- Kitap ---


def test_create_and_get_book(db, refs):
    book = svc.create_book(db, _book_in(refs))

    row = svc.get_book_row(db, book.id)
    assert row.book.isbn == "9789750719387"
    assert [a.full_name for a in row.book.authors] == ["Fyodor Dostoyevski"]
    assert row.book.publisher.name == "Can Yayınları"
    assert (row.copy_count, row.available_count) == (0, 0)


def test_create_book_rejects_duplicate_isbn(db, refs):
    svc.create_book(db, _book_in(refs))
    code = _error_code(svc.create_book, db, _book_in(refs, title="Başka"))
    assert code == ErrorCode.ISBN_EXISTS


def test_create_book_rejects_unknown_references(db, refs):
    assert _error_code(svc.create_book, db, _book_in(refs, author_ids=[999])) == (
        ErrorCode.INVALID_REFERENCE
    )
    assert _error_code(svc.create_book, db, _book_in(refs, category_ids=[999])) == (
        ErrorCode.INVALID_REFERENCE
    )
    assert _error_code(svc.create_book, db, _book_in(refs, publisher_id=999)) == (
        ErrorCode.INVALID_REFERENCE
    )


def test_update_book_keeps_own_isbn_and_replaces_relations(db, refs):
    book = svc.create_book(db, _book_in(refs))
    updated = svc.update_book(
        db,
        book.id,
        _book_in(refs, author_ids=[refs["pamuk"].id], category_ids=[refs["siir"].id]),
    )
    assert [a.full_name for a in updated.authors] == ["Orhan Pamuk"]
    assert [c.name for c in updated.categories] == ["Şiir"]
    assert updated.isbn == "9789750719387"


def test_delete_book_removes_copies(db, refs):
    book = svc.create_book(db, _book_in(refs))
    copy = svc.add_copy(db, book.id, CopyIn())

    svc.delete_book(db, book.id)
    assert _error_code(svc.get_book, db, book.id) == ErrorCode.NOT_FOUND
    assert _error_code(svc.get_copy, db, copy.id) == ErrorCode.NOT_FOUND


def _member(db, make_user) -> Member:
    member = Member(
        user=make_user(UserRole.MEMBER),
        member_no="UYE-000001",
        member_type=MemberType.STUDENT,
        membership_start=date(2026, 1, 1),
        membership_end=date(2027, 1, 1),
    )
    db.add(member)
    db.commit()
    return member


def test_book_with_loan_history_cannot_be_deleted(db, refs, make_user):
    book = svc.create_book(db, _book_in(refs))
    copy = svc.add_copy(db, book.id, CopyIn())
    staff = make_user(UserRole.LIBRARIAN)
    db.add(
        Loan(
            copy_id=copy.id,
            member=_member(db, make_user),
            issued_by=staff.id,
            loan_date=date(2026, 10, 1),
            due_date=date(2026, 10, 16),
        )
    )
    db.commit()

    assert _error_code(svc.delete_book, db, book.id) == ErrorCode.ENTITY_IN_USE


def test_book_with_reservation_cannot_be_deleted(db, refs, make_user):
    book = svc.create_book(db, _book_in(refs))
    db.add(Reservation(book_id=book.id, member=_member(db, make_user)))
    db.commit()

    assert _error_code(svc.delete_book, db, book.id) == ErrorCode.ENTITY_IN_USE


# --- Arama ---


@pytest.fixture
def catalog(db, refs):
    suc = svc.create_book(db, _book_in(refs, publish_year=1866))
    svc.add_copy(db, suc.id, CopyIn())
    kirmizi = svc.create_book(
        db,
        _book_in(
            refs,
            title="Benim Adım Kırmızı",
            isbn=None,
            publish_year=1998,
            author_ids=[refs["pamuk"].id],
        ),
    )
    loaned = svc.add_copy(db, kirmizi.id, CopyIn())
    loaned.status = CopyStatus.LOANED
    siir = svc.create_book(
        db,
        _book_in(refs, title="Şiirler", isbn=None, category_ids=[refs["siir"].id]),
    )
    db.commit()
    return {"suc": suc, "kirmizi": kirmizi, "siir": siir}


def _titles(db, **filters) -> list[str]:
    rows, _ = svc.search_books(db, BookFilters(**filters), page=1, size=50)
    return [row.book.title for row in rows]


def test_search_by_title_author_and_isbn(db, catalog):
    assert _titles(db, q="kırmızı") == ["Benim Adım Kırmızı"]
    assert _titles(db, q="pamuk") == ["Benim Adım Kırmızı"]
    assert _titles(db, q="978-975-07") == ["Suç ve Ceza"]


def test_filter_by_category_author_and_availability(db, catalog, refs):
    assert _titles(db, category_id=refs["siir"].id) == ["Şiirler"]
    assert _titles(db, author_id=refs["pamuk"].id) == ["Benim Adım Kırmızı"]
    assert _titles(db, available=True) == ["Suç ve Ceza"]
    assert _titles(db, available=False) == ["Benim Adım Kırmızı", "Şiirler"]


def test_search_sort_and_counts(db, catalog):
    assert _titles(db, sort="-publish_year")[:2] == ["Benim Adım Kırmızı", "Suç ve Ceza"]

    rows, total = svc.search_books(db, BookFilters(), page=1, size=2)
    assert total == 3
    assert len(rows) == 2
    counts = {row.book.title: (row.copy_count, row.available_count) for row in rows}
    assert counts["Benim Adım Kırmızı"] == (1, 0)


# --- Nüsha ---


def test_barcode_generation_continues_sequence(db, refs):
    book = svc.create_book(db, _book_in(refs))
    first = svc.add_copy(db, book.id, CopyIn(shelf_location="A-01-1"))
    second = svc.add_copy(db, book.id, CopyIn())

    assert first.barcode == f"KTP-{book.id:04d}-01"
    assert second.barcode == f"KTP-{book.id:04d}-02"
    assert first.status == CopyStatus.AVAILABLE
    assert [c.barcode for c in svc.list_copies(db, book.id)] == [first.barcode, second.barcode]


def test_get_copy_by_barcode_is_case_insensitive(db, refs):
    book = svc.create_book(db, _book_in(refs))
    copy = svc.add_copy(db, book.id, CopyIn())

    assert svc.get_copy_by_barcode(db, copy.barcode.lower()).id == copy.id
    assert _error_code(svc.get_copy_by_barcode, db, "KTP-9999-99") == ErrorCode.NOT_FOUND


def test_update_copy_status_and_location(db, refs):
    book = svc.create_book(db, _book_in(refs))
    copy = svc.add_copy(db, book.id, CopyIn())

    updated = svc.update_copy(db, copy.id, CopyUpdate(status="damaged", shelf_location="B-02-1"))
    assert updated.status == CopyStatus.DAMAGED
    assert updated.shelf_location == "B-02-1"


def test_loaned_copy_status_is_locked(db, refs):
    book = svc.create_book(db, _book_in(refs))
    copy = svc.add_copy(db, book.id, CopyIn())
    copy.status = CopyStatus.LOANED
    db.commit()

    code = _error_code(svc.update_copy, db, copy.id, CopyUpdate(status="available"))
    assert code == ErrorCode.COPY_STATUS_LOCKED
    # durum değişmiyorsa diğer alanlar güncellenebilir
    assert svc.update_copy(db, copy.id, CopyUpdate(notes="Kapak yıpranmış")).notes == (
        "Kapak yıpranmış"
    )

import pytest

from app.core.errors import AppError, ErrorCode
from app.models import Book
from app.schemas.catalog import AuthorIn, CategoryIn, PublisherIn
from app.services import catalog_service as svc


def _error_code(fn, *args) -> ErrorCode:
    with pytest.raises(AppError) as exc_info:
        fn(*args)
    return exc_info.value.code


# --- Yazar ---


def test_author_crud(db):
    author = svc.create_author(db, AuthorIn(full_name="Sabahattin Ali", birth_year=1907))
    assert svc.get_author(db, author.id).birth_year == 1907

    svc.update_author(db, author.id, AuthorIn(full_name="Sabahattin Ali", bio="Yazar"))
    assert svc.get_author(db, author.id).bio == "Yazar"
    assert svc.get_author(db, author.id).birth_year is None

    svc.delete_author(db, author.id)
    assert _error_code(svc.get_author, db, author.id) == ErrorCode.NOT_FOUND


def test_list_authors_search_and_pagination(db):
    for name in ["Orhan Pamuk", "Orhan Veli Kanık", "Yaşar Kemal"]:
        svc.create_author(db, AuthorIn(full_name=name))

    items, total = svc.list_authors(db, "orhan", page=1, size=1)
    assert total == 2
    assert [a.full_name for a in items] == ["Orhan Pamuk"]

    items, _ = svc.list_authors(db, "orhan", page=2, size=1)
    assert [a.full_name for a in items] == ["Orhan Veli Kanık"]


def test_author_with_books_cannot_be_deleted(db):
    author = svc.create_author(db, AuthorIn(full_name="Oğuz Atay"))
    db.add(Book(title="Tutunamayanlar", authors=[author]))
    db.commit()

    assert _error_code(svc.delete_author, db, author.id) == ErrorCode.ENTITY_IN_USE


# --- Yayınevi ---


def test_publisher_name_must_be_unique_case_insensitive(db):
    svc.create_publisher(db, PublisherIn(name="Can Yayınları"))
    code = _error_code(svc.create_publisher, db, PublisherIn(name="can yayınları"))
    assert code == ErrorCode.NAME_EXISTS


def test_publisher_update_allows_keeping_own_name(db):
    publisher = svc.create_publisher(db, PublisherIn(name="Metis"))
    assert svc.update_publisher(db, publisher.id, PublisherIn(name="Metis")).name == "Metis"


def test_publisher_with_books_cannot_be_deleted(db):
    publisher = svc.create_publisher(db, PublisherIn(name="Metis"))
    db.add(Book(title="Kitap", publisher=publisher))
    db.commit()

    assert _error_code(svc.delete_publisher, db, publisher.id) == ErrorCode.ENTITY_IN_USE


def test_list_publishers(db):
    svc.create_publisher(db, PublisherIn(name="Metis"))
    svc.create_publisher(db, PublisherIn(name="Can"))
    items, total = svc.list_publishers(db, None, page=1, size=10)
    assert total == 2
    assert [p.name for p in items] == ["Can", "Metis"]


# --- Kategori ---


def test_category_tree(db):
    parent = svc.create_category(db, CategoryIn(name="Edebiyat"))
    child = svc.create_category(db, CategoryIn(name="Roman", parent_id=parent.id))

    assert child.parent_id == parent.id
    assert [c.name for c in svc.list_categories(db)] == ["Edebiyat", "Roman"]


def test_category_unknown_parent(db):
    code = _error_code(svc.create_category, db, CategoryIn(name="Roman", parent_id=999))
    assert code == ErrorCode.INVALID_REFERENCE


def test_category_cannot_become_its_own_descendant(db):
    root = svc.create_category(db, CategoryIn(name="Edebiyat"))
    child = svc.create_category(db, CategoryIn(name="Roman", parent_id=root.id))

    code = _error_code(
        svc.update_category, db, root.id, CategoryIn(name="Edebiyat", parent_id=child.id)
    )
    assert code == ErrorCode.CATEGORY_CYCLE
    code = _error_code(
        svc.update_category, db, root.id, CategoryIn(name="Edebiyat", parent_id=root.id)
    )
    assert code == ErrorCode.CATEGORY_CYCLE


def test_category_with_children_or_books_cannot_be_deleted(db):
    root = svc.create_category(db, CategoryIn(name="Edebiyat"))
    child = svc.create_category(db, CategoryIn(name="Roman", parent_id=root.id))
    db.add(Book(title="Kitap", categories=[child]))
    db.commit()

    assert _error_code(svc.delete_category, db, root.id) == ErrorCode.ENTITY_IN_USE
    assert _error_code(svc.delete_category, db, child.id) == ErrorCode.ENTITY_IN_USE


def test_category_name_unique(db):
    svc.create_category(db, CategoryIn(name="Roman"))
    assert _error_code(svc.create_category, db, CategoryIn(name="ROMAN")) == ErrorCode.NAME_EXISTS


def test_delete_empty_category(db):
    category = svc.create_category(db, CategoryIn(name="Şiir"))
    svc.delete_category(db, category.id)
    assert svc.list_categories(db) == []

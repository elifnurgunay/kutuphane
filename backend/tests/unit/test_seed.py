from datetime import date

import pytest
from sqlalchemy import func, select

from app import seed
from app.models import Book, BookCopy, Loan, Member, User
from app.models.enums import CopyStatus, LoanStatus, UserRole


def _count(db, column, *where):
    return db.scalar(select(func.count(column)).where(*where))


def test_seed_creates_plan_counts(db):
    seed.run(db, today=date(2026, 10, 17))

    assert _count(db, User.id, User.role == UserRole.ADMIN) == 1
    assert _count(db, User.id, User.role == UserRole.LIBRARIAN) == 2
    assert _count(db, Member.id) == 20
    assert _count(db, Book.id) == 100
    assert _count(db, BookCopy.id) == 250
    assert _count(db, Loan.id, Loan.status == LoanStatus.RETURNED) == seed.RETURNED_LOAN_COUNT


def test_seed_is_consistent(db):
    seed.run(db, today=date(2026, 10, 17))

    active = db.scalars(select(Loan).where(Loan.status == LoanStatus.ACTIVE)).all()
    assert len(active) == seed.ACTIVE_LOAN_COUNT
    assert all(loan.copy.status == CopyStatus.LOANED for loan in active)
    assert _count(db, BookCopy.id, BookCopy.status == CopyStatus.LOANED) == len(active)

    example = db.scalar(select(BookCopy).where(BookCopy.barcode == "KTP-0012-01"))
    assert example.book.title == "Suç ve Ceza"
    assert example.book.isbn == "9789750719387"
    ayse_loan = next(loan for loan in active if loan.copy is example)
    assert ayse_loan.member.user.full_name == "Ayşe Yılmaz"
    assert ayse_loan.loan_date == date(2026, 10, 10)
    assert ayse_loan.due_date == date(2026, 10, 25)


def test_seed_refuses_non_empty_database(db, make_user):
    make_user()
    with pytest.raises(RuntimeError):
        seed.run(db)

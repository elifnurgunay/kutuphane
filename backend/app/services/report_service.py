"""Gösterge paneli ve raporlar."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Book, BookCopy, Category, Fine, Loan, Member, User
from app.models.catalog import book_categories
from app.models.enums import CopyStatus, FineStatus, MemberStatus
from app.repositories.loan_repository import is_overdue
from app.repositories.member_repository import OPEN_LOAN_STATUSES
from app.services import fine_service, settings_service


@dataclass(frozen=True)
class DateRange:
    start: date | None = None
    end: date | None = None

    def apply(self, column):
        conditions = []
        if self.start is not None:
            conditions.append(column >= self.start)
        if self.end is not None:
            conditions.append(column <= self.end)
        return conditions


# --- Gösterge paneli ---


@dataclass(frozen=True)
class Activity:
    kind: str  # "loan" | "return"
    day: date
    loan_id: int
    book_title: str
    member_name: str
    member_no: str


@dataclass(frozen=True)
class Dashboard:
    total_books: int
    total_copies: int
    available_copies: int
    active_members: int
    open_loans: int
    overdue_loans: int
    loans_today: int
    returns_today: int
    unpaid_fine_total: Decimal
    recent_activity: list[Activity]


def _count(db: Session, column, *conditions) -> int:
    return db.scalar(select(func.count(column)).where(*conditions)) or 0


def _recent_activity(db: Session, limit: int) -> list[Activity]:
    options = (
        joinedload(Loan.copy).joinedload(BookCopy.book),
        joinedload(Loan.member).joinedload(Member.user),
    )
    issued = db.scalars(
        select(Loan).options(*options).order_by(Loan.loan_date.desc(), Loan.id.desc()).limit(limit)
    ).all()
    returned = db.scalars(
        select(Loan)
        .options(*options)
        .where(Loan.return_date.is_not(None))
        .order_by(Loan.return_date.desc(), Loan.id.desc())
        .limit(limit)
    ).all()

    def activity(loan: Loan, kind: str, day: date) -> Activity:
        return Activity(
            kind=kind,
            day=day,
            loan_id=loan.id,
            book_title=loan.copy.book.title,
            member_name=loan.member.user.full_name,
            member_no=loan.member.member_no,
        )

    events = [activity(loan, "loan", loan.loan_date) for loan in issued]
    events += [activity(loan, "return", loan.return_date) for loan in returned]
    events.sort(key=lambda e: (e.day, e.kind == "return", e.loan_id), reverse=True)
    return events[:limit]


def dashboard(db: Session, today: date | None = None, recent_limit: int = 10) -> Dashboard:
    today = today or date.today()
    unpaid = db.scalar(
        select(func.coalesce(func.sum(Fine.amount), 0)).where(Fine.status == FineStatus.UNPAID)
    )
    return Dashboard(
        total_books=_count(db, Book.id),
        total_copies=_count(db, BookCopy.id),
        available_copies=_count(db, BookCopy.id, BookCopy.status == CopyStatus.AVAILABLE),
        active_members=_count(db, Member.id, Member.status == MemberStatus.ACTIVE),
        open_loans=_count(db, Loan.id, Loan.status.in_(OPEN_LOAN_STATUSES)),
        overdue_loans=_count(db, Loan.id, is_overdue(today)),
        loans_today=_count(db, Loan.id, Loan.loan_date == today),
        returns_today=_count(db, Loan.id, Loan.return_date == today),
        unpaid_fine_total=Decimal(unpaid).quantize(Decimal("0.01")),
        recent_activity=_recent_activity(db, recent_limit),
    )


# --- Raporlar ---


@dataclass(frozen=True)
class PopularBook:
    book_id: int
    title: str
    authors: str
    loan_count: int


def popular_books(db: Session, period: DateRange, limit: int) -> list[PopularBook]:
    loan_count = func.count(Loan.id).label("loan_count")
    rows = db.execute(
        select(Book, loan_count)
        .join(BookCopy, BookCopy.book_id == Book.id)
        .join(Loan, Loan.copy_id == BookCopy.id)
        .where(*period.apply(Loan.loan_date))
        .group_by(Book.id)
        .order_by(loan_count.desc(), Book.title)
        .limit(limit)
    ).all()
    return [
        PopularBook(
            book_id=book.id,
            title=book.title,
            authors=", ".join(a.full_name for a in book.authors),
            loan_count=count,
        )
        for book, count in rows
    ]


@dataclass(frozen=True)
class OverdueItem:
    loan_id: int
    book_title: str
    barcode: str
    member_id: int
    member_no: str
    member_name: str
    phone: str | None
    due_date: date
    days_late: int
    estimated_fine: Decimal


def overdue(db: Session, today: date | None = None) -> list[OverdueItem]:
    today = today or date.today()
    daily_fine = settings_service.get_decimal(db, "daily_fine")
    loans = db.scalars(
        select(Loan)
        .options(
            joinedload(Loan.copy).joinedload(BookCopy.book),
            joinedload(Loan.member).joinedload(Member.user),
        )
        .where(is_overdue(today))
        .order_by(Loan.due_date, Loan.id)
    ).all()
    return [
        OverdueItem(
            loan_id=loan.id,
            book_title=loan.copy.book.title,
            barcode=loan.copy.barcode,
            member_id=loan.member_id,
            member_no=loan.member.member_no,
            member_name=loan.member.user.full_name,
            phone=loan.member.phone,
            due_date=loan.due_date,
            days_late=fine_service.overdue_days(loan.due_date, today),
            estimated_fine=fine_service.calculate_overdue_fine(loan.due_date, today, daily_fine),
        )
        for loan in loans
    ]


@dataclass(frozen=True)
class ActiveMember:
    member_id: int
    member_no: str
    full_name: str
    loan_count: int


def active_members(db: Session, period: DateRange, limit: int) -> list[ActiveMember]:
    loan_count = func.count(Loan.id).label("loan_count")
    rows = db.execute(
        select(Member.id, Member.member_no, User.full_name, loan_count)
        .join(User, User.id == Member.user_id)
        .join(Loan, Loan.member_id == Member.id)
        .where(*period.apply(Loan.loan_date))
        .group_by(Member.id, Member.member_no, User.full_name)
        .order_by(loan_count.desc(), Member.member_no)
        .limit(limit)
    ).all()
    return [ActiveMember(*row) for row in rows]


@dataclass(frozen=True)
class CategoryStat:
    category_id: int
    name: str
    book_count: int
    copy_count: int
    loan_count: int


def category_stats(db: Session, period: DateRange) -> list[CategoryStat]:
    books = (
        select(func.count(book_categories.c.book_id))
        .where(book_categories.c.category_id == Category.id)
        .correlate(Category)
        .scalar_subquery()
    )
    copies = (
        select(func.count(BookCopy.id))
        .join(book_categories, book_categories.c.book_id == BookCopy.book_id)
        .where(book_categories.c.category_id == Category.id)
        .correlate(Category)
        .scalar_subquery()
    )
    loans = (
        select(func.count(Loan.id))
        .join(BookCopy, BookCopy.id == Loan.copy_id)
        .join(book_categories, book_categories.c.book_id == BookCopy.book_id)
        .where(book_categories.c.category_id == Category.id, *period.apply(Loan.loan_date))
        .correlate(Category)
        .scalar_subquery()
    )
    rows = db.execute(
        select(Category.id, Category.name, books, copies, loans).order_by(Category.name)
    ).all()
    return [CategoryStat(*row) for row in rows]

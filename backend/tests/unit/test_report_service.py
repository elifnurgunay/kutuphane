from datetime import timedelta
from decimal import Decimal

import pytest

from app.models import Category
from app.services import report_service as svc
from tests.factories import TODAY, World


@pytest.fixture
def w(db):
    return World(db)


@pytest.fixture
def history(w, db):
    """3 kitap: A 3 kez, B 1 kez ödünç alındı; C hiç; bir ödünç gecikmiş."""
    roman, siir = Category(name="Roman"), Category(name="Şiir")
    db.add_all([roman, siir])
    [a] = w.book()
    [b] = w.book()
    [c] = w.book()
    a.book.categories = [roman]
    b.book.categories = [roman]
    c.book.categories = [siir]
    db.commit()

    ayse, ali = w.member(), w.member()
    for days_ago in (60, 40):
        loan = w.issue(ayse, a, today=TODAY - timedelta(days=days_ago))
        w.return_(loan, today=TODAY - timedelta(days=days_ago - 5))
    w.issue(ali, a, today=TODAY - timedelta(days=20))  # 5 gün gecikmiş, açık
    loan = w.issue(ayse, b, today=TODAY)
    w.return_(loan, today=TODAY)
    return {"a": a, "b": b, "c": c, "ayse": ayse, "ali": ali, "roman": roman, "siir": siir}


def test_dashboard(db, history):
    d = svc.dashboard(db, today=TODAY)
    assert (d.total_books, d.total_copies, d.available_copies) == (3, 3, 2)
    assert (d.open_loans, d.overdue_loans) == (1, 1)
    assert (d.loans_today, d.returns_today) == (1, 1)
    assert d.active_members == 2
    assert d.unpaid_fine_total == Decimal("0.00")
    assert d.recent_activity[0].kind == "return"
    assert d.recent_activity[0].day == TODAY


def test_popular_books_with_period(db, history):
    all_time = svc.popular_books(db, svc.DateRange(), limit=10)
    assert [(p.title, p.loan_count) for p in all_time] == [("Kitap 1", 3), ("Kitap 2", 1)]

    recent = svc.popular_books(db, svc.DateRange(start=TODAY - timedelta(days=30)), limit=10)
    assert [(p.title, p.loan_count) for p in recent] == [("Kitap 1", 1), ("Kitap 2", 1)]

    assert len(svc.popular_books(db, svc.DateRange(), limit=1)) == 1


def test_overdue_report(db, history):
    [item] = svc.overdue(db, today=TODAY)
    assert item.member_no == history["ali"].member_no
    assert item.days_late == 5
    assert item.estimated_fine == Decimal("10.00")


def test_active_members(db, history):
    rows = svc.active_members(db, svc.DateRange(), limit=10)
    assert [(r.member_no, r.loan_count) for r in rows] == [
        (history["ayse"].member_no, 3),
        (history["ali"].member_no, 1),
    ]


def test_category_stats(db, history):
    stats = {
        s.name: (s.book_count, s.copy_count, s.loan_count)
        for s in svc.category_stats(db, svc.DateRange())
    }
    assert stats == {"Roman": (2, 2, 4), "Şiir": (1, 1, 0)}

    period = svc.DateRange(start=TODAY - timedelta(days=30), end=TODAY - timedelta(days=1))
    stats = {s.name: s.loan_count for s in svc.category_stats(db, period)}
    assert stats == {"Roman": 1, "Şiir": 0}

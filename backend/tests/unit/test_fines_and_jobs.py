from datetime import UTC, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.errors import AppError, ErrorCode
from app.jobs import daily
from app.jobs.scheduler import seconds_until_next_run
from app.models.enums import FineStatus, LoanStatus, MemberStatus, ReservationStatus
from app.services import fine_service, reservation_service
from tests.factories import NOW, TODAY, World


def _error_code(fn, *args, **kwargs) -> ErrorCode:
    with pytest.raises(AppError) as exc_info:
        fn(*args, **kwargs)
    return exc_info.value.code


@pytest.fixture
def w(db):
    return World(db)


@pytest.fixture
def unpaid_fine(w):
    loan = w.issue(w.member(), w.book()[0])
    result = w.return_(loan, today=loan.due_date + timedelta(days=4))
    return result.fines[0]


# --- Ceza tahsilatı / affetme ---


def test_pay_fine(w, unpaid_fine):
    fine = fine_service.pay_fine(w.db, unpaid_fine.id, w.staff, now=NOW)
    assert fine.status == FineStatus.PAID
    assert fine.collected_by == w.staff.id
    assert fine.paid_at is not None


def test_waive_fine(w, unpaid_fine):
    fine = fine_service.waive_fine(w.db, unpaid_fine.id, w.staff, now=NOW)
    assert fine.status == FineStatus.WAIVED


def test_closed_fine_cannot_be_paid_again(w, unpaid_fine):
    fine_service.pay_fine(w.db, unpaid_fine.id, w.staff)
    assert _error_code(fine_service.pay_fine, w.db, unpaid_fine.id, w.staff) == (
        ErrorCode.FINE_NOT_UNPAID
    )
    assert _error_code(fine_service.waive_fine, w.db, unpaid_fine.id, w.staff) == (
        ErrorCode.FINE_NOT_UNPAID
    )


def test_unknown_fine(w):
    assert _error_code(fine_service.pay_fine, w.db, 999, w.staff) == ErrorCode.NOT_FOUND


def test_paying_fine_unblocks_member(w, db):
    member = w.member()
    loan = w.issue(member, w.book()[0])
    w.set("daily_fine", "20.00")
    [fine] = w.return_(loan, today=loan.due_date + timedelta(days=3)).fines  # 60 TL
    assert _error_code(w.issue, member, w.book()[0]) == ErrorCode.UNPAID_FINES

    fine_service.pay_fine(db, fine.id, w.staff)
    assert w.issue(member, w.book()[0]).status == LoanStatus.ACTIVE


def test_search_fines(w, unpaid_fine):
    items, total, amount = fine_service.search_fines(w.db, FineStatus.UNPAID, None, 1, 10)
    assert total == 1
    assert amount == Decimal("8.00")
    assert items[0].loan.copy.book.title.startswith("Kitap")

    _, total, amount = fine_service.search_fines(w.db, FineStatus.PAID, None, 1, 10)
    assert (total, amount) == (0, Decimal("0.00"))


# --- Günlük görev ---


def test_daily_job(w, db):
    on_time = w.issue(w.member(), w.book()[0], today=TODAY - timedelta(days=5))
    late = w.issue(w.member(), w.book()[0], today=TODAY - timedelta(days=20))
    expiring = w.member(membership_end=TODAY - timedelta(days=1))
    suspended = w.member(status=MemberStatus.SUSPENDED, membership_end=TODAY - timedelta(days=1))

    [copy] = w.book()
    held = w.issue(w.member(), copy, today=TODAY - timedelta(days=10))
    waiting = reservation_service.create_reservation(
        db, copy.book_id, w.member().id, today=TODAY, now=NOW - timedelta(days=5)
    )
    w.return_(held, today=TODAY - timedelta(days=5))  # rezervasyon 5 gün önce hazır oldu
    db.refresh(waiting)
    waiting.ready_at = NOW - timedelta(days=5)
    waiting.expires_at = NOW - timedelta(days=2)
    db.commit()

    result = daily.run(db, today=TODAY, now=NOW)
    assert result == daily.DailyResult(
        overdue_loans=1, expired_reservations=1, expired_memberships=1
    )
    assert late.status == LoanStatus.OVERDUE
    assert on_time.status == LoanStatus.ACTIVE
    assert expiring.status == MemberStatus.EXPIRED
    assert suspended.status == MemberStatus.SUSPENDED
    assert waiting.status == ReservationStatus.EXPIRED

    # tekrar çalıştırmak bir şey değiştirmez
    assert daily.run(db, today=TODAY, now=NOW) == daily.DailyResult(0, 0, 0)


def test_overdue_loan_return_still_fined(w, db):
    loan = w.issue(w.member(), w.book()[0], today=TODAY - timedelta(days=20))
    daily.run(db, today=TODAY, now=NOW)

    result = w.return_(loan, today=TODAY)
    assert loan.status == LoanStatus.RETURNED
    assert result.fines[0].amount == Decimal("10.00")


@pytest.mark.parametrize(
    ("now", "expected_hours"),
    [
        (datetime(2026, 10, 17, 0, 0, tzinfo=UTC), 5 / 60),
        (datetime(2026, 10, 17, 0, 5, tzinfo=UTC), 24),
        (datetime(2026, 10, 17, 12, 5, tzinfo=timezone(timedelta(hours=3))), 12),
    ],
)
def test_seconds_until_next_run(now, expected_hours):
    assert seconds_until_next_run(now, time(0, 5)) == pytest.approx(expected_hours * 3600)


def test_daily_main_runs(monkeypatch, db, capsys):
    monkeypatch.setattr(daily, "SessionLocal", lambda: _NoCloseSession(db))
    daily.main()
    assert "Günlük görev" in capsys.readouterr().out


class _NoCloseSession:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, *exc):
        return False

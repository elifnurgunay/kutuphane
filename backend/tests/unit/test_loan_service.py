from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.errors import AppError, ErrorCode
from app.models import Fine, Loan, Member
from app.models.enums import (
    CopyStatus,
    FineReason,
    FineStatus,
    LoanStatus,
    MemberStatus,
    MemberType,
    ReservationStatus,
)
from app.services import fine_service
from app.services import loan_service as svc
from tests.factories import NOW, TODAY, World


def _error_code(fn, *args, **kwargs) -> ErrorCode:
    with pytest.raises(AppError) as exc_info:
        fn(*args, **kwargs)
    return exc_info.value.code


@pytest.fixture
def w(db):
    return World(db)


# --- fine_service ---


@pytest.mark.parametrize(
    ("due", "returned", "expected"),
    [
        (date(2026, 10, 10), date(2026, 10, 15), Decimal("10.00")),  # PLAN 10.2: 5 gün → 10 TL
        (date(2026, 10, 10), date(2026, 10, 10), Decimal("0.00")),
        (date(2026, 10, 10), date(2026, 10, 1), Decimal("0.00")),
    ],
)
def test_calculate_overdue_fine(due, returned, expected):
    assert fine_service.calculate_overdue_fine(due, returned, Decimal("2.00")) == expected


# --- Ödünç verme ---


def test_issue_loan_sets_due_date_and_copy_status(w):
    member = w.member()
    [copy] = w.book()

    loan = w.issue(member, copy)
    assert loan.loan_date == TODAY
    assert loan.due_date == TODAY + timedelta(days=15)
    assert loan.issued_by == w.staff.id
    assert copy.status == CopyStatus.LOANED


def test_loan_days_come_from_settings(w):
    w.set("loan_days", "7")
    loan = w.issue(w.member(), w.book()[0])
    assert loan.due_date == TODAY + timedelta(days=7)


def test_student_loan_limit(w):
    """PLAN 10.1: öğrenci 3 kitap alır, 4.'sünde LOAN_LIMIT_EXCEEDED."""
    member = w.member(MemberType.STUDENT)
    for _ in range(3):
        w.issue(member, w.book()[0])

    code = _error_code(w.issue, member, w.book()[0])
    assert code == ErrorCode.LOAN_LIMIT_EXCEEDED


@pytest.mark.parametrize(("member_type", "limit"), [(MemberType.STAFF, 5), (MemberType.PUBLIC, 2)])
def test_loan_limit_by_member_type(w, member_type, limit):
    member = w.member(member_type)
    for _ in range(limit):
        w.issue(member, w.book()[0])
    assert _error_code(w.issue, member, w.book()[0]) == ErrorCode.LOAN_LIMIT_EXCEEDED


def test_member_with_unpaid_fines_cannot_borrow(w, db):
    """PLAN 10.3: 60 TL ödenmemiş cezası olan üye kitap alamaz."""
    member = w.member()
    [copy] = w.book(copies=2)[:1]
    loan = w.issue(member, copy)
    w.return_(loan)
    db.add(Fine(loan_id=loan.id, member_id=member.id, amount=Decimal("60"), reason=FineReason.LOST))
    db.commit()

    assert _error_code(w.issue, member, w.book()[0]) == ErrorCode.UNPAID_FINES


def test_paid_fines_do_not_block(w, db):
    member = w.member()
    [copy] = w.book()
    loan = w.issue(member, copy)
    w.return_(loan)
    db.add(
        Fine(
            loan_id=loan.id,
            member_id=member.id,
            amount=Decimal("60"),
            reason=FineReason.LOST,
            status=FineStatus.PAID,
        )
    )
    db.commit()

    assert w.issue(member, w.book()[0]).status == LoanStatus.ACTIVE


def test_member_with_overdue_loan_cannot_borrow(w):
    member = w.member()
    w.issue(member, w.book()[0], today=TODAY - timedelta(days=20))  # vadesi 5 gün önce geçti

    assert _error_code(w.issue, member, w.book()[0]) == ErrorCode.HAS_OVERDUE


@pytest.mark.parametrize(
    "overrides",
    [{"status": MemberStatus.SUSPENDED}, {"membership_end": TODAY - timedelta(days=1)}],
)
def test_inactive_member_cannot_borrow(w, overrides):
    member = w.member(**overrides)
    assert _error_code(w.issue, member, w.book()[0]) == ErrorCode.MEMBER_INACTIVE


@pytest.mark.parametrize(
    "status", [CopyStatus.LOANED, CopyStatus.LOST, CopyStatus.DAMAGED, CopyStatus.MAINTENANCE]
)
def test_unavailable_copy_cannot_be_issued(w, db, status):
    [copy] = w.book()
    copy.status = status
    db.commit()

    assert _error_code(w.issue, w.member(), copy) == ErrorCode.COPY_NOT_AVAILABLE


def test_unknown_barcode_and_member(w):
    member = w.member()
    assert (
        _error_code(svc.issue_loan, w.db, member.id, "KTP-9999-99", w.staff, today=TODAY)
        == ErrorCode.NOT_FOUND
    )
    assert _error_code(w.issue, Member(id=999), w.book()[0]) == ErrorCode.NOT_FOUND


def test_failed_issue_changes_nothing(w, db):
    member = w.member(status=MemberStatus.SUSPENDED)
    [copy] = w.book()
    _error_code(w.issue, member, copy)

    assert db.query(Loan).count() == 0
    assert copy.status == CopyStatus.AVAILABLE


# --- İade ---


def test_return_on_time(w):
    member = w.member()
    [copy] = w.book()
    loan = w.issue(member, copy)

    result = w.return_(loan, today=TODAY + timedelta(days=3))
    assert loan.status == LoanStatus.RETURNED
    assert loan.return_date == TODAY + timedelta(days=3)
    assert loan.returned_to == w.staff.id
    assert result.fines == []
    assert copy.status == CopyStatus.AVAILABLE


def test_late_return_creates_fine(w):
    """PLAN 10.2: 5 gün geciken iade → 10 TL ceza."""
    loan = w.issue(w.member(), w.book()[0])

    result = w.return_(loan, today=loan.due_date + timedelta(days=5))
    [fine] = result.fines
    assert fine.amount == Decimal("10.00")
    assert fine.reason == FineReason.OVERDUE
    assert fine.status == FineStatus.UNPAID


def test_daily_fine_change_applies_to_new_returns(w):
    """PLAN 10.10: daily_fine değişince yeni iadelerde yeni tutar kullanılır."""
    loan = w.issue(w.member(), w.book()[0])
    w.set("daily_fine", "3.50")

    result = w.return_(loan, today=loan.due_date + timedelta(days=2))
    assert result.fines[0].amount == Decimal("7.00")


def test_damaged_return(w):
    [copy] = w.book()
    loan = w.issue(w.member(), copy)

    result = w.return_(loan, damaged=True, damage_fine=Decimal("40"), notes="Sayfalar yırtık")
    assert copy.status == CopyStatus.DAMAGED
    assert copy.notes == "Sayfalar yırtık"
    assert [(f.reason, f.amount) for f in result.fines] == [(FineReason.DAMAGED, Decimal("40.00"))]


def test_return_twice_is_rejected(w):
    loan = w.issue(w.member(), w.book()[0])
    w.return_(loan)
    assert _error_code(w.return_, loan) == ErrorCode.LOAN_NOT_ACTIVE


def test_reservation_queue_flow(w, db):
    """PLAN 10.4: tek nüshalı kitap ödünçteyken A ve B sırayla rezerve eder;
    iade edilince A ready olur, nüsha reserved; B alamaz, A alabilir."""
    holder, a, b = w.member(), w.member(), w.member()
    [copy] = w.book()
    loan = w.issue(holder, copy)
    res_a = w.reserve(a, copy, minutes=0)
    res_b = w.reserve(b, copy, minutes=5)

    result = w.return_(loan)
    assert result.reservation.id == res_a.id
    assert res_a.status == ReservationStatus.READY
    assert res_a.assigned_copy_id == copy.id
    assert res_a.expires_at == (NOW + timedelta(days=3)).replace(tzinfo=res_a.expires_at.tzinfo)
    assert res_b.status == ReservationStatus.WAITING
    assert copy.status == CopyStatus.RESERVED

    assert _error_code(w.issue, b, copy) == ErrorCode.COPY_NOT_AVAILABLE
    w.issue(a, copy)
    assert res_a.status == ReservationStatus.FULFILLED
    assert copy.status == CopyStatus.LOANED


# --- Süre uzatma ---


def test_renew(w):
    loan = w.issue(w.member(), w.book()[0])
    renewed = svc.renew_loan(w.db, loan.id, today=TODAY + timedelta(days=10))

    assert renewed.due_date == TODAY + timedelta(days=25)
    assert renewed.renew_count == 1


def test_renew_limit(w):
    loan = w.issue(w.member(), w.book()[0])
    svc.renew_loan(w.db, loan.id, today=TODAY)
    assert _error_code(svc.renew_loan, w.db, loan.id, today=TODAY) == ErrorCode.RENEW_LIMIT


def test_renew_rejected_when_book_reserved(w):
    """PLAN 10.6: rezervasyonu olan kitap için süre uzatma reddedilir."""
    [copy] = w.book()
    loan = w.issue(w.member(), copy)
    w.reserve(w.member(), copy)

    code = _error_code(svc.renew_loan, w.db, loan.id, today=TODAY)
    assert code == ErrorCode.RESERVATION_PENDING


def test_overdue_loan_cannot_be_renewed(w):
    loan = w.issue(w.member(), w.book()[0])
    code = _error_code(svc.renew_loan, w.db, loan.id, today=loan.due_date + timedelta(days=1))
    assert code == ErrorCode.LOAN_OVERDUE


# --- Kayıp ---


def test_mark_lost(w):
    [copy] = w.book()
    loan = w.issue(w.member(), copy)

    loan, fine = svc.mark_lost(w.db, loan.id)
    assert loan.status == LoanStatus.LOST
    assert copy.status == CopyStatus.LOST
    assert (fine.reason, fine.amount) == (FineReason.LOST, Decimal("150.00"))


def test_lost_fine_comes_from_settings(w):
    w.set("lost_book_fine", "275.50")
    loan = w.issue(w.member(), w.book()[0])
    _, fine = svc.mark_lost(w.db, loan.id)
    assert fine.amount == Decimal("275.50")


# --- Uygunluk özeti ---


def test_eligibility_lists_all_problems(w, db):
    member = w.member(MemberType.PUBLIC)
    for _ in range(2):  # 30 gün önce verildi, bugün ikisi de gecikmiş
        w.issue(member, w.book()[0], today=TODAY - timedelta(days=30))
    member.status = MemberStatus.SUSPENDED
    db.commit()

    result = svc.get_eligibility(db, member.id, today=TODAY)
    assert not result.can_borrow
    assert [p.code for p in result.problems] == [
        ErrorCode.MEMBER_INACTIVE,
        ErrorCode.LOAN_LIMIT_EXCEEDED,
        ErrorCode.HAS_OVERDUE,
    ]
    assert (result.active_loan_count, result.loan_limit, result.overdue_count) == (2, 2, 2)

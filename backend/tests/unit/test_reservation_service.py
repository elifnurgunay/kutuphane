from datetime import timedelta

import pytest

from app.core.errors import AppError, ErrorCode
from app.models.enums import CopyStatus, MemberStatus, ReservationStatus
from app.services import reservation_service as svc
from tests.factories import NOW, TODAY, World


def _error_code(fn, *args, **kwargs) -> ErrorCode:
    with pytest.raises(AppError) as exc_info:
        fn(*args, **kwargs)
    return exc_info.value.code


@pytest.fixture
def w(db):
    return World(db)


def _reserve(w, member, copy, minutes=0):
    return svc.create_reservation(
        w.db, copy.book_id, member.id, today=TODAY, now=NOW + timedelta(minutes=minutes)
    )


def test_create_reservation_when_no_copy_available(w):
    [copy] = w.book()
    w.issue(w.member(), copy)

    reservation = _reserve(w, w.member(), copy)
    assert reservation.status == ReservationStatus.WAITING
    assert svc.queue_position(w.db, reservation) == 1


def test_cannot_reserve_available_book(w):
    """PLAN 10.7: müsait nüshası olan kitaba rezervasyon yapılamaz."""
    [copy] = w.book()
    code = _error_code(_reserve, w, w.member(), copy)
    assert code == ErrorCode.BOOK_AVAILABLE_NO_RESERVATION


def test_duplicate_reservation_rejected(w):
    [copy] = w.book()
    w.issue(w.member(), copy)
    member = w.member()
    _reserve(w, member, copy)

    assert _error_code(_reserve, w, member, copy) == ErrorCode.RESERVATION_EXISTS


def test_borrower_cannot_reserve_same_book(w):
    [copy] = w.book()
    member = w.member()
    w.issue(member, copy)

    assert _error_code(_reserve, w, member, copy) == ErrorCode.ALREADY_BORROWED


def test_inactive_member_cannot_reserve(w):
    [copy] = w.book()
    w.issue(w.member(), copy)
    member = w.member(status=MemberStatus.SUSPENDED)

    assert _error_code(_reserve, w, member, copy) == ErrorCode.MEMBER_INACTIVE


def test_queue_positions(w):
    [copy] = w.book()
    w.issue(w.member(), copy)
    first = _reserve(w, w.member(), copy, minutes=0)
    second = _reserve(w, w.member(), copy, minutes=1)
    third = _reserve(w, w.member(), copy, minutes=2)

    svc.cancel_reservation(w.db, second.id, now=NOW)
    assert svc.queue_position(w.db, first) == 1
    assert svc.queue_position(w.db, third) == 2
    assert svc.queue_position(w.db, second) is None


def test_cancel_ready_reservation_passes_copy_to_next(w):
    [copy] = w.book()
    loan = w.issue(w.member(), copy)
    a = _reserve(w, w.member(), copy, minutes=0)
    b = _reserve(w, w.member(), copy, minutes=1)
    w.return_(loan)
    assert a.status == ReservationStatus.READY

    svc.cancel_reservation(w.db, a.id, now=NOW)
    assert a.status == ReservationStatus.CANCELLED
    assert b.status == ReservationStatus.READY
    assert b.assigned_copy_id == copy.id
    assert copy.status == CopyStatus.RESERVED


def test_cancel_last_ready_reservation_frees_copy(w):
    [copy] = w.book()
    loan = w.issue(w.member(), copy)
    a = _reserve(w, w.member(), copy)
    w.return_(loan)

    svc.cancel_reservation(w.db, a.id, now=NOW)
    assert copy.status == CopyStatus.AVAILABLE
    assert _error_code(svc.cancel_reservation, w.db, a.id) == ErrorCode.RESERVATION_NOT_ACTIVE


def test_expired_ready_reservation_moves_to_next(w):
    """PLAN 10.5: A 3 gün içinde almazsa rezervasyonu expired, B ready olur."""
    [copy] = w.book()
    loan = w.issue(w.member(), copy)
    a = _reserve(w, w.member(), copy, minutes=0)
    b = _reserve(w, w.member(), copy, minutes=1)
    w.return_(loan)

    assert svc.expire_ready_reservations(w.db, now=NOW + timedelta(days=2)) == 0
    assert a.status == ReservationStatus.READY

    later = NOW + timedelta(days=3, minutes=1)
    assert svc.expire_ready_reservations(w.db, now=later) == 1
    assert a.status == ReservationStatus.EXPIRED
    assert b.status == ReservationStatus.READY
    assert copy.status == CopyStatus.RESERVED

    # B de almazsa nüsha rafa döner
    svc.expire_ready_reservations(w.db, now=later + timedelta(days=4))
    assert b.status == ReservationStatus.EXPIRED
    assert copy.status == CopyStatus.AVAILABLE


def test_search_reservations(w):
    [copy] = w.book()
    w.issue(w.member(), copy)
    member = w.member()
    _reserve(w, member, copy)

    items, total = svc.search_reservations(w.db, copy.book_id, None, None, 1, 10)
    assert total == 1
    assert items[0].member.id == member.id
    items, total = svc.search_reservations(w.db, None, None, ReservationStatus.READY, 1, 10)
    assert total == 0


def test_member_can_only_cancel_own_reservation(w):
    [copy] = w.book()
    w.issue(w.member(), copy)
    owner, other = w.member(), w.member()
    reservation = _reserve(w, owner, copy)

    code = _error_code(svc.cancel_reservation, w.db, reservation.id, member_id=other.id)
    assert code == ErrorCode.FORBIDDEN
    svc.cancel_reservation(w.db, reservation.id, member_id=owner.id)
    assert reservation.status == ReservationStatus.CANCELLED

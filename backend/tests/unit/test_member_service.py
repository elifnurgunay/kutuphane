from datetime import date
from decimal import Decimal

import pytest

from app.core.errors import AppError, ErrorCode
from app.core.security import verify_password
from app.models import Book, BookCopy, Fine, Loan, Reservation
from app.models.enums import (
    FineReason,
    FineStatus,
    LoanStatus,
    MemberStatus,
    MemberType,
    UserRole,
)
from app.schemas.member import MemberCreate, MemberUpdate
from app.services import member_service as svc


def _error_code(fn, *args, **kwargs) -> ErrorCode:
    with pytest.raises(AppError) as exc_info:
        fn(*args, **kwargs)
    return exc_info.value.code


def _create_in(**overrides) -> MemberCreate:
    data = {
        "email": "Ayse@Ornek.com",
        "full_name": "Ayşe Yılmaz",
        "password": "Parola123!",
        "phone": "0532 000 00 00",
        "member_type": MemberType.STUDENT,
        "membership_start": date(2026, 1, 1),
        "membership_end": date(2027, 1, 1),
    }
    return MemberCreate(**(data | overrides))


def _update_in(member, **overrides) -> MemberUpdate:
    data = {
        "email": member.user.email,
        "full_name": member.user.full_name,
        "phone": member.phone,
        "address": member.address,
        "member_type": member.member_type,
        "membership_start": member.membership_start,
        "membership_end": member.membership_end,
    }
    return MemberUpdate(**(data | overrides))


def test_create_member_creates_user_and_member_no(db):
    member = svc.create_member(db, _create_in())

    assert member.member_no == "UYE-000001"
    assert member.status == MemberStatus.ACTIVE
    assert member.user.role == UserRole.MEMBER
    assert member.user.email == "ayse@ornek.com"
    assert verify_password("Parola123!", member.user.password_hash)


def test_member_numbers_continue_from_highest(db):
    first = svc.create_member(db, _create_in())
    first.member_no = "UYE-000041"
    db.commit()

    second = svc.create_member(db, _create_in(email="ali@ornek.com"))
    assert second.member_no == "UYE-000042"


def test_create_member_rejects_duplicate_email(db, make_user):
    make_user(email="ayse@ornek.com")
    assert _error_code(svc.create_member, db, _create_in()) == ErrorCode.EMAIL_EXISTS


def test_create_member_rejects_end_before_start(db):
    code = _error_code(svc.create_member, db, _create_in(membership_end=date(2025, 12, 31)))
    assert code == ErrorCode.INVALID_DATE_RANGE


def test_update_member(db):
    member = svc.create_member(db, _create_in())
    other = svc.create_member(db, _create_in(email="ali@ornek.com"))

    updated = svc.update_member(
        db, member.id, _update_in(member, full_name="Ayşe Kaya", member_type=MemberType.STAFF)
    )
    assert updated.user.full_name == "Ayşe Kaya"
    assert updated.member_type == MemberType.STAFF

    code = _error_code(svc.update_member, db, member.id, _update_in(member, email=other.user.email))
    assert code == ErrorCode.EMAIL_EXISTS


def test_suspend_and_activate(db):
    member = svc.create_member(db, _create_in())

    assert svc.suspend_member(db, member.id).status == MemberStatus.SUSPENDED
    assert svc.activate_member(db, member.id, today=date(2026, 6, 1)).status == (
        MemberStatus.ACTIVE
    )


def test_cannot_activate_expired_membership(db):
    member = svc.create_member(db, _create_in())
    svc.suspend_member(db, member.id)

    code = _error_code(svc.activate_member, db, member.id, today=date(2027, 1, 2))
    assert code == ErrorCode.MEMBERSHIP_EXPIRED


def test_get_unknown_member(db):
    assert _error_code(svc.get_member, db, 999) == ErrorCode.NOT_FOUND


@pytest.fixture
def member_with_history(db, make_user):
    member = svc.create_member(db, _create_in())
    staff = make_user(UserRole.LIBRARIAN)
    book = Book(title="Suç ve Ceza")
    copies = [BookCopy(book=book, barcode=f"KTP-0001-0{i}") for i in (1, 2)]
    db.add_all([book, *copies])
    db.flush()
    returned = Loan(
        copy_id=copies[0].id,
        member_id=member.id,
        issued_by=staff.id,
        loan_date=date(2026, 9, 1),
        due_date=date(2026, 9, 16),
        return_date=date(2026, 9, 20),
        status=LoanStatus.RETURNED,
    )
    active = Loan(
        copy_id=copies[1].id,
        member_id=member.id,
        issued_by=staff.id,
        loan_date=date(2026, 10, 10),
        due_date=date(2026, 10, 25),
    )
    db.add_all([returned, active])
    db.flush()
    db.add_all(
        [
            Fine(
                loan_id=returned.id,
                member_id=member.id,
                amount=Decimal("8.00"),
                reason=FineReason.OVERDUE,
            ),
            Fine(
                loan_id=returned.id,
                member_id=member.id,
                amount=Decimal("5.00"),
                reason=FineReason.DAMAGED,
                status=FineStatus.PAID,
            ),
            Reservation(book_id=book.id, member_id=member.id),
        ]
    )
    db.commit()
    return member


def test_member_row_counts_and_fine_total(db, member_with_history):
    row = svc.get_member_row(db, member_with_history.id)
    assert row.active_loan_count == 1
    assert svc.unpaid_fine_total(db, member_with_history.id) == Decimal("8.00")


def test_member_history_lists(db, member_with_history):
    loans = svc.member_loans(db, member_with_history.id)
    assert [loan.loan_date for loan in loans] == [date(2026, 10, 10), date(2026, 9, 1)]
    assert loans[0].copy.book.title == "Suç ve Ceza"

    active = svc.member_loans(db, member_with_history.id, LoanStatus.ACTIVE)
    assert len(active) == 1

    assert len(svc.member_fines(db, member_with_history.id)) == 2
    assert svc.member_reservations(db, member_with_history.id)[0].book.title == "Suç ve Ceza"


def test_search_members(db):
    svc.create_member(db, _create_in())
    ali = svc.create_member(db, _create_in(email="ali@ornek.com", full_name="Ali Çelik"))
    svc.suspend_member(db, ali.id)

    def names(**kwargs):
        rows, _ = svc.search_members(db, page=1, size=10, **kwargs)
        return [row.member.user.full_name for row in rows]

    assert names(q="ali", status=None) == ["Ali Çelik"]
    assert names(q="UYE-000001", status=None) == ["Ayşe Yılmaz"]
    assert names(q=None, status=MemberStatus.SUSPENDED) == ["Ali Çelik"]
    assert names(q=None, status=None) == ["Ayşe Yılmaz", "Ali Çelik"]

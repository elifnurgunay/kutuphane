from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core import audit
from app.core.errors import AppError, ErrorCode
from app.core.security import verify_password
from app.jobs import daily
from app.models import AuditLog, Book
from app.models.enums import UserRole
from app.schemas.staff import StaffCreate, StaffUpdate
from app.services import audit_service, settings_service, staff_service
from tests.factories import NOW, TODAY, World


def _error(fn, *args, **kwargs) -> AppError:
    with pytest.raises(AppError) as exc_info:
        fn(*args, **kwargs)
    return exc_info.value


# --- Ayarlar ---


def test_update_settings_normalizes_values(db):
    result = settings_service.update_settings(db, {"daily_fine": "3,5", "loan_days": " 21 "})
    assert result["daily_fine"] == "3.50"
    assert result["loan_days"] == "21"
    assert settings_service.get_decimal(db, "daily_fine") == Decimal("3.50")


@pytest.mark.parametrize(
    "values",
    [{"bilinmeyen": "1"}, {"loan_days": "0"}, {"loan_days": "1.5"}, {"daily_fine": "abc"}],
)
def test_update_settings_rejects_invalid(db, values):
    assert _error(settings_service.update_settings, db, values).code == ErrorCode.VALIDATION_ERROR


def test_invalid_setting_saves_nothing(db):
    _error(settings_service.update_settings, db, {"daily_fine": "5", "loan_days": "-1"})
    assert settings_service.get_value(db, "daily_fine") == "2.00"


# --- Personel ---


def _create(db, **overrides):
    data = {"email": "Yeni@Kutuphane.local", "full_name": "Yeni Görevli", "role": "librarian"}
    return staff_service.create_staff(db, StaffCreate(password="Parola123!", **(data | overrides)))


def _update(user, **overrides):
    data = {
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
    }
    return StaffUpdate(**(data | overrides))


def test_create_and_list_staff(db, make_user):
    make_user(UserRole.MEMBER)
    user = _create(db)
    assert user.email == "yeni@kutuphane.local"
    assert verify_password("Parola123!", user.password_hash)
    assert [u.id for u in staff_service.list_staff(db)] == [user.id]


def test_staff_email_unique(db):
    _create(db)
    assert _error(_create, db).code == ErrorCode.EMAIL_EXISTS


def test_update_and_reset_password(db, make_user):
    admin = make_user(UserRole.ADMIN)
    user = _create(db)
    updated = staff_service.update_staff(db, user.id, _update(user, is_active=False), admin)
    assert updated.is_active is False

    staff_service.reset_password(db, user.id, "YeniParola9!")
    assert verify_password("YeniParola9!", user.password_hash)


def test_admin_cannot_demote_self_or_last_admin(db, make_user):
    admin = make_user(UserRole.ADMIN)
    other_admin = make_user(UserRole.ADMIN)

    code = _error(
        staff_service.update_staff, db, admin.id, _update(admin, role="librarian"), admin
    ).code
    assert code == ErrorCode.FORBIDDEN

    staff_service.update_staff(db, other_admin.id, _update(other_admin, is_active=False), admin)
    librarian = _create(db, role="admin", email="ikinci@kutuphane.local")
    staff_service.update_staff(db, librarian.id, _update(librarian, role="librarian"), admin)
    # artık tek aktif yönetici "admin"; başkası da onu düşüremez
    assert (
        _error(
            staff_service.update_staff, db, admin.id, _update(admin, is_active=False), librarian
        ).code
        == ErrorCode.FORBIDDEN
    )


def test_members_are_not_staff(db, make_user):
    member = make_user(UserRole.MEMBER)
    assert _error(staff_service.get_staff, db, member.id).code == ErrorCode.NOT_FOUND


# --- Audit log ---


def _logs(db, entity=None):
    rows, _ = audit_service.search_logs(db, entity, None, 1, 100)
    return [log for log, _name in rows]


def test_audit_records_create_update_delete(db, make_user):
    staff = make_user(UserRole.LIBRARIAN)
    audit.set_actor(db, staff.id)

    book = Book(title="Deneme")
    db.add(book)
    db.commit()
    book.title = "Deneme 2"
    db.commit()
    db.delete(book)
    db.commit()

    logs = _logs(db, "books")
    assert [log.action for log in logs] == ["delete", "update", "create"]
    assert all(log.user_id == staff.id for log in logs)
    assert logs[1].details == {"title": ["Deneme", "Deneme 2"]}
    assert logs[2].details["title"] == "Deneme"
    assert logs[0].entity_id == str(book.id)


def test_audit_masks_passwords(db, make_user):
    user = make_user(UserRole.LIBRARIAN)
    [create] = [log for log in _logs(db, "users") if log.entity_id == str(user.id)]
    assert create.details["password_hash"] == "***"


def test_audit_rolled_back_with_transaction(db):
    db.add(Book(title="Geri alınacak"))
    db.flush()
    db.rollback()
    assert db.scalars(select(AuditLog).where(AuditLog.entity == "books")).all() == []


def test_daily_job_leaves_summary(db):
    w = World(db)
    w.issue(w.member(), w.book()[0], today=TODAY - timedelta(days=20))
    daily.run(db, today=TODAY, now=NOW)

    [summary] = _logs(db, "system")
    assert summary.action == "daily_job"
    assert summary.details["overdue_loans"] == 1

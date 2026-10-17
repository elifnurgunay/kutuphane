from decimal import Decimal

import pytest

from app.core.errors import AppError, ErrorCode
from app.models import Setting
from app.services import settings_service


def test_ensure_defaults_inserts_all_keys(db):
    assert settings_service.get_all(db) == settings_service.DEFAULT_SETTINGS


def test_ensure_defaults_is_idempotent_and_keeps_changed_values(db):
    db.get(Setting, "daily_fine").value = "5.00"
    db.commit()

    assert settings_service.ensure_defaults(db) == 0
    assert settings_service.get_decimal(db, "daily_fine") == Decimal("5.00")


def test_ensure_defaults_adds_only_missing_keys(db):
    db.delete(db.get(Setting, "loan_days"))
    db.commit()

    assert settings_service.ensure_defaults(db) == 1
    assert settings_service.get_value(db, "loan_days") == "15"


def test_typed_getters(db):
    assert settings_service.get_int(db, "loan_days") == 15
    assert settings_service.get_decimal(db, "max_unpaid_fine") == Decimal("50.00")


def test_missing_setting_raises(db):
    with pytest.raises(AppError) as exc_info:
        settings_service.get_value(db, "no_such_key")
    assert exc_info.value.code == ErrorCode.SETTING_MISSING

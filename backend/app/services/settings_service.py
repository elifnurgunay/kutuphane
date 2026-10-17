from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.models import Setting

# Sistemdeki tek varsayılan değer kaynağı.
# Çalışma zamanında değerler her zaman `settings` tablosundan okunur.
DEFAULT_SETTINGS: dict[str, str] = {
    "loan_days": "15",
    "max_loans_student": "3",
    "max_loans_staff": "5",
    "max_loans_public": "2",
    "daily_fine": "2.00",
    "max_renewals": "1",
    "reservation_hold_days": "3",
    "max_unpaid_fine": "50.00",
}


def ensure_defaults(db: Session) -> int:
    """Eksik ayar anahtarlarını varsayılan değerleriyle ekler; eklenen sayısını döner."""
    existing = set(db.scalars(select(Setting.key)))
    missing = [Setting(key=k, value=v) for k, v in DEFAULT_SETTINGS.items() if k not in existing]
    db.add_all(missing)
    db.commit()
    return len(missing)


def get_all(db: Session) -> dict[str, str]:
    return {s.key: s.value for s in db.scalars(select(Setting).order_by(Setting.key))}


def get_value(db: Session, key: str) -> str:
    setting = db.get(Setting, key)
    if setting is None:
        raise AppError(ErrorCode.SETTING_MISSING, f"'{key}' ayarı tanımlı değil.", 500)
    return setting.value


def get_int(db: Session, key: str) -> int:
    return int(get_value(db, key))


def get_decimal(db: Session, key: str) -> Decimal:
    return Decimal(get_value(db, key))

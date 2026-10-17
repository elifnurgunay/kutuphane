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
    # Kayıp kitap cezası
    "lost_book_fine": "150.00",
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


# --- Ayar güncelleme (yalnız admin; yetki kontrolü uç noktadadır) ---

# Her anahtar için tip ve izin verilen en küçük değer
SETTING_RULES: dict[str, tuple[type, int]] = {
    "loan_days": (int, 1),
    "max_loans_student": (int, 0),
    "max_loans_staff": (int, 0),
    "max_loans_public": (int, 0),
    "max_renewals": (int, 0),
    "reservation_hold_days": (int, 1),
    "daily_fine": (Decimal, 0),
    "max_unpaid_fine": (Decimal, 0),
    "lost_book_fine": (Decimal, 0),
}


def _invalid(message: str) -> AppError:
    return AppError(ErrorCode.VALIDATION_ERROR, message, 400)


def _normalize(key: str, raw: str) -> str:
    if key not in SETTING_RULES:
        raise _invalid(f"Bilinmeyen ayar: {key}")
    kind, minimum = SETTING_RULES[key]
    text = str(raw).strip().replace(",", ".")
    try:
        value = int(text) if kind is int else Decimal(text)
    except (ValueError, ArithmeticError) as exc:
        raise _invalid(f"{key} için geçerli bir sayı girin.") from exc
    if isinstance(value, Decimal) and not value.is_finite():
        raise _invalid(f"{key} için geçerli bir sayı girin.")
    if value < minimum:
        raise _invalid(f"{key} en az {minimum} olmalı.")
    return str(value) if kind is int else str(value.quantize(Decimal("0.01")))


def update_settings(db: Session, values: dict[str, str]) -> dict[str, str]:
    """Birden çok ayarı doğrular ve tek işlemde kaydeder; biri hatalıysa hiçbiri kaydedilmez."""
    normalized = {key: _normalize(key, raw) for key, raw in values.items()}
    for key, value in normalized.items():
        setting = db.get(Setting, key)
        if setting is None:
            db.add(Setting(key=key, value=value))
        else:
            setting.value = value
    db.commit()
    return get_all(db)

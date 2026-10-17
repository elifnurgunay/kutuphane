"""Pydantic doğrulama hatalarını Türkçe, alan bazlı mesajlara çevirir."""

from typing import Any

FIELD_LABELS = {
    "email": "E-posta",
    "password": "Şifre",
    "current_password": "Mevcut şifre",
    "new_password": "Yeni şifre",
    "full_name": "Ad soyad",
    "phone": "Telefon",
    "address": "Adres",
    "member_type": "Üye tipi",
    "membership_start": "Üyelik başlangıcı",
    "membership_end": "Üyelik bitişi",
    "member_id": "Üye",
    "book_id": "Kitap",
    "barcode": "Barkod",
    "title": "Başlık",
    "subtitle": "Alt başlık",
    "isbn": "ISBN",
    "publisher_id": "Yayınevi",
    "publish_year": "Yayın yılı",
    "page_count": "Sayfa sayısı",
    "language": "Dil",
    "author_ids": "Yazar",
    "category_ids": "Kategori",
    "name": "Ad",
    "parent_id": "Üst kategori",
    "birth_year": "Doğum yılı",
    "shelf_location": "Raf konumu",
    "acquired_at": "Edinme tarihi",
    "status": "Durum",
    "role": "Rol",
    "damage_fine": "Hasar cezası",
    "refresh_token": "Oturum",
    "page": "Sayfa",
    "size": "Sayfa boyutu",
    "from": "Başlangıç tarihi",
    "to": "Bitiş tarihi",
}


def _label(loc: tuple[Any, ...]) -> str:
    # loc ör. ("body", "author_ids") veya ("query", "page")
    names = [
        part for part in loc if isinstance(part, str) and part not in ("body", "query", "path")
    ]
    if not names:
        return "Gönderilen veri"
    return FIELD_LABELS.get(names[-1], names[-1])


def _message(error: dict[str, Any]) -> str:
    field = _label(tuple(error.get("loc", ())))
    ctx = error.get("ctx") or {}
    kind = error.get("type", "")
    templates = {
        "missing": f"{field} zorunlu.",
        "string_too_short": f"{field} en az {ctx.get('min_length')} karakter olmalı.",
        "string_too_long": f"{field} en fazla {ctx.get('max_length')} karakter olabilir.",
        "too_short": f"{field} için en az {ctx.get('min_length')} seçim yapılmalı.",
        "too_long": f"{field} için en fazla {ctx.get('max_length')} seçim yapılabilir.",
        "greater_than_equal": f"{field} en az {ctx.get('ge')} olmalı.",
        "greater_than": f"{field} {ctx.get('gt')} değerinden büyük olmalı.",
        "less_than_equal": f"{field} en fazla {ctx.get('le')} olabilir.",
        "less_than": f"{field} {ctx.get('lt')} değerinden küçük olmalı.",
        "int_parsing": f"{field} tam sayı olmalı.",
        "int_type": f"{field} tam sayı olmalı.",
        "int_from_float": f"{field} tam sayı olmalı.",
        "decimal_parsing": f"{field} sayı olmalı.",
        "float_parsing": f"{field} sayı olmalı.",
        "decimal_type": f"{field} sayı olmalı.",
        "date_parsing": f"{field} geçerli bir tarih olmalı.",
        "date_from_datetime_parsing": f"{field} geçerli bir tarih olmalı.",
        "datetime_parsing": f"{field} geçerli bir tarih olmalı.",
        "bool_parsing": f"{field} evet/hayır olmalı.",
        "literal_error": f"{field} için geçersiz seçim.",
        "enum": f"{field} için geçersiz seçim.",
        "string_type": f"{field} metin olmalı.",
        "list_type": f"{field} liste olmalı.",
        "dict_type": f"{field} geçersiz.",
        "json_invalid": "Gönderilen veri okunamadı (geçersiz JSON).",
        "model_attributes_type": "Gönderilen veri eksik veya hatalı.",
    }
    return templates.get(kind, f"{field} geçersiz.")


def translate(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"field": _label(tuple(error.get("loc", ()))), "message": _message(error)}
        for error in errors
    ]

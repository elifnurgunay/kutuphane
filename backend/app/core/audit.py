"""Tüm yazma işlemleri için otomatik audit log.

ORM üzerinden yapılan her ekleme / güncelleme / silme, aynı veritabanı işleminin
içinde `audit_logs` tablosuna yazılır; işlem geri alınırsa kayıt da geri alınır.
İşlemi yapan kullanıcı `session.info["user_id"]` üzerinden gelir (bkz. api/deps.py).
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import event, insert, inspect
from sqlalchemy.orm import Session, attributes

from app.models import AuditLog

SKIP_TABLES = {"audit_logs"}
MASKED_COLUMNS = {"password_hash"}
# Çoka-çok ilişkilerde değişikliğin kaydedileceği taraf (karşı taraf yinelenmesin diye)
AUDITED_COLLECTIONS = {"books": ("authors", "categories")}

USER_KEY = "user_id"
DISABLED_KEY = "audit_disabled"
_PENDING_KEY = "audit_pending"


def _json(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _value(key: str, value: Any) -> Any:
    return "***" if key in MASKED_COLUMNS and value is not None else _json(value)


def _snapshot(obj: Any) -> dict[str, Any]:
    mapper = inspect(obj).mapper
    return {
        attr.key: _value(attr.key, getattr(obj, attr.key))
        for attr in mapper.column_attrs
        if getattr(obj, attr.key) is not None
    }


def _ids(items: list[Any]) -> list[Any]:
    return [inspect(item).identity[0] if inspect(item).identity else None for item in items]


def _changes(obj: Any) -> dict[str, Any]:
    state = inspect(obj)
    changes: dict[str, Any] = {}
    for attr in state.mapper.column_attrs:
        history = attributes.get_history(obj, attr.key)
        if history.added or history.deleted:
            old = history.deleted[0] if history.deleted else None
            new = history.added[0] if history.added else None
            if old != new:
                changes[attr.key] = [_value(attr.key, old), _value(attr.key, new)]
    for key in AUDITED_COLLECTIONS.get(obj.__tablename__, ()):
        history = attributes.get_history(obj, key)
        if history.added or history.deleted:
            changes[key] = {"added": _ids(history.added), "removed": _ids(history.deleted)}
    return changes


def _entity_id(obj: Any) -> str | None:
    # after_flush anında yeni nesnelerin identity'si henüz atanmamış olur; PK'yi nesneden oku
    key = inspect(obj).mapper.primary_key_from_instance(obj)
    return ",".join(str(part) for part in key) if all(p is not None for p in key) else None


@event.listens_for(Session, "before_flush")
def _collect(session: Session, _flush_context, _instances) -> None:
    if session.info.get(DISABLED_KEY):
        return
    pending = session.info.setdefault(_PENDING_KEY, [])
    for obj in session.new:
        if getattr(obj, "__tablename__", None) not in SKIP_TABLES:
            pending.append(("create", obj, None))
    for obj in session.dirty:
        if getattr(obj, "__tablename__", None) in SKIP_TABLES:
            continue
        changes = _changes(obj)
        if changes:
            pending.append(("update", obj, changes))
    for obj in session.deleted:
        if getattr(obj, "__tablename__", None) not in SKIP_TABLES:
            pending.append(("delete", obj, _snapshot(obj)))


@event.listens_for(Session, "after_flush")
def _write(session: Session, _flush_context) -> None:
    pending = session.info.pop(_PENDING_KEY, [])
    if not pending:
        return
    now = datetime.now(UTC)
    rows = [
        {
            "user_id": session.info.get(USER_KEY),
            "action": action,
            "entity": obj.__tablename__,
            "entity_id": _entity_id(obj),
            "details": _snapshot(obj) if action == "create" else details,
            "created_at": now,
        }
        for action, obj, details in pending
    ]
    session.connection().execute(insert(AuditLog), rows)


@event.listens_for(Session, "after_rollback")
def _discard(session: Session) -> None:
    session.info.pop(_PENDING_KEY, None)


def set_actor(session: Session, user_id: int | None) -> None:
    session.info[USER_KEY] = user_id


def record(session: Session, action: str, entity: str, details: dict[str, Any]) -> None:
    """ORM dışı toplu işlemler (ör. günlük görev) için elle kayıt; commit etmez."""
    session.add(
        AuditLog(
            user_id=session.info.get(USER_KEY),
            action=action,
            entity=entity,
            details={k: _json(v) for k, v in details.items()},
        )
    )

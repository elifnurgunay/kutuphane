"""İşlem kayıtlarını (audit log) listeleme — yalnız admin."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, User
from app.repositories.pagination import paginate


def search_logs(
    db: Session, entity: str | None, user_id: int | None, page: int, size: int
) -> tuple[list[tuple[AuditLog, str | None]], int]:
    stmt = select(AuditLog, User.full_name).outerjoin(User, User.id == AuditLog.user_id)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    rows, total = paginate(db, stmt.order_by(AuditLog.id.desc()), page, size)
    return [(log, name) for log, name in rows], total

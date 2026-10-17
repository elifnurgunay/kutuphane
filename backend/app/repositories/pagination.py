from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


def paginate(db: Session, stmt: Select[Any], page: int, size: int) -> tuple[list[Any], int]:
    """Sorguyu sayfalar; (satırlar, toplam kayıt sayısı) döner."""
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.limit(size).offset((page - 1) * size)).all()
    return list(rows), total

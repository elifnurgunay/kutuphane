"""books title trigram index

Revision ID: 5cc57653664a
Revises: f6d2e9a06424
Create Date: 2026-10-17 14:34:10.797264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cc57653664a'
down_revision: Union[str, Sequence[str], None] = 'f6d2e9a06424'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = "ix_books_title_trgm"  # alembic/env.py autogenerate'de yok sayar


def upgrade() -> None:
    """Başlıkta ILIKE '%...%' araması için trigram indeksi (yalnız PostgreSQL)."""
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_index(
        INDEX_NAME,
        "books",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    op.drop_index(INDEX_NAME, table_name="books")

"""lost book fine setting

Revision ID: 4500d1b51080
Revises: 5cc57653664a
Create Date: 2026-10-17 14:55:39.408233

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4500d1b51080'
down_revision: Union[str, Sequence[str], None] = '5cc57653664a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


KEY = "lost_book_fine"
DEFAULT_VALUE = "150.00"

settings_table = sa.table("settings", sa.column("key", sa.String), sa.column("value", sa.String))


def upgrade() -> None:
    """Kayıp kitap cezası varsayılanı."""
    bind = op.get_bind()
    exists = bind.execute(
        sa.select(settings_table.c.key).where(settings_table.c.key == KEY)
    ).first()
    if exists is None:
        op.bulk_insert(settings_table, [{"key": KEY, "value": DEFAULT_VALUE}])


def downgrade() -> None:
    op.execute(settings_table.delete().where(settings_table.c.key == KEY))

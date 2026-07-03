"""repuesto_destacado

Revision ID: 82cf135f0f7b
Revises: d97fe713a26a
Create Date: 2026-07-03 09:15:07.278447

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82cf135f0f7b'
down_revision: Union[str, None] = 'd97fe713a26a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "repuesto",
        sa.Column("destacado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "idx_repuesto_destacado", "repuesto", ["destacado", "universo"],
    )


def downgrade() -> None:
    op.drop_index("idx_repuesto_destacado", table_name="repuesto")
    op.drop_column("repuesto", "destacado")

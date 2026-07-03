"""repuesto_imagen_url

Revision ID: 993fb3e102f4
Revises: c044e39769da
Create Date: 2026-07-02 15:16:51.309617

Campo único imagen_url en repuesto (ADR imagen R2 — sesión migración Bajaj).
Se evaluó una tabla repuesto_imagen (galería multi-imagen) y se descartó por
simplicidad MVP: un repuesto tiene una sola foto de catálogo, ver
.doc3/adr-010-imagen-repuesto-campo-unico.md.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '993fb3e102f4'
down_revision: Union[str, None] = 'c044e39769da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("repuesto", sa.Column("imagen_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("repuesto", "imagen_url")

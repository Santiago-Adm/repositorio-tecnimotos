"""imagen_repuesto_galeria

Revision ID: d97fe713a26a
Revises: b536bf0f31a2
Create Date: 2026-07-03 00:20:00.000000

Tabla imagen_repuesto — galería multi-imagen por repuesto. Formaliza el
código huérfano existente (EP-CAT-08/09/11/12, nunca migrado) y revierte
la decisión de campo único de ADR-010. Ver .doc3/adr-012-galeria-imagenes.md.
orden=0 es la imagen principal (la que aparece en tarjetas de EP-CAT-01).
repuesto.imagen_url (ADR-010) se conserva sin cambios — coexisten.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd97fe713a26a'
down_revision: Union[str, None] = 'b536bf0f31a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "imagen_repuesto",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "repuesto_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("repuesto.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("subido_por", sa.String(100), nullable=False),
        sa.Column(
            "subido_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("repuesto_id", "orden", name="uq_imagen_repuesto_orden"),
    )
    op.create_index(
        "idx_imagen_repuesto_repuesto_id", "imagen_repuesto", ["repuesto_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_imagen_repuesto_repuesto_id", table_name="imagen_repuesto")
    op.drop_table("imagen_repuesto")

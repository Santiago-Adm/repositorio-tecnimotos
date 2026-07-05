"""ot_aceptada_en

Pieza E (sesión catálogo/UI, 2026-07-05) — registro de auditoría de cuándo
el mecánico master asignado reconoció/aceptó una OT ya creada. No reemplaza
el ciclo de `estado` (ABIERTA→...→CERRADA); una OT ya nace asignada a un
mecanico_master_id (EP-TAL-01), `aceptada_en` es independiente de eso.

Revision ID: ee34ddd8e9a1
Revises: dfa240cff40b
Create Date: 2026-07-04 23:49:18.048058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee34ddd8e9a1'
down_revision: Union[str, None] = 'dfa240cff40b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orden_trabajo", sa.Column("aceptada_en", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("orden_trabajo", "aceptada_en")

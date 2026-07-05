"""dispositivo_confiable_sesion_idle

Pieza 6-bis (sesión pulido, 2026-07-05) — reconocimiento de dispositivo
confiable (saltar MFA en el mismo dispositivo) y sesión con expiración
deslizante por rol (15 min roles estándar, 3h SUPERADMIN/ADMINISTRADOR,
en vez del TTL fijo de 7 días que existía antes).

Revision ID: 438034b83227
Revises: ee34ddd8e9a1
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '438034b83227'
down_revision: Union[str, None] = 'ee34ddd8e9a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dispositivo_confiable",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ultimo_uso", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_dispositivo_confiable_usuario", "dispositivo_confiable", ["usuario_id"])

    op.add_column(
        "sesion",
        sa.Column("idle_window_minutos", sa.Integer(), nullable=False, server_default="10080"),
    )


def downgrade() -> None:
    op.drop_column("sesion", "idle_window_minutos")
    op.drop_index("idx_dispositivo_confiable_usuario", table_name="dispositivo_confiable")
    op.drop_table("dispositivo_confiable")

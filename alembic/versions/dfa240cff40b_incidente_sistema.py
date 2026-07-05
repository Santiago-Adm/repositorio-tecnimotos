"""incidente_sistema

Revision ID: dfa240cff40b
Revises: 4186070f6f3b
Create Date: 2026-07-04 14:16:32.332906

ADR-019. FASE 0 confirmó con `grep -rln "incidente" src/ api/ alembic/versions/`
que no existe ninguna tabla de incidentes/bugs del sistema — la sesión
maestra de dashboards por rol anticipó exactamente este caso y pidió un ADR
nuevo antes de construir el widget "registro de incidentes" de SUPERADMIN.
Tabla nueva, por contexto (mismo criterio que `mfa_intento`,
`movimiento_stock`, `pedido_evento`/`orden_trabajo_evento` — nunca una
tabla genérica compartida): registro manual de incidentes operativos del
sistema (no confundir con `EstadoPedido.INCIDENCIA`, que es del dominio de
negocio de un pedido puntual).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'dfa240cff40b'
down_revision: Union[str, None] = '4186070f6f3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incidente_sistema",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("severidad", sa.String(length=20), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="ABIERTO"),
        sa.Column("reportado_por", postgresql.UUID(as_uuid=False), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("resuelto_por", postgresql.UUID(as_uuid=False), sa.ForeignKey("usuario.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resuelto_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "severidad IN ('BAJA','MEDIA','ALTA','CRITICA')", name="chk_incidente_severidad"
        ),
        sa.CheckConstraint(
            "estado IN ('ABIERTO','RESUELTO')", name="chk_incidente_estado"
        ),
    )
    op.create_index("idx_incidente_estado", "incidente_sistema", ["estado"])
    op.create_index("idx_incidente_created_at", "incidente_sistema", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_incidente_created_at", table_name="incidente_sistema")
    op.drop_index("idx_incidente_estado", table_name="incidente_sistema")
    op.drop_table("incidente_sistema")

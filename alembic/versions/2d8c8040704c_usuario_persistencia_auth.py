"""usuario_persistencia_auth

Revision ID: 2d8c8040704c
Revises: 82cf135f0f7b
Create Date: 2026-07-03 12:46:24.275085

ADR-014 — migración auth InMemory -> PostgreSQL. Agrega a `usuario` los
campos que hoy solo viven en InMemoryUserStore.UsuarioRecord (nombre,
estado_cuenta, motivo_rechazo, variante_tema) y el estado de bloqueo MFA
cross-sesión (ADR-011) que hoy vive en InMemorySessionStore._mfa_bloqueo.
Crea `documento_usuario` (documentos de autorregistro, EP-AUTH-07) y
`mfa_sesion` (desafío MFA de 2 pasos, EP-AUTH-01/02) para que el flujo
login -> mfa sobreviva a un reinicio o a múltiples réplicas.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2d8c8040704c'
down_revision: Union[str, None] = '82cf135f0f7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("nombre", sa.Text(), nullable=False, server_default=""))
    op.add_column(
        "usuario",
        sa.Column("estado_cuenta", sa.String(length=30), nullable=False, server_default="ACTIVO"),
    )
    op.add_column("usuario", sa.Column("motivo_rechazo", sa.Text(), nullable=True))
    op.add_column(
        "usuario",
        sa.Column("variante_tema", sa.String(length=30), nullable=False, server_default="OSCURO_ESTANDAR"),
    )
    op.add_column(
        "usuario",
        sa.Column("mfa_fallos_consecutivos", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("usuario", sa.Column("mfa_bloqueado_hasta", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "chk_usuario_estado_cuenta",
        "usuario",
        "estado_cuenta IN ('PENDIENTE_DOCUMENTOS','EN_REVISION','ACTIVO','RECHAZADO')",
    )
    op.create_check_constraint(
        "chk_usuario_variante_tema",
        "usuario",
        "variante_tema IN ('OSCURO_ESTANDAR','OSCURO_SUAVE','OSCURO_ALTO_CONTRASTE',"
        "'CLARO_ESTANDAR','CLARO_CALIDO','CLARO_ALTO_CONTRASTE')",
    )

    op.create_table(
        "documento_usuario",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_documento_usuario_usuario", "documento_usuario", ["usuario_id"])

    op.create_table(
        "mfa_sesion",
        sa.Column("token", sa.String(length=36), primary_key=True),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("usuario.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("intentos_fallidos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("usado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("requiere_codigo_real", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("codigo_hash", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_mfa_sesion_usuario", "mfa_sesion", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("idx_mfa_sesion_usuario", table_name="mfa_sesion")
    op.drop_table("mfa_sesion")
    op.drop_index("idx_documento_usuario_usuario", table_name="documento_usuario")
    op.drop_table("documento_usuario")
    op.drop_constraint("chk_usuario_variante_tema", "usuario", type_="check")
    op.drop_constraint("chk_usuario_estado_cuenta", "usuario", type_="check")
    op.drop_column("usuario", "mfa_bloqueado_hasta")
    op.drop_column("usuario", "mfa_fallos_consecutivos")
    op.drop_column("usuario", "variante_tema")
    op.drop_column("usuario", "motivo_rechazo")
    op.drop_column("usuario", "estado_cuenta")
    op.drop_column("usuario", "nombre")

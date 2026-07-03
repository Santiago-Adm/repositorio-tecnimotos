"""mfa_intento_auditoria

Revision ID: b536bf0f31a2
Revises: 993fb3e102f4
Create Date: 2026-07-02 15:29:42.632852

Tabla de auditoría de intentos MFA (R29) — ADR-011. Sin FK a usuario: el
store de autenticación es InMemory hoy (usuario_id no existe en la tabla
usuario de PostgreSQL en esta etapa del proyecto) — ver ADR-011.
usuario_id es String, no UUID: el store InMemory usa literales no-UUID para
cuentas semilla (ej. "user-admin-seed").
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b536bf0f31a2'
down_revision: Union[str, None] = '993fb3e102f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mfa_intento",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("usuario_id", sa.String(100), nullable=False),
        sa.Column("resultado", sa.String(20), nullable=False),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "resultado IN ('EXITOSO','CODIGO_INCORRECTO','EXPIRADO','BLOQUEADO','TOKEN_INVALIDO')",
            name="chk_mfa_intento_resultado",
        ),
    )
    op.create_index("idx_mfa_intento_usuario", "mfa_intento", ["usuario_id"])
    op.create_index("idx_mfa_intento_creado", "mfa_intento", ["creado_en"])


def downgrade() -> None:
    op.drop_index("idx_mfa_intento_creado", table_name="mfa_intento")
    op.drop_index("idx_mfa_intento_usuario", table_name="mfa_intento")
    op.drop_table("mfa_intento")

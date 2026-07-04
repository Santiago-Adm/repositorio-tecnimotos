"""usuario_eliminado_auditoria

Revision ID: f4bd9d536a4b
Revises: 593686985730
Create Date: 2026-07-04 00:15:51.926732

Tabla de auditoría append-only de eliminaciones físicas de usuario (R29) —
ADR-016. Sin FK a usuario.id: el registro debe sobrevivir al DELETE que
audita (mismo patrón que mfa_intento, ADR-011).

Nota: el autogenerate detectó además varios diffs falsos-positivos no
relacionados con este cambio (categoria/proforma/rendicion_mecanico/
usuario_perfil) causados por modelos no registrados en alembic/env.py en
sesiones anteriores — no se incluyen aquí, fuera de alcance de esta pieza.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f4bd9d536a4b'
down_revision: Union[str, None] = '593686985730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'usuario_eliminado',
        sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('usuario_id_original', sa.String(length=100), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('nombre', sa.Text(), nullable=False),
        sa.Column('rol', sa.String(length=30), nullable=False),
        sa.Column('eliminado_por', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('motivo', sa.Text(), nullable=True),
        sa.Column('eliminado_en', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['eliminado_por'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_usuario_eliminado_en', 'usuario_eliminado', ['eliminado_en'], unique=False)
    op.create_index('idx_usuario_eliminado_original', 'usuario_eliminado', ['usuario_id_original'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_usuario_eliminado_original', table_name='usuario_eliminado')
    op.drop_index('idx_usuario_eliminado_en', table_name='usuario_eliminado')
    op.drop_table('usuario_eliminado')

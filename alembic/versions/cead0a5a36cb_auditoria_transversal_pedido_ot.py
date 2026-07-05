"""auditoria_transversal_pedido_ot

Revision ID: cead0a5a36cb
Revises: f4bd9d536a4b
Create Date: 2026-07-04 09:13:59.881259

FASE 2 (R29) — auditoría append-only de acciones de negocio sobre Pedido y
OrdenTrabajo (quién/qué/cuándo), mismo criterio ya validado en
movimiento_stock/mfa_intento/usuario_eliminado. Se mantiene el patrón "una
tabla por contexto" del proyecto — no se generaliza usuario_eliminado a
otros dominios.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cead0a5a36cb'
down_revision: Union[str, None] = 'f4bd9d536a4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pedido_evento',
        sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('pedido_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('evento', sa.String(length=50), nullable=False),
        sa.Column('estado_anterior', sa.String(length=20), nullable=False),
        sa.Column('estado_nuevo', sa.String(length=20), nullable=False),
        sa.Column('actor_id', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedido.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_pedido_evento_pedido', 'pedido_evento', ['pedido_id'], unique=False)
    op.create_index('idx_pedido_evento_actor', 'pedido_evento', ['actor_id'], unique=False)

    op.create_table(
        'orden_trabajo_evento',
        sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('ot_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('evento', sa.String(length=50), nullable=False),
        sa.Column('estado_anterior', sa.String(length=20), nullable=False),
        sa.Column('estado_nuevo', sa.String(length=20), nullable=False),
        sa.Column('actor_id', sa.String(length=100), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ot_id'], ['orden_trabajo.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_ot_evento_ot', 'orden_trabajo_evento', ['ot_id'], unique=False)
    op.create_index('idx_ot_evento_actor', 'orden_trabajo_evento', ['actor_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_ot_evento_actor', table_name='orden_trabajo_evento')
    op.drop_index('idx_ot_evento_ot', table_name='orden_trabajo_evento')
    op.drop_table('orden_trabajo_evento')

    op.drop_index('idx_pedido_evento_actor', table_name='pedido_evento')
    op.drop_index('idx_pedido_evento_pedido', table_name='pedido_evento')
    op.drop_table('pedido_evento')

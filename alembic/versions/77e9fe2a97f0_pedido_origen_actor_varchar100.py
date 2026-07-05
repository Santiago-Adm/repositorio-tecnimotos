"""pedido_origen_actor_varchar100

Revision ID: 77e9fe2a97f0
Revises: cead0a5a36cb
Create Date: 2026-07-04 09:40:34.776199

Bug real encontrado verificando FASE 2 con curl contra Postgres: `crear_pedido`
nunca había recibido un actor_id real (leía `request.state.usuario_id`, un
atributo que `require_roles` nunca setea — siempre "" en producción). Al
corregir ese bug en esta misma sesión, `origen_actor` empezó a recibir un
UUID real (36 caracteres) contra una columna VARCHAR(30) — StringDataRight-
TruncationError real, reproducido antes de este fix. Se amplía a VARCHAR(100),
igual que `actor_id` en movimiento_stock/pedido_evento/orden_trabajo_evento.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77e9fe2a97f0'
down_revision: Union[str, None] = 'cead0a5a36cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('pedido', 'origen_actor', type_=sa.String(length=100), existing_type=sa.String(length=30))


def downgrade() -> None:
    op.alter_column('pedido', 'origen_actor', type_=sa.String(length=30), existing_type=sa.String(length=100))

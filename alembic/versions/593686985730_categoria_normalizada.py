"""categoria_normalizada

Revision ID: 593686985730
Revises: 2d8c8040704c
Create Date: 2026-07-03 17:09:40.481142

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '593686985730'
down_revision: Union[str, None] = '2d8c8040704c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CATEGORIAS_SEED = [
    ("motor", 1), ("transmision", 2), ("frenos", 3), ("electrico", 4),
    ("carroceria", 5), ("suspension", 6), ("tecnico_especializado", 7),
    ("consumible", 8), ("otro", 9),
]


def upgrade() -> None:
    op.create_table(
        "categoria",
        sa.Column("id", UUID(as_uuid=False), primary_key=True),
        sa.Column("nombre", sa.String(50), nullable=False),
        sa.Column("orden", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("nombre", name="uq_categoria_nombre"),
    )
    op.create_index("idx_categoria_orden", "categoria", ["orden"])

    # Semilla: los 9 valores del enum CategoriaRepuesto que ya existía en código
    # (preserva el dominio actual como punto de partida editable por admin).
    categoria_table = sa.table(
        "categoria",
        sa.column("id", UUID(as_uuid=False)),
        sa.column("nombre", sa.String),
        sa.column("orden", sa.Integer),
    )
    import uuid
    op.bulk_insert(categoria_table, [
        {"id": str(uuid.uuid4()), "nombre": nombre, "orden": orden}
        for nombre, orden in CATEGORIAS_SEED
    ])

    # FK real desde repuesto.categoria (varchar existente, sin cambio de tipo)
    # hacia categoria.nombre — ON UPDATE CASCADE propaga renombres automáticamente,
    # sin ON DELETE explícito → Postgres aplica NO ACTION (bloquea el borrado si
    # hay repuestos usando la categoría, decisión confirmada con Sant).
    op.create_foreign_key(
        "fk_repuesto_categoria", "repuesto", "categoria",
        ["categoria"], ["nombre"], onupdate="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_repuesto_categoria", "repuesto", type_="foreignkey")
    op.drop_index("idx_categoria_orden", table_name="categoria")
    op.drop_table("categoria")

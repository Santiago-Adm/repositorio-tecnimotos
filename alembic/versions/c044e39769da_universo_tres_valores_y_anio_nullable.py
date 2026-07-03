"""universo_tres_valores_y_anio_nullable

Revision ID: c044e39769da
Revises: 2c9eda3438e9
Create Date: 2026-07-02 14:59:57.232328

Sesión migración Bajaj (02 §1.5 actualizado): el universo 'mototaxi' se separa
en 'mototaxi_3r' y 'mototaxi_4r' para distinguir repuestos por número de ruedas
del vehículo. 'motolineal' no cambia. Datos existentes con universo='mototaxi'
(seed/dev, no hay compuerta #2 de producción activa aún) se remapean a
'mototaxi_3r' por ser el caso mayoritario en el catálogo real de Bajaj.

año pasa a nullable: filas migradas desde el Excel Bajaj no traen año por
vehículo (curación manual posterior — ver prompt de sesión), y el dominio ya
soporta año=None (Repuesto.__post_init__ solo valida rango si no es None).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c044e39769da'
down_revision: Union[str, None] = '2c9eda3438e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Soltar constraints viejos antes de tocar los datos que dejarían de cumplirlos
    op.drop_constraint("chk_repuesto_universo", "repuesto", type_="check")
    op.drop_constraint("chk_repuesto_año", "repuesto", type_="check")

    # 2. Datos existentes: 'mototaxi' -> 'mototaxi_3r' (mayoría del catálogo real Bajaj)
    op.execute("UPDATE repuesto SET universo = 'mototaxi_3r' WHERE universo = 'mototaxi'")

    # 3. año nullable
    op.alter_column("repuesto", "año", existing_type=sa.Integer(), nullable=True)

    # 4. Recrear constraints con los nuevos valores/reglas
    op.create_check_constraint(
        "chk_repuesto_universo",
        "repuesto",
        "universo IN ('motolineal', 'mototaxi_3r', 'mototaxi_4r')",
    )
    op.create_check_constraint(
        "chk_repuesto_año",
        "repuesto",
        "año IS NULL OR año BETWEEN 1990 AND 2100",
    )


def downgrade() -> None:
    op.drop_constraint("chk_repuesto_año", "repuesto", type_="check")
    op.create_check_constraint(
        "chk_repuesto_año",
        "repuesto",
        "año BETWEEN 1990 AND 2100",
    )

    op.drop_constraint("chk_repuesto_universo", "repuesto", type_="check")
    op.create_check_constraint(
        "chk_repuesto_universo",
        "repuesto",
        "universo IN ('mototaxi', 'motolineal')",
    )

    op.execute(
        "UPDATE repuesto SET universo = 'mototaxi' "
        "WHERE universo IN ('mototaxi_3r', 'mototaxi_4r')"
    )

    op.execute("UPDATE repuesto SET año = 1990 WHERE año IS NULL")
    op.alter_column("repuesto", "año", existing_type=sa.Integer(), nullable=False)

"""envio_distrito_estructurado

Revision ID: 4186070f6f3b
Revises: 77e9fe2a97f0
Create Date: 2026-07-04 14:16:18.854361

ADR-018. FASE 0 confirmó con `\\d envio` que `direccion_destino` (columna
real, cifrada con Fernet — 03 §5.7) vive en `envio`, no en `pedido` —
`PedidoModel` no tiene ningún campo de dirección. `envio` solo existe para
pedidos que requieren despacho fuera de la ciudad (02 §1.1), 1:1 con
`pedido` (`unique=True` en `pedido_id`). El widget de distribución
geográfica del panel SUPERADMIN necesita una clasificación por distrito
confiable para agregación — texto libre cifrado no sirve para agrupar.
Se agrega `distrito` como columna nueva, sin cifrar (no es PII de
dirección exacta, es una categoría de 16 valores), con CHECK contra los
16 distritos reales de la provincia de Huamanga, Ayacucho.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4186070f6f3b'
down_revision: Union[str, None] = '77e9fe2a97f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DISTRITOS_HUAMANGA = (
    "AYACUCHO", "ACOCRO", "ACOS_VINCHOS", "CARMEN_ALTO", "CHIARA", "OCROS",
    "PACAYCASA", "QUINUA", "SAN_JOSE_DE_TICLLAS", "SAN_JUAN_BAUTISTA",
    "SANTIAGO_DE_PISCHA", "SOCOS", "TAMBILLO", "VINCHOS", "JESUS_NAZARENO",
    "ANDRES_AVELINO_CACERES_DORREGARAY",
)


def upgrade() -> None:
    op.add_column("envio", sa.Column("distrito", sa.String(length=40), nullable=True))
    op.create_check_constraint(
        "chk_envio_distrito",
        "envio",
        "distrito IS NULL OR distrito IN (" + ", ".join(f"'{d}'" for d in _DISTRITOS_HUAMANGA) + ")",
    )
    op.create_index("idx_envio_distrito", "envio", ["distrito"])


def downgrade() -> None:
    op.drop_index("idx_envio_distrito", table_name="envio")
    op.drop_constraint("chk_envio_distrito", "envio", type_="check")
    op.drop_column("envio", "distrito")

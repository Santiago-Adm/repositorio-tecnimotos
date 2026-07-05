"""email_cifrado_real_mas_hash

Pieza verificación profunda (2026-07-05) — hallazgo real: el campo
usuario.email decía "# cifrado Fernet" en el modelo pero se guardaba en
texto plano. Esta migración cifra los valores existentes y agrega
email_hash (índice ciego HMAC-SHA256, determinístico) para poder seguir
buscando por email — Fernet no es determinístico, así que ya no se puede
hacer WHERE email = :valor sobre la columna cifrada.

Revision ID: 9b4702918fb5
Revises: 438034b83227
Create Date: 2026-07-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9b4702918fb5'
down_revision: Union[str, None] = '438034b83227'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from src.shared.infrastructure.fernet import encrypt, hash_email

    op.add_column("usuario", sa.Column("email_hash", sa.Text(), nullable=True))

    conn = op.get_bind()
    usuario_tabla = sa.table(
        "usuario",
        sa.column("id", postgresql.UUID(as_uuid=False)),
        sa.column("email", sa.Text()),
        sa.column("email_hash", sa.Text()),
    )
    filas = conn.execute(sa.select(usuario_tabla.c.id, usuario_tabla.c.email)).fetchall()
    for uid, email_plano in filas:
        conn.execute(
            usuario_tabla.update()
            .where(usuario_tabla.c.id == uid)
            .values(email_hash=hash_email(email_plano), email=encrypt(email_plano))
        )

    op.drop_constraint("usuario_email_key", "usuario", type_="unique")
    op.alter_column("usuario", "email_hash", nullable=False)
    op.create_unique_constraint("usuario_email_hash_key", "usuario", ["email_hash"])
    op.create_index("idx_usuario_email_hash", "usuario", ["email_hash"])


def downgrade() -> None:
    from src.shared.infrastructure.fernet import decrypt

    conn = op.get_bind()
    usuario_tabla = sa.table(
        "usuario",
        sa.column("id", postgresql.UUID(as_uuid=False)),
        sa.column("email", sa.Text()),
    )
    filas = conn.execute(sa.select(usuario_tabla.c.id, usuario_tabla.c.email)).fetchall()
    for uid, email_cifrado in filas:
        conn.execute(
            usuario_tabla.update()
            .where(usuario_tabla.c.id == uid)
            .values(email=decrypt(email_cifrado))
        )

    op.drop_index("idx_usuario_email_hash", table_name="usuario")
    op.drop_constraint("usuario_email_hash_key", "usuario", type_="unique")
    op.drop_column("usuario", "email_hash")
    op.create_unique_constraint("usuario_email_key", "usuario", ["email"])

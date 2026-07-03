"""Alembic env.py — async PostgreSQL con todos los modelos del proyecto (03 §5)."""
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Importar todos los modelos para que Alembic los detecte ──────────────────
# El orden importa: shared primero (usuario, etc. son FK de otros módulos)
from src.shared.infrastructure.database import Base  # noqa: F401 — registra metadata
import src.shared.infrastructure.models.usuario_model  # noqa: F401
import src.shared.infrastructure.models.sistema_model   # noqa: F401
import src.shared.infrastructure.models.mfa_intento_model  # noqa: F401
import src.catalogo.infrastructure.repositories.models.repuesto_model          # noqa: F401
import src.catalogo.infrastructure.repositories.models.historial_precio_model  # noqa: F401
import src.catalogo.infrastructure.repositories.models.imagen_repuesto_model   # noqa: F401
import src.stock.infrastructure.repositories.models.stock_model                # noqa: F401
import src.pedidos.infrastructure.repositories.models.pedido_models            # noqa: F401
import src.taller.infrastructure.repositories.models.taller_models             # noqa: F401

# ── Config Alembic ────────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Sobreescribir DATABASE_URL desde variable de entorno si está disponible
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # asyncpg requiere el esquema postgresql+asyncpg://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


# ── Offline mode (genera SQL sin conexión) ────────────────────────────────────
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (conexión real a PostgreSQL) ──────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

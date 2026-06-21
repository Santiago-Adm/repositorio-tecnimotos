"""
Fixtures compartidos para tests de integración contra PostgreSQL real.
Se salta automáticamente si la BD no está disponible.
Uso: from tests.integration.conftest_pg import pg_session
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database import create_engine, create_session_factory


@pytest.fixture
async def pg_session() -> AsyncSession:
    """
    AsyncSession contra PostgreSQL real. Se salta si la BD no responde.
    Usa transacción que hace ROLLBACK al final → tests son idempotentes.
    """
    engine = create_engine()
    try:
        async with engine.connect() as probe:
            await probe.execute(text("SELECT 1"))
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"PostgreSQL no disponible — skipping PG test: {exc}")

    factory = create_session_factory(engine)
    async with factory() as session:
        # Envuelve en transacción anidada para rollback al final
        async with session.begin_nested():
            yield session
            await session.rollback()

    await engine.dispose()

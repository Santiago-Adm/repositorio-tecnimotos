"""
Tests de integración — StockRepositoryPG contra PostgreSQL real.
Se salta automáticamente si PostgreSQL no está disponible.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from decimal import Decimal

from src.catalogo.domain.models.repuesto import CategoriaRepuesto, Repuesto, UniversoRepuesto
from src.catalogo.infrastructure.repositories.repuesto_repository_pg import RepuestoRepositoryPG
from src.stock.domain.models.stock import Reabastecimiento, ReabastecimientoItem, StockRepuesto
from src.stock.infrastructure.repositories.stock_repository_pg import StockRepositoryPG
from tests.integration.conftest_pg import pg_session


@pytest.fixture
async def repo(pg_session):
    return StockRepositoryPG(pg_session)


@pytest.fixture
async def repuesto_id(pg_session) -> str:
    """Crea un Repuesto real en BD para satisfacer FK de stock_repuesto."""
    rep_repo = RepuestoRepositoryPG(pg_session)
    rep = Repuesto(
        codigo=f"STK-FK-{uuid.uuid4().hex[:8]}",
        nombre="Repuesto para test stock PG",
        universo=UniversoRepuesto.MOTOTAXI,
        modelo="Test",
        año=2022,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("10.00"),
    )
    saved = await rep_repo.guardar(rep)
    await pg_session.flush()
    return saved.id


class TestStockRepositoryPG:

    async def test_guardar_y_obtener_por_repuesto_id(self, repo, repuesto_id, pg_session):
        stock = StockRepuesto(
            repuesto_id=repuesto_id,
            codigo=f"PG-TEST-{repuesto_id[:8]}",
            cantidad_disponible=50,
            umbral_minimo=5,
        )
        saved = await repo.guardar(stock)
        assert saved.repuesto_id == repuesto_id

        obtenido = await repo.obtener_por_repuesto_id(repuesto_id)
        assert obtenido is not None
        assert obtenido.cantidad_disponible == 50
        assert obtenido.umbral_minimo == 5

    async def test_obtener_por_codigo(self, repo, repuesto_id, pg_session):
        codigo = f"PGCOD-{repuesto_id[:8]}"
        stock = StockRepuesto(repuesto_id=repuesto_id, codigo=codigo, cantidad_disponible=20)
        await repo.guardar(stock)

        result = await repo.obtener_por_codigo(codigo)
        assert result is not None
        assert result.repuesto_id == repuesto_id

    async def test_actualizar_cantidades(self, repo, repuesto_id, pg_session):
        stock = StockRepuesto(repuesto_id=repuesto_id, codigo=f"UPD-{repuesto_id[:8]}",
                              cantidad_disponible=100)
        await repo.guardar(stock)

        stock.cantidad_disponible = 80
        stock.cantidad_apartada = 20
        await repo.actualizar(stock)

        actualizado = await repo.obtener_por_repuesto_id(repuesto_id)
        assert actualizado.cantidad_disponible == 80
        assert actualizado.cantidad_apartada == 20

    async def test_listar_todos(self, repo, repuesto_id, pg_session):
        """repuesto_id satisface FK; usamos ese mismo para 1 stock entry."""
        rid1 = repuesto_id
        await repo.guardar(StockRepuesto(repuesto_id=rid1, codigo=f"LST1-{rid1[:6]}"))

        todos = await repo.listar_todos()
        ids = {s.repuesto_id for s in todos}
        assert rid1 in ids

    async def test_guardar_reabastecimiento(self, repo, pg_session):
        reab = Reabastecimiento(
            proveedor="Proveedor PG Test",
            solicitado_por="u-test",
        )
        saved = await repo.guardar_reabastecimiento(reab)
        assert saved.id == reab.id

        obtenido = await repo.obtener_reabastecimiento(reab.id)
        assert obtenido is not None
        assert obtenido.proveedor == "Proveedor PG Test"
        assert obtenido.estado.value == "SOLICITADO"

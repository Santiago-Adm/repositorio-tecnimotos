"""
Tests de integración — CatalogoAdapterPG / StockAdapterPG contra PostgreSQL real.
Hasta esta sesión, _get_catalogo()/_get_stock() en api/routes/pedidos.py siempre
devolvían los adaptadores InMemory ("para tests", nunca poblados en el arranque
real) — POST /v1/pedidos rechazaba cualquier repuesto real de PostgreSQL.
Se salta automáticamente si PostgreSQL no está disponible.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel
from src.pedidos.domain.models.pedido import DomainError
from src.pedidos.infrastructure.adapters.catalogo_adapter_pg import (
    CatalogoAdapterPG,
    StockAdapterPG,
)
from src.stock.infrastructure.repositories.models.stock_model import StockRepuestoModel
from tests.integration.conftest_pg import pg_session


@pytest.fixture
async def repuesto_con_stock(pg_session):
    codigo = f"TEST-ADPG-{uuid.uuid4().hex[:8]}"
    modelo = RepuestoModel(
        id=str(uuid.uuid4()), codigo=codigo, nombre="Repuesto test adapter PG",
        universo="motolineal", modelo="Universal", categoria="motor",
        precio_venta=Decimal("30.00"), activo=True,
    )
    pg_session.add(modelo)
    await pg_session.flush()
    stock = StockRepuestoModel(
        id=str(uuid.uuid4()), repuesto_id=modelo.id, codigo=codigo,
        cantidad_disponible=5, umbral_minimo=1,
    )
    pg_session.add(stock)
    await pg_session.flush()
    return modelo, stock


class TestCatalogoAdapterPG:

    async def test_obtener_precio_vigente_encontrado(self, pg_session, repuesto_con_stock):
        modelo, _ = repuesto_con_stock
        adapter = CatalogoAdapterPG(pg_session)
        info = await adapter.obtener_precio_vigente(modelo.codigo)
        assert info.codigo == modelo.codigo
        assert info.precio_venta == Decimal("30.00")
        assert info.repuesto_id == modelo.id
        assert info.activo is True

    async def test_obtener_precio_vigente_no_encontrado_lanza_domain_error(self, pg_session):
        adapter = CatalogoAdapterPG(pg_session)
        with pytest.raises(DomainError):
            await adapter.obtener_precio_vigente("CODIGO-QUE-NO-EXISTE-XYZ")

    async def test_verificar_existencia_true(self, pg_session, repuesto_con_stock):
        modelo, _ = repuesto_con_stock
        adapter = CatalogoAdapterPG(pg_session)
        assert await adapter.verificar_existencia(modelo.codigo) is True

    async def test_verificar_existencia_false(self, pg_session):
        adapter = CatalogoAdapterPG(pg_session)
        assert await adapter.verificar_existencia("CODIGO-QUE-NO-EXISTE-XYZ") is False


class TestStockAdapterPG:

    async def test_consultar_disponibilidad(self, pg_session, repuesto_con_stock):
        modelo, stock = repuesto_con_stock
        adapter = StockAdapterPG(pg_session)
        resp = await adapter.consultar_disponibilidad(modelo.id)
        assert resp.cantidad_disponible == 5

    async def test_consultar_disponibilidad_repuesto_sin_stock_retorna_cero(self, pg_session):
        adapter = StockAdapterPG(pg_session)
        resp = await adapter.consultar_disponibilidad(str(uuid.uuid4()))
        assert resp.cantidad_disponible == 0

    async def test_apartar_stock_exitoso_decrementa_disponible(self, pg_session, repuesto_con_stock):
        modelo, stock = repuesto_con_stock
        adapter = StockAdapterPG(pg_session)
        ok = await adapter.apartar_stock(modelo.id, 3, actor_id="a-1", referencia_id="p-1")
        assert ok is True
        resp = await adapter.consultar_disponibilidad(modelo.id)
        assert resp.cantidad_disponible == 2

    async def test_apartar_stock_insuficiente_retorna_false(self, pg_session, repuesto_con_stock):
        modelo, _ = repuesto_con_stock
        adapter = StockAdapterPG(pg_session)
        ok = await adapter.apartar_stock(modelo.id, 999, actor_id="a-1", referencia_id="p-1")
        assert ok is False

    async def test_liberar_stock_exitoso_incrementa_disponible(self, pg_session, repuesto_con_stock):
        modelo, _ = repuesto_con_stock
        adapter = StockAdapterPG(pg_session)
        await adapter.apartar_stock(modelo.id, 3, actor_id="a-1", referencia_id="p-1")
        ok = await adapter.liberar_stock(modelo.id, 3, actor_id="a-1", referencia_id="p-1")
        assert ok is True
        resp = await adapter.consultar_disponibilidad(modelo.id)
        assert resp.cantidad_disponible == 5

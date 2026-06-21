"""
Tests de integración — PedidoRepositoryPG contra PostgreSQL real.
Se salta automáticamente si PostgreSQL no está disponible.

Nota FK: PedidoModel.cliente_id es nullable → se puede guardar pedido sin cliente.
Los tests usan cliente_id=None para evitar FK hacia la tabla cliente.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from src.pedidos.domain.models.pedido import EstadoPedido, Pedido, PedidoItem
from src.pedidos.infrastructure.repositories.pedido_repository_pg import PedidoRepositoryPG
from tests.integration.conftest_pg import pg_session


@pytest.fixture
async def repo(pg_session):
    return PedidoRepositoryPG(pg_session)


class TestPedidoRepositoryPG:

    async def test_guardar_y_obtener_pedido(self, repo, pg_session):
        pedido = Pedido(canal_origen="presencial", origen_actor="VENDEDOR")
        saved = await repo.guardar(pedido)
        assert saved.id == pedido.id

        obtenido = await repo.obtener_por_id(pedido.id)
        assert obtenido is not None
        assert obtenido.canal_origen == "presencial"
        assert obtenido.estado == EstadoPedido.BORRADOR

    async def test_pedido_sin_cliente_nullable(self, repo, pg_session):
        """PedidoModel.cliente_id es nullable — permite pedidos sin cliente."""
        pedido = Pedido(canal_origen="S2", origen_actor="CLIENTE")
        await repo.guardar(pedido)

        obtenido = await repo.obtener_por_id(pedido.id)
        assert obtenido is not None
        assert obtenido.cliente_id is None

    async def test_actualizar_estado(self, repo, pg_session):
        pedido = Pedido(canal_origen="presencial", origen_actor="VENDEDOR")
        await repo.guardar(pedido)

        pedido.avanzar_estado(EstadoPedido.CONFIRMADO)
        await repo.actualizar(pedido)

        actualizado = await repo.obtener_por_id(pedido.id)
        assert actualizado.estado == EstadoPedido.CONFIRMADO

    async def test_guardar_proforma(self, repo, pg_session):
        pedido = Pedido(canal_origen="presencial", origen_actor="VENDEDOR")
        await repo.guardar(pedido)

        from src.pedidos.domain.models.pedido import Proforma
        proforma = Proforma(
            pedido_id=pedido.id,
            numero_referencia=f"PRF-{pedido.id[:8].upper()}",
            monto_total=Decimal("150.00"),
        )
        saved = await repo.guardar_proforma(proforma)
        assert saved.id == proforma.id

        obtenida = await repo.obtener_proforma(proforma.id)
        assert obtenida is not None
        assert obtenida.monto_total == Decimal("150.00")

    async def test_guardar_envio(self, repo, pg_session):
        pedido = Pedido(canal_origen="S2", origen_actor="VENDEDOR")
        await repo.guardar(pedido)

        from src.pedidos.domain.models.pedido import Envio
        envio = Envio(
            pedido_id=pedido.id,
            empresa_encomienda="Marvisur",
            direccion_destino="Jr. Lima 123",
        )
        saved = await repo.guardar_envio(envio)
        assert saved.id == envio.id

        obtenido = await repo.obtener_envio_por_pedido(pedido.id)
        assert obtenido is not None
        assert obtenido.empresa_encomienda == "Marvisur"

    async def test_listar_todos(self, repo, pg_session):
        p1 = Pedido(canal_origen="presencial", origen_actor="VENDEDOR")
        p2 = Pedido(canal_origen="S2", origen_actor="CLIENTE")
        await repo.guardar(p1)
        await repo.guardar(p2)

        todos = await repo.listar_todos()
        ids = {p.id for p in todos}
        assert p1.id in ids
        assert p2.id in ids

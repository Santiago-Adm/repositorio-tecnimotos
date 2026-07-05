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

from src.pedidos.application.use_cases.gestionar_pedido import ListarPedidosUseCase, ObtenerPedidoUseCase
from src.pedidos.domain.models.pedido import Comprobante, EstadoPedido, Pedido, PedidoEvento, PedidoItem, TipoComprobante
from src.pedidos.infrastructure.repositories.models.pedido_models import ClienteModel
from src.pedidos.infrastructure.repositories.pedido_repository_pg import PedidoRepositoryPG
from src.shared.infrastructure.repositories.usuario_repository_pg import UsuarioRepositoryPG
from tests.integration.conftest_pg import pg_session


@pytest.fixture
async def repo(pg_session):
    return PedidoRepositoryPG(pg_session)


@pytest.fixture
async def usuario_repo(pg_session):
    return UsuarioRepositoryPG(pg_session)


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

    async def test_guardar_y_listar_comprobantes(self, repo, pg_session):
        """listar_comprobantes() contra PG real — EP-ADM-10 depende de este método
        (bug real detectado: PedidoRepositoryPG no lo implementaba, solo InMemory)."""
        pedido = Pedido(canal_origen="presencial", origen_actor="VENDEDOR")
        await repo.guardar(pedido)

        comp = Comprobante(
            pedido_id=pedido.id, monto=Decimal("120.50"),
            tipo=TipoComprobante.BOLETA, emitido_por="user-test",
        )
        comp.aprobar()
        await repo.guardar_comprobante(comp)

        comprobantes = await repo.listar_comprobantes()
        assert any(c.id == comp.id and c.monto == Decimal("120.50") for c in comprobantes)

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


class TestScopingClientePedidosPG:
    """Reproduce contra Postgres real lo que hace listar_pedidos/obtener_pedido
    en api/routes/pedidos.py para CLIENTE_*: resolver cliente_id real (tabla
    `cliente`, con FK real desde `pedido.cliente_id`) a partir del usuario_id
    del JWT — no probado con InMemoryPedidoRepository porque su
    obtener_cliente_id_por_usuario() siempre devuelve None a propósito."""

    async def test_cliente_ve_su_propio_pedido_via_cliente_id_resuelto(self, repo, usuario_repo, pg_session):
        user = await usuario_repo.crear_usuario(
            email="scoping-conductor@test.com", nombre="Conductor Scoping", rol="CLIENTE_CONDUCTOR", password="pass12345",
        )
        pg_session.add(ClienteModel(usuario_id=user.usuario_id, segmento="S1"))
        await pg_session.flush()
        cliente_id = await repo.obtener_cliente_id_por_usuario(user.usuario_id)
        assert cliente_id is not None

        pedido = Pedido(canal_origen="presencial", origen_actor="CLIENTE", cliente_id=cliente_id)
        await repo.guardar(pedido)

        listados = await ListarPedidosUseCase(repo).execute(cliente_id=cliente_id)
        assert {p.id for p in listados} == {pedido.id}

        obtenido = await ObtenerPedidoUseCase(repo).execute(pedido.id)
        assert obtenido.cliente_id == cliente_id

    async def test_cliente_no_ve_pedido_de_otro_cliente(self, repo, usuario_repo, pg_session):
        dueno = await usuario_repo.crear_usuario(
            email="scoping-dueno@test.com", nombre="Dueño", rol="CLIENTE_DISTRITO", password="pass12345",
        )
        pg_session.add(ClienteModel(usuario_id=dueno.usuario_id, segmento="S2"))
        otro = await usuario_repo.crear_usuario(
            email="scoping-otro@test.com", nombre="Otro", rol="CLIENTE_RURAL", password="pass12345",
        )
        pg_session.add(ClienteModel(usuario_id=otro.usuario_id, segmento="S4"))
        await pg_session.flush()

        cliente_id_dueno = await repo.obtener_cliente_id_por_usuario(dueno.usuario_id)
        cliente_id_otro = await repo.obtener_cliente_id_por_usuario(otro.usuario_id)
        assert cliente_id_dueno != cliente_id_otro

        pedido = Pedido(canal_origen="presencial", origen_actor="CLIENTE", cliente_id=cliente_id_dueno)
        await repo.guardar(pedido)

        listados_otro = await ListarPedidosUseCase(repo).execute(cliente_id=cliente_id_otro)
        assert pedido.id not in {p.id for p in listados_otro}

        obtenido = await ObtenerPedidoUseCase(repo).execute(pedido.id)
        assert obtenido.cliente_id != cliente_id_otro


class TestPedidoEventoPG:
    async def test_registrar_y_listar_eventos(self, repo, pg_session):
        pedido = Pedido(canal_origen="presencial", origen_actor="VENDEDOR")
        await repo.guardar(pedido)

        await repo.registrar_evento(PedidoEvento(
            pedido_id=pedido.id, evento="EP-PED-01-CREADO",
            estado_anterior="BORRADOR", estado_nuevo="BORRADOR", actor_id="actor-1",
        ))
        await repo.registrar_evento(PedidoEvento(
            pedido_id=pedido.id, evento="EP-PED-04-CONFIRMAR",
            estado_anterior="BORRADOR", estado_nuevo="CONFIRMADO", actor_id="actor-1",
        ))

        eventos = await repo.listar_eventos(pedido.id)
        assert [e.evento for e in eventos] == ["EP-PED-01-CREADO", "EP-PED-04-CONFIRMAR"]
        assert eventos[1].estado_nuevo == "CONFIRMADO"

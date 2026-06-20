"""
Test específico del criterio 09 §3.2 — Flujo comprobante.
Verifica: VENDEDOR SIEMPRE pasa por PENDIENTE_VALIDACION (07 ABAC-06 corregido).
"""
import pytest
from decimal import Decimal

from src.pedidos.domain.models.pedido import (
    EstadoComprobante,
    TipoComprobante,
)
from src.pedidos.application.use_cases.gestionar_comprobante import (
    AprobarComprobanteCommand,
    AprobarComprobanteUseCase,
    AnularComprobanteCommand,
    AnularComprobanteUseCase,
    GenerarComprobanteCommand,
    GenerarComprobanteUseCase,
)
from src.pedidos.infrastructure.repositories.pedido_repository_inmemory import (
    InMemoryPedidoRepository,
)
from src.pedidos.domain.models.pedido import Pedido
from src.shared.events.event_bus import InMemoryEventBus


@pytest.fixture
async def repo_con_pedido():
    repo = InMemoryPedidoRepository()
    pedido = Pedido(canal_origen="presencial", origen_actor="v")
    await repo.guardar(pedido)
    return repo, pedido.id


class TestComprobanteFlujoVendedor:
    """
    Verifica que VENDEDOR SIEMPRE genera PENDIENTE_VALIDACION.
    Corrección de ABAC-06 — ver 09 §3.2 fila 'Flujo comprobante'.
    """

    async def test_vendedor_siempre_pendiente_validacion(self, repo_con_pedido):
        repo, pedido_id = repo_con_pedido
        bus = InMemoryEventBus()
        uc = GenerarComprobanteUseCase(repo, bus)
        comp = await uc.execute(GenerarComprobanteCommand(
            pedido_id=pedido_id,
            tipo=TipoComprobante.BOLETA,
            monto=Decimal("75.00"),
            emitido_por="vendedor-1",
            rol_emisor="VENDEDOR",
        ))
        assert comp.estado == EstadoComprobante.PENDIENTE_VALIDACION
        assert bus.fue_publicado("comprobante.pendiente_validacion")

    async def test_vendedor_pendiente_validacion_monto_alto(self, repo_con_pedido):
        """Incluso con monto alto, VENDEDOR pasa por PENDIENTE_VALIDACION."""
        repo, pedido_id = repo_con_pedido
        bus = InMemoryEventBus()
        uc = GenerarComprobanteUseCase(repo, bus)
        comp = await uc.execute(GenerarComprobanteCommand(
            pedido_id=pedido_id,
            tipo=TipoComprobante.FACTURA,
            monto=Decimal("5000.00"),
            emitido_por="vendedor-2",
            rol_emisor="VENDEDOR",
            ruc_cliente="20123456789",
        ))
        assert comp.estado == EstadoComprobante.PENDIENTE_VALIDACION

    async def test_vendedor_pendiente_validacion_boleta(self, repo_con_pedido):
        """VENDEDOR con boleta también pasa por PENDIENTE_VALIDACION."""
        repo, pedido_id = repo_con_pedido
        bus = InMemoryEventBus()
        uc = GenerarComprobanteUseCase(repo, bus)
        comp = await uc.execute(GenerarComprobanteCommand(
            pedido_id=pedido_id,
            tipo=TipoComprobante.BOLETA,
            monto=Decimal("15.00"),
            emitido_por="vendedor-3",
            rol_emisor="VENDEDOR",
        ))
        assert comp.estado == EstadoComprobante.PENDIENTE_VALIDACION

    async def test_administrador_genera_pendiente_validacion_tambien(self, repo_con_pedido):
        """
        ADMINISTRADOR genera PENDIENTE_VALIDACION (estado inicial siempre).
        La diferencia es que ADMINISTRADOR puede aprobar directamente después.
        """
        repo, pedido_id = repo_con_pedido
        bus = InMemoryEventBus()
        uc = GenerarComprobanteUseCase(repo, bus)
        comp = await uc.execute(GenerarComprobanteCommand(
            pedido_id=pedido_id,
            tipo=TipoComprobante.BOLETA,
            monto=Decimal("50.00"),
            emitido_por="admin-1",
            rol_emisor="ADMINISTRADOR",
        ))
        assert comp.estado == EstadoComprobante.PENDIENTE_VALIDACION
        # ADMINISTRADOR no publica el evento de validación
        assert not bus.fue_publicado("comprobante.pendiente_validacion")

    async def test_flujo_completo_vendedor_a_emitido(self, repo_con_pedido):
        """VENDEDOR genera → ADMINISTRADOR aprueba → EMITIDO."""
        repo, pedido_id = repo_con_pedido
        bus = InMemoryEventBus()

        # Paso 1: VENDEDOR genera
        gen_uc = GenerarComprobanteUseCase(repo, bus)
        comp = await gen_uc.execute(GenerarComprobanteCommand(
            pedido_id=pedido_id,
            tipo=TipoComprobante.BOLETA,
            monto=Decimal("75.00"),
            emitido_por="vendedor-1",
            rol_emisor="VENDEDOR",
        ))
        assert comp.estado == EstadoComprobante.PENDIENTE_VALIDACION
        assert bus.fue_publicado("comprobante.pendiente_validacion")

        # Paso 2: ADMINISTRADOR aprueba
        apr_uc = AprobarComprobanteUseCase(repo, bus)
        comp_aprobado = await apr_uc.execute(AprobarComprobanteCommand(
            comprobante_id=comp.id,
            actor_id="admin-1",
        ))
        assert comp_aprobado.estado == EstadoComprobante.EMITIDO
        assert comp_aprobado.esta_emitido() is True

    async def test_flujo_con_anulacion(self, repo_con_pedido):
        """Comprobante EMITIDO puede anularse con nota de crédito."""
        repo, pedido_id = repo_con_pedido
        bus = InMemoryEventBus()

        gen_uc = GenerarComprobanteUseCase(repo, bus)
        comp = await gen_uc.execute(GenerarComprobanteCommand(
            pedido_id=pedido_id,
            tipo=TipoComprobante.BOLETA,
            monto=Decimal("50.00"),
            emitido_por="vendedor-1",
            rol_emisor="VENDEDOR",
        ))
        apr_uc = AprobarComprobanteUseCase(repo, bus)
        await apr_uc.execute(AprobarComprobanteCommand(comprobante_id=comp.id, actor_id="admin-1"))

        anu_uc = AnularComprobanteUseCase(repo)
        comp_anulado = await anu_uc.execute(AnularComprobanteCommand(
            comprobante_id=comp.id, actor_id="admin-1"
        ))
        assert comp_anulado.estado == EstadoComprobante.ANULADO
        assert comp_anulado.nota_credito_id is not None


class TestComprobanteFlujoAPI:
    """Tests via API HTTP para el flujo de comprobante."""

    async def test_vendedor_via_api_siempre_pendiente(self, pedidos_client):
        crear = await pedidos_client.post("/v1/pedidos", json={"canal_origen": "presencial", "items": []})
        pedido_id = crear.json()["data"]["pedido_id"]

        response = await pedidos_client.post(
            f"/v1/pedidos/{pedido_id}/comprobante",
            json={
                "tipo": "boleta",
                "monto": "75.00",
                "emitido_por": "vendedor-1",
                "rol_emisor": "VENDEDOR",
            },
        )
        assert response.status_code == 201
        assert response.json()["data"]["estado"] == "PENDIENTE_VALIDACION"

    async def test_aprobar_via_api(self, pedidos_client):
        crear = await pedidos_client.post("/v1/pedidos", json={"canal_origen": "presencial", "items": []})
        pedido_id = crear.json()["data"]["pedido_id"]

        gen = await pedidos_client.post(
            f"/v1/pedidos/{pedido_id}/comprobante",
            json={"tipo": "boleta", "monto": "50.00", "emitido_por": "v", "rol_emisor": "VENDEDOR"},
        )
        comp_id = gen.json()["data"]["comprobante_id"]
        response = await pedidos_client.post(f"/v1/comprobantes/{comp_id}/aprobar")
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "EMITIDO"

    async def test_aprobar_dos_veces_falla(self, pedidos_client):
        crear = await pedidos_client.post("/v1/pedidos", json={"canal_origen": "presencial", "items": []})
        pedido_id = crear.json()["data"]["pedido_id"]
        gen = await pedidos_client.post(
            f"/v1/pedidos/{pedido_id}/comprobante",
            json={"tipo": "boleta", "monto": "50.00", "emitido_por": "v", "rol_emisor": "VENDEDOR"},
        )
        comp_id = gen.json()["data"]["comprobante_id"]
        await pedidos_client.post(f"/v1/comprobantes/{comp_id}/aprobar")
        response = await pedidos_client.post(f"/v1/comprobantes/{comp_id}/aprobar")
        assert response.status_code == 422

    async def test_anular_via_api(self, pedidos_client):
        crear = await pedidos_client.post("/v1/pedidos", json={"canal_origen": "presencial", "items": []})
        pedido_id = crear.json()["data"]["pedido_id"]
        gen = await pedidos_client.post(
            f"/v1/pedidos/{pedido_id}/comprobante",
            json={"tipo": "boleta", "monto": "50.00", "emitido_por": "v", "rol_emisor": "VENDEDOR"},
        )
        comp_id = gen.json()["data"]["comprobante_id"]
        await pedidos_client.post(f"/v1/comprobantes/{comp_id}/aprobar")
        response = await pedidos_client.post(f"/v1/comprobantes/{comp_id}/anular")
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "ANULADO"

    async def test_aprobar_inexistente(self, pedidos_client):
        response = await pedidos_client.post("/v1/comprobantes/id-99999/aprobar")
        assert response.status_code == 404

    async def test_anular_inexistente(self, pedidos_client):
        response = await pedidos_client.post("/v1/comprobantes/id-99999/anular")
        assert response.status_code == 404

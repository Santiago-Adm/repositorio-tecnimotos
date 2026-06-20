"""
Suite de contrato LSP: TallerPedidosPort (04 §6.2).
Valida que InMemoryTallerPedidosService e implementación real (TallerPedidosServiceImpl)
siguen el mismo contrato de comportamiento.
Protocol: TallerPedidosPort (03 §8.2).
"""
import pytest

from src.pedidos.infrastructure.adapters.taller_pedidos_adapter import (
    InMemoryTallerPedidosService,
    TallerPedidosServiceImpl,
)
from src.pedidos.infrastructure.repositories.pedido_repository_inmemory import (
    InMemoryPedidoRepository,
)
from src.pedidos.domain.models.pedido import EstadoPedido, Pedido


async def _repo_con_pedido_confirmado(ot_id: str) -> InMemoryPedidoRepository:
    repo = InMemoryPedidoRepository()
    pedido = Pedido(canal_origen="taller", origen_actor="m-1", ot_id=ot_id)
    pedido.confirmar()
    await repo.guardar(pedido)
    return repo


async def _repo_con_pedido_borrador(ot_id: str) -> InMemoryPedidoRepository:
    repo = InMemoryPedidoRepository()
    pedido = Pedido(canal_origen="taller", origen_actor="m-1", ot_id=ot_id)
    await repo.guardar(pedido)
    return repo


@pytest.fixture(params=["inmemory", "real"])
async def service_confirmado(request):
    """Fixture con cobro confirmado."""
    ot_id = "ot-cobrado-001"

    if request.param == "inmemory":
        svc = InMemoryTallerPedidosService()
        svc.registrar_cobro(ot_id, confirmado=True)
        return svc, ot_id

    repo = await _repo_con_pedido_confirmado(ot_id)
    return TallerPedidosServiceImpl(repo), ot_id


@pytest.fixture(params=["inmemory", "real"])
async def service_no_confirmado(request):
    """Fixture con cobro pendiente."""
    ot_id = "ot-pendiente-001"

    if request.param == "inmemory":
        svc = InMemoryTallerPedidosService()
        return svc, ot_id

    repo = await _repo_con_pedido_borrador(ot_id)
    return TallerPedidosServiceImpl(repo), ot_id


# ── Casos de contrato — deben pasar en AMBAS implementaciones ─────────────────

@pytest.mark.asyncio
async def test_cobro_confirmado_retorna_true(service_confirmado):
    service, ot_id = service_confirmado
    result = await service.verificar_cobro_confirmado(ot_id)
    assert result is True


@pytest.mark.asyncio
async def test_cobro_no_confirmado_retorna_false(service_no_confirmado):
    service, ot_id = service_no_confirmado
    result = await service.verificar_cobro_confirmado(ot_id)
    assert result is False


@pytest.mark.asyncio
async def test_ot_inexistente_retorna_false(service_no_confirmado):
    service, _ = service_no_confirmado
    result = await service.verificar_cobro_confirmado("ot-inexistente-999")
    assert result is False


@pytest.mark.asyncio
async def test_retorno_es_tipo_bool(service_confirmado):
    service, ot_id = service_confirmado
    result = await service.verificar_cobro_confirmado(ot_id)
    assert isinstance(result, bool)

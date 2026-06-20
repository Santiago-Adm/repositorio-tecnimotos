"""
Suite de contrato LSP: StockPedidosPort (04 §6.2).
Valida que InMemoryStockService e implementación real (StockServiceImpl)
siguen el mismo contrato de comportamiento.
Protocol: StockPedidosPort (03 §8.2, Contrato 3).
"""
import pytest
from decimal import Decimal

from src.stock.domain.models.stock import StockNoEncontradoError, StockRepuesto
from src.stock.domain.ports.stock_pedidos_port import DisponibilidadResponse
from src.stock.infrastructure.adapters.stock_service_impl import (
    InMemoryStockService,
    StockServiceImpl,
)
from src.stock.infrastructure.repositories.stock_repository_inmemory import (
    InMemoryStockRepository,
)


async def _repo_con_stock(repuesto_id: str, cantidad: int) -> InMemoryStockRepository:
    repo = InMemoryStockRepository()
    await repo.guardar(
        StockRepuesto(repuesto_id=repuesto_id, codigo="REP-001", cantidad_disponible=cantidad)
    )
    return repo


@pytest.fixture(params=["inmemory", "real"])
async def service(request):
    """Fixture parametrizado — misma suite corre sobre Fake y implementación real."""
    repuesto_id = "rp-contrato-001"
    cantidad_inicial = 10

    if request.param == "inmemory":
        svc = InMemoryStockService()
        svc.agregar_stock(repuesto_id, cantidad_inicial)
        return svc

    repo = await _repo_con_stock(repuesto_id, cantidad_inicial)
    return StockServiceImpl(repo)


# ── Casos de contrato — deben pasar en AMBAS implementaciones ─────────────────

@pytest.mark.asyncio
async def test_consultar_disponibilidad_repuesto_existente(service):
    result = await service.consultar_disponibilidad("rp-contrato-001")
    assert isinstance(result, DisponibilidadResponse)
    assert result.repuesto_id == "rp-contrato-001"
    assert result.cantidad_disponible == 10


@pytest.mark.asyncio
async def test_consultar_disponibilidad_repuesto_inexistente_lanza(service):
    with pytest.raises(StockNoEncontradoError):
        await service.consultar_disponibilidad("rp-inexistente-999")


@pytest.mark.asyncio
async def test_apartar_stock_exitoso(service):
    resultado = await service.apartar_stock(
        repuesto_id="rp-contrato-001",
        cantidad=3,
        actor_id="actor-test",
        referencia_id="ref-test",
    )
    assert resultado is True


@pytest.mark.asyncio
async def test_apartar_stock_insuficiente_retorna_false(service):
    resultado = await service.apartar_stock(
        repuesto_id="rp-contrato-001",
        cantidad=999,
        actor_id="actor-test",
        referencia_id="ref-test",
    )
    assert resultado is False


@pytest.mark.asyncio
async def test_liberar_stock_tras_apartar(service):
    await service.apartar_stock("rp-contrato-001", 5, "actor-test", "ref-1")
    resultado = await service.liberar_stock("rp-contrato-001", 5, "actor-test", "ref-1")
    assert resultado is True


@pytest.mark.asyncio
async def test_retorno_disponibilidad_es_tipo_correcto(service):
    result = await service.consultar_disponibilidad("rp-contrato-001")
    assert isinstance(result.cantidad_disponible, int)
    assert isinstance(result.repuesto_id, str)

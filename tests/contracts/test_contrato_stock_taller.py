"""
Suite de contrato LSP: StockTallerPort (04 §6.2).
Valida que InMemoryStockTallerAdapter e implementación real (StockTallerServiceImpl)
siguen el mismo contrato de comportamiento.
Protocol: StockTallerPort (03 §8.2).
"""
import pytest

from src.stock.domain.models.stock import StockRepuesto
from src.stock.infrastructure.adapters.stock_taller_impl import StockTallerServiceImpl
from src.stock.infrastructure.repositories.stock_repository_inmemory import (
    InMemoryStockRepository,
)
from src.taller.domain.ports.stock_taller_port import DisponibilidadOTResponse
from src.taller.infrastructure.adapters.catalogo_taller_adapter import (
    InMemoryStockTallerAdapter,
)


async def _repo_con_stock(repuesto_id: str, disponible: int, apartado: int = 3) -> InMemoryStockRepository:
    repo = InMemoryStockRepository()
    await repo.guardar(
        StockRepuesto(
            repuesto_id=repuesto_id,
            codigo="REP-OT-001",
            cantidad_disponible=disponible,
            cantidad_apartada=apartado,
        )
    )
    return repo


@pytest.fixture(params=["inmemory", "real"])
async def service(request):
    """Fixture parametrizado — misma suite corre sobre Fake e implementación real."""
    repuesto_id = "rp-taller-001"
    disponible = 7
    apartado = 3

    if request.param == "inmemory":
        svc = InMemoryStockTallerAdapter()
        svc.establecer_stock(repuesto_id, disponible=disponible, apartado=apartado)
        return svc

    repo = await _repo_con_stock(repuesto_id, disponible, apartado)
    return StockTallerServiceImpl(repo)


# ── Casos de contrato — deben pasar en AMBAS implementaciones ─────────────────

@pytest.mark.asyncio
async def test_verificar_disponibilidad_ot_retorna_tipo_correcto(service):
    result = await service.verificar_disponibilidad_ot("rp-taller-001")
    assert isinstance(result, DisponibilidadOTResponse)
    assert isinstance(result.repuesto_id, str)
    assert isinstance(result.cantidad_disponible, int)
    assert isinstance(result.cantidad_apartada, int)


@pytest.mark.asyncio
async def test_verificar_disponibilidad_ot_valores_correctos(service):
    result = await service.verificar_disponibilidad_ot("rp-taller-001")
    assert result.repuesto_id == "rp-taller-001"
    assert result.cantidad_disponible == 7
    assert result.cantidad_apartada == 3


@pytest.mark.asyncio
async def test_consultar_apartado_retorna_int(service):
    result = await service.consultar_apartado("rp-taller-001")
    assert isinstance(result, int)


@pytest.mark.asyncio
async def test_consultar_apartado_valor_correcto(service):
    result = await service.consultar_apartado("rp-taller-001")
    assert result == 3


@pytest.mark.asyncio
async def test_repuesto_inexistente_retorna_cero_apartado(service):
    result = await service.consultar_apartado("rp-inexistente-999")
    assert result == 0

"""
Suite de contrato LSP: CatalogoPedidosPort (04 §6.2).
Valida que InMemoryCatalogoService e implementación real siguen el mismo contrato.
"""
import pytest
from decimal import Decimal

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    RepuestoDadoDeBajaError,
    RepuestoNoEncontradoError,
    UniversoRepuesto,
)
from src.catalogo.domain.ports.catalogo_pedidos_port import PrecioVigenteResponse
from src.catalogo.infrastructure.adapters.catalogo_service_impl import (
    CatalogoServiceImpl,
    InMemoryCatalogoService,
)
from src.catalogo.infrastructure.repositories.repuesto_repository_inmemory import (
    InMemoryRepuestoRepository,
)


def _repuesto_fixture() -> Repuesto:
    return Repuesto(
        codigo="REP-001",
        nombre="Filtro",
        universo=UniversoRepuesto.MOTOTAXI,
        modelo="Bajaj RE",
        año=2019,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("45.00"),
    )


def _precio_vigente_fixture() -> PrecioVigenteResponse:
    r = _repuesto_fixture()
    return PrecioVigenteResponse(
        repuesto_id=r.id,
        codigo=r.codigo,
        precio_venta=r.precio_venta,
        nombre=r.nombre,
        categoria=r.categoria.value,
        universo=r.universo.value,
        activo=r.activo,
    )


@pytest.fixture(params=["inmemory", "real"])
async def service(request):
    """Fixture parametrizado — misma suite corre sobre Fake y real."""
    if request.param == "inmemory":
        svc = InMemoryCatalogoService()
        svc.agregar_repuesto(_precio_vigente_fixture())
        return svc
    repo = InMemoryRepuestoRepository()
    await repo.guardar(_repuesto_fixture())
    return CatalogoServiceImpl(repo)


# ── Casos de contrato — deben pasar en AMBAS implementaciones ─────────────────

@pytest.mark.asyncio
async def test_obtener_precio_codigo_existente(service):
    result = await service.obtener_precio_vigente("REP-001")
    assert result.codigo == "REP-001"
    assert result.precio_venta == Decimal("45.00")
    assert result.activo is True


@pytest.mark.asyncio
async def test_obtener_precio_codigo_inexistente_lanza(service):
    with pytest.raises(RepuestoNoEncontradoError):
        await service.obtener_precio_vigente("REP-999")


@pytest.mark.asyncio
async def test_verificar_existencia_codigo_existente(service):
    result = await service.verificar_existencia("REP-001")
    assert result is True


@pytest.mark.asyncio
async def test_verificar_existencia_codigo_inexistente(service):
    result = await service.verificar_existencia("REP-999")
    assert result is False


@pytest.mark.asyncio
async def test_precio_vigente_retorna_tipo_correcto(service):
    result = await service.obtener_precio_vigente("REP-001")
    assert isinstance(result, PrecioVigenteResponse)
    assert isinstance(result.precio_venta, Decimal)

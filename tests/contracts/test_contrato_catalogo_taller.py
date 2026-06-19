"""
Suite de contrato LSP: CatalogoTallerPort (04 §6.2).
"""
import pytest
from decimal import Decimal

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
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
        codigo="REP-OT-001",
        nombre="Bujia TVS",
        universo=UniversoRepuesto.MOTOTAXI,
        modelo="TVS King",
        año=2020,
        categoria=CategoriaRepuesto.ELECTRICO,
        precio_venta=Decimal("25.00"),
    )


@pytest.fixture(params=["inmemory", "real"])
async def service(request):
    """Fixture parametrizado — misma suite corre sobre Fake y real."""
    r = _repuesto_fixture()
    if request.param == "inmemory":
        svc = InMemoryCatalogoService()
        svc.agregar_repuesto(
            PrecioVigenteResponse(
                repuesto_id=r.id,
                codigo=r.codigo,
                precio_venta=r.precio_venta,
                nombre=r.nombre,
                categoria=r.categoria.value,
                universo=r.universo.value,
                activo=r.activo,
            )
        )
        return svc
    repo = InMemoryRepuestoRepository()
    await repo.guardar(r)
    return CatalogoServiceImpl(repo)


@pytest.mark.asyncio
async def test_obtener_precio_para_ot_existente(service):
    result = await service.obtener_precio_para_ot("REP-OT-001")
    assert isinstance(result, PrecioVigenteResponse)
    assert result.precio_venta == Decimal("25.00")


@pytest.mark.asyncio
async def test_obtener_precio_para_ot_inexistente_lanza(service):
    with pytest.raises(RepuestoNoEncontradoError):
        await service.obtener_precio_para_ot("REP-999")

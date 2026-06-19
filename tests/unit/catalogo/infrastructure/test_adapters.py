"""
Tests unitarios — CatalogoServiceImpl e InMemoryCatalogoService (04 §4.2).
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


def _repuesto() -> Repuesto:
    return Repuesto(
        codigo="REP-001",
        nombre="Filtro",
        universo=UniversoRepuesto.MOTOTAXI,
        modelo="Bajaj RE",
        año=2019,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("45.00"),
    )


class TestCatalogoServiceImpl:
    @pytest.mark.asyncio
    async def test_obtener_precio_vigente(self):
        repo = InMemoryRepuestoRepository()
        await repo.guardar(_repuesto())
        svc = CatalogoServiceImpl(repo)

        result = await svc.obtener_precio_vigente("REP-001")
        assert isinstance(result, PrecioVigenteResponse)
        assert result.precio_venta == Decimal("45.00")
        assert result.activo is True

    @pytest.mark.asyncio
    async def test_obtener_precio_vigente_inexistente_lanza(self):
        repo = InMemoryRepuestoRepository()
        svc = CatalogoServiceImpl(repo)
        with pytest.raises(RepuestoNoEncontradoError):
            await svc.obtener_precio_vigente("REP-999")

    @pytest.mark.asyncio
    async def test_verificar_existencia_existente(self):
        repo = InMemoryRepuestoRepository()
        await repo.guardar(_repuesto())
        svc = CatalogoServiceImpl(repo)
        assert await svc.verificar_existencia("REP-001") is True

    @pytest.mark.asyncio
    async def test_verificar_existencia_no_existe(self):
        repo = InMemoryRepuestoRepository()
        svc = CatalogoServiceImpl(repo)
        assert await svc.verificar_existencia("REP-999") is False

    @pytest.mark.asyncio
    async def test_verificar_existencia_dado_de_baja(self):
        repo = InMemoryRepuestoRepository()
        r = _repuesto()
        r.dar_de_baja("test")
        await repo.guardar(r)
        svc = CatalogoServiceImpl(repo)
        assert await svc.verificar_existencia("REP-001") is False

    @pytest.mark.asyncio
    async def test_obtener_precio_para_ot(self):
        repo = InMemoryRepuestoRepository()
        await repo.guardar(_repuesto())
        svc = CatalogoServiceImpl(repo)
        result = await svc.obtener_precio_para_ot("REP-001")
        assert result.codigo == "REP-001"


class TestInMemoryCatalogoService:
    @pytest.mark.asyncio
    async def test_agregar_y_obtener(self):
        r = _repuesto()
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
        result = await svc.obtener_precio_vigente("REP-001")
        assert result.codigo == "REP-001"

    @pytest.mark.asyncio
    async def test_inexistente_lanza(self):
        svc = InMemoryCatalogoService()
        with pytest.raises(RepuestoNoEncontradoError):
            await svc.obtener_precio_vigente("REP-999")

    @pytest.mark.asyncio
    async def test_verificar_existencia(self):
        r = _repuesto()
        svc = InMemoryCatalogoService()
        svc.agregar_repuesto(
            PrecioVigenteResponse(
                repuesto_id=r.id, codigo=r.codigo, precio_venta=r.precio_venta,
                nombre=r.nombre, categoria=r.categoria.value,
                universo=r.universo.value, activo=r.activo,
            )
        )
        assert await svc.verificar_existencia("REP-001") is True
        assert await svc.verificar_existencia("REP-999") is False

    @pytest.mark.asyncio
    async def test_obtener_precio_para_ot(self):
        r = _repuesto()
        svc = InMemoryCatalogoService()
        svc.agregar_repuesto(
            PrecioVigenteResponse(
                repuesto_id=r.id, codigo=r.codigo, precio_venta=r.precio_venta,
                nombre=r.nombre, categoria=r.categoria.value,
                universo=r.universo.value, activo=r.activo,
            )
        )
        result = await svc.obtener_precio_para_ot("REP-001")
        assert result.codigo == "REP-001"

"""
Tests unitarios — InMemoryRepuestoRepository (04 §4.2).
Verifica la implementación Fake contra el contrato del puerto.
"""
import pytest
from decimal import Decimal

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    UniversoRepuesto,
)
from src.catalogo.infrastructure.repositories.repuesto_repository_inmemory import (
    InMemoryRepuestoRepository,
)


@pytest.fixture
def repo() -> InMemoryRepuestoRepository:
    return InMemoryRepuestoRepository()


@pytest.fixture
def repuesto() -> Repuesto:
    return Repuesto(
        codigo="REP-001",
        nombre="Filtro",
        universo=UniversoRepuesto.MOTOTAXI_3R,
        modelo="Bajaj RE",
        año=2019,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("45.00"),
    )


@pytest.mark.asyncio
async def test_guardar_y_obtener_por_codigo(repo, repuesto):
    await repo.guardar(repuesto)
    encontrado = await repo.obtener_por_codigo("REP-001")
    assert encontrado is not None
    assert encontrado.codigo == "REP-001"


@pytest.mark.asyncio
async def test_obtener_por_codigo_inexistente_retorna_none(repo):
    resultado = await repo.obtener_por_codigo("REP-999")
    assert resultado is None


@pytest.mark.asyncio
async def test_obtener_por_id(repo, repuesto):
    await repo.guardar(repuesto)
    encontrado = await repo.obtener_por_id(repuesto.id)
    assert encontrado is not None
    assert encontrado.id == repuesto.id


@pytest.mark.asyncio
async def test_obtener_por_id_inexistente_retorna_none(repo):
    assert await repo.obtener_por_id("no-existe") is None


@pytest.mark.asyncio
async def test_buscar_por_universo(repo, repuesto):
    repuesto_ml = Repuesto(
        codigo="REP-100",
        nombre="Cadena",
        universo=UniversoRepuesto.MOTOLINEAL,
        modelo="TVS",
        año=2022,
        categoria=CategoriaRepuesto.TRANSMISION,
        precio_venta=Decimal("85.00"),
    )
    await repo.guardar(repuesto)
    await repo.guardar(repuesto_ml)

    result = await repo.buscar(UniversoRepuesto.MOTOTAXI_3R)
    assert len(result) == 1
    assert result[0].codigo == "REP-001"


@pytest.mark.asyncio
async def test_buscar_filtra_dados_de_baja(repo, repuesto):
    repuesto.dar_de_baja("test")
    await repo.guardar(repuesto)
    result = await repo.buscar(UniversoRepuesto.MOTOTAXI_3R)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_buscar_por_modelo(repo, repuesto):
    await repo.guardar(repuesto)
    result = await repo.buscar(UniversoRepuesto.MOTOTAXI_3R, modelo="Bajaj")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_buscar_por_año(repo, repuesto):
    await repo.guardar(repuesto)
    result = await repo.buscar(UniversoRepuesto.MOTOTAXI_3R, año=2019)
    assert len(result) == 1
    result_vacio = await repo.buscar(UniversoRepuesto.MOTOTAXI_3R, año=2025)
    assert len(result_vacio) == 0


@pytest.mark.asyncio
async def test_buscar_por_lista_codigos(repo, repuesto):
    await repo.guardar(repuesto)
    result = await repo.buscar_por_lista_codigos(["REP-001", "REP-999"])
    assert len(result) == 1
    assert result[0].codigo == "REP-001"


@pytest.mark.asyncio
async def test_buscar_por_lista_codigos_con_universo(repo, repuesto):
    await repo.guardar(repuesto)
    result = await repo.buscar_por_lista_codigos(
        ["REP-001"], universo=UniversoRepuesto.MOTOLINEAL
    )
    assert len(result) == 0


@pytest.mark.asyncio
async def test_actualizar_repuesto(repo, repuesto):
    await repo.guardar(repuesto)
    repuesto.actualizar_precio(Decimal("60.00"), "admin")
    updated = await repo.actualizar(repuesto)
    assert updated.precio_venta == Decimal("60.00")


@pytest.mark.asyncio
async def test_actualizar_repuesto_inexistente_lanza(repo, repuesto):
    with pytest.raises(ValueError):
        await repo.actualizar(repuesto)


@pytest.mark.asyncio
async def test_obtener_historial_precio(repo, repuesto):
    await repo.guardar(repuesto)
    repuesto.actualizar_precio(Decimal("55.00"), "admin")
    await repo.actualizar(repuesto)

    historial = await repo.obtener_historial_precio(repuesto.id)
    assert len(historial) == 1
    assert historial[0].precio_nuevo == Decimal("55.00")


@pytest.mark.asyncio
async def test_obtener_historial_vacio(repo, repuesto):
    await repo.guardar(repuesto)
    historial = await repo.obtener_historial_precio(repuesto.id)
    assert historial == []


@pytest.mark.asyncio
async def test_contar_disponibles_activo(repo, repuesto):
    await repo.guardar(repuesto)
    count = await repo.contar_disponibles(repuesto.id)
    assert count == 1


@pytest.mark.asyncio
async def test_contar_disponibles_inactivo(repo, repuesto):
    repuesto.dar_de_baja("test")
    await repo.guardar(repuesto)
    count = await repo.contar_disponibles(repuesto.id)
    assert count == 0


@pytest.mark.asyncio
async def test_contar_disponibles_no_existe(repo):
    count = await repo.contar_disponibles("no-existe")
    assert count == 0


def test_limpiar(repo):
    repo._store["dummy"] = None  # type: ignore[assignment]
    repo.limpiar()
    assert len(repo._store) == 0

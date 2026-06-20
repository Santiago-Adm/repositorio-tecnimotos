"""Fixtures compartidos para tests unitarios del módulo taller."""
import pytest
from decimal import Decimal

from src.taller.domain.models.orden_trabajo import (
    Entrada,
    ListaRepuestosOT,
    Mecanico,
    ModalidadIntervencion,
    NivelMecanico,
    NivelUrgencia,
    OrdenTrabajo,
    Vehiculo,
)
from src.taller.infrastructure.repositories.taller_repository_inmemory import (
    InMemoryTallerRepository,
)
from src.taller.infrastructure.adapters.catalogo_taller_adapter import (
    InMemoryCatalogoTallerAdapter,
)
from src.taller.domain.ports.catalogo_taller_port import RepuestoInfoTaller
from src.shared.events.event_bus import InMemoryEventBus


@pytest.fixture
async def repo() -> InMemoryTallerRepository:
    r = InMemoryTallerRepository()
    vehiculo = Vehiculo(universo="mototaxi", modelo="Bajaj RE", año=2020)
    await r.guardar_vehiculo(vehiculo)
    mecanico = Mecanico(usuario_id="u-master", nivel=NivelMecanico.MASTER)
    await r.guardar_mecanico(mecanico)
    r._vehiculo_id = vehiculo.id
    r._mecanico_id = mecanico.id
    return r


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def catalogo_taller() -> InMemoryCatalogoTallerAdapter:
    adapter = InMemoryCatalogoTallerAdapter()
    adapter.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-001",
        codigo="REP-001",
        precio_venta=Decimal("45.00"),
        nombre="Filtro aceite",
        activo=True,
    ))
    adapter.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-002",
        codigo="REP-002",
        precio_venta=Decimal("25.00"),
        nombre="Bujía",
        activo=True,
    ))
    adapter.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-caro",
        codigo="REP-CARO",
        precio_venta=Decimal("150.00"),
        nombre="Sensor ABS",
        activo=True,
    ))
    adapter.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-medio",
        codigo="REP-MEDIO",
        precio_venta=Decimal("65.00"),
        nombre="Rodamiento",
        activo=True,
    ))
    return adapter


@pytest.fixture
def ot_abierta(repo) -> OrdenTrabajo:
    ot = OrdenTrabajo(
        vehiculo_id=repo._vehiculo_id,
        mecanico_master_id=repo._mecanico_id,
        modalidad=ModalidadIntervencion.CORRECTIVO,
        urgencia=NivelUrgencia.ALTA,
    )
    return ot


@pytest.fixture
def item_barato() -> ListaRepuestosOT:
    return ListaRepuestosOT(
        orden_trabajo_id="ot-1",
        repuesto_id="rp-001",
        codigo="REP-001",
        cantidad=1,
        precio_unitario=Decimal("25.00"),
        momento_agregado="inicial",
    )


@pytest.fixture
def item_costoso() -> ListaRepuestosOT:
    return ListaRepuestosOT(
        orden_trabajo_id="ot-1",
        repuesto_id="rp-caro",
        codigo="REP-CARO",
        cantidad=1,
        precio_unitario=Decimal("150.00"),
        momento_agregado="en_ejecucion",
    )

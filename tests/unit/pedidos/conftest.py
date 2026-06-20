"""Fixtures compartidos para tests unitarios del módulo pedidos."""
import pytest
from decimal import Decimal

from src.pedidos.domain.models.pedido import (
    Pedido,
    PedidoItem,
    Reserva,
    SegmentoCliente,
)
from src.pedidos.infrastructure.repositories.pedido_repository_inmemory import (
    InMemoryPedidoRepository,
)
from src.pedidos.infrastructure.adapters.catalogo_adapter import (
    InMemoryCatalogoAdapter,
    InMemoryStockAdapter,
)
from src.pedidos.domain.ports.catalogo_pedidos_port import RepuestoInfo
from src.shared.events.event_bus import InMemoryEventBus


@pytest.fixture
def repo() -> InMemoryPedidoRepository:
    return InMemoryPedidoRepository()


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def catalogo() -> InMemoryCatalogoAdapter:
    adapter = InMemoryCatalogoAdapter()
    adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id="rp-001",
        codigo="REP-001",
        precio_venta=Decimal("45.00"),
        nombre="Filtro aceite",
        categoria="motor",
        universo="mototaxi",
        activo=True,
    ))
    adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id="rp-002",
        codigo="REP-002",
        precio_venta=Decimal("30.00"),
        nombre="Cadena TVS",
        categoria="transmision",
        universo="motolineal",
        activo=True,
    ))
    adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id="rp-003",
        codigo="REP-003",
        precio_venta=Decimal("80.00"),
        nombre="Freno delantero",
        categoria="frenos",
        universo="mototaxi",
        activo=False,
    ))
    return adapter


@pytest.fixture
def stock() -> InMemoryStockAdapter:
    adapter = InMemoryStockAdapter()
    adapter.establecer_stock("rp-001", 10)
    adapter.establecer_stock("rp-002", 5)
    return adapter


@pytest.fixture
def pedido_borrador() -> Pedido:
    pedido = Pedido(canal_origen="presencial", origen_actor="vendedor-1")
    item = PedidoItem(
        pedido_id=pedido.id,
        repuesto_id="rp-001",
        codigo="REP-001",
        cantidad=2,
        precio_unitario=Decimal("45.00"),
    )
    pedido.items.append(item)
    pedido._recalcular_total()
    return pedido


@pytest.fixture
def reserva_conductor() -> Reserva:
    return Reserva(
        cliente_id="cli-001",
        repuesto_id="rp-001",
        cantidad=3,
        segmento=SegmentoCliente.CONDUCTOR,
    )

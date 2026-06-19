"""Fixtures compartidos para tests unitarios del módulo stock."""
import pytest
from decimal import Decimal

from src.stock.domain.models.stock import (
    Reabastecimiento,
    ReabastecimientoItem,
    StockRepuesto,
)
from src.stock.infrastructure.repositories.stock_repository_inmemory import (
    InMemoryStockRepository,
)
from src.shared.events.event_bus import InMemoryEventBus


@pytest.fixture
def repo() -> InMemoryStockRepository:
    return InMemoryStockRepository()


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def stock_filtro() -> StockRepuesto:
    return StockRepuesto(
        repuesto_id="rp-001",
        codigo="REP-001",
        cantidad_disponible=20,
        cantidad_apartada=0,
        cantidad_en_transito=5,
        umbral_minimo=5,
    )


@pytest.fixture
def stock_cadena() -> StockRepuesto:
    return StockRepuesto(
        repuesto_id="rp-002",
        codigo="REP-002",
        cantidad_disponible=3,
        cantidad_apartada=2,
        umbral_minimo=5,
    )


@pytest.fixture
def stock_agotado() -> StockRepuesto:
    return StockRepuesto(
        repuesto_id="rp-003",
        codigo="REP-003",
        cantidad_disponible=0,
        umbral_minimo=2,
    )


@pytest.fixture
def reab_basico() -> Reabastecimiento:
    reab = Reabastecimiento(proveedor="Bajaj Perú", solicitado_por="user-1")
    reab.agregar_item(
        ReabastecimientoItem(
            repuesto_id="rp-001",
            codigo="REP-001",
            cantidad_solicitada=10,
            precio_costo_unitario=Decimal("30.00"),
        )
    )
    return reab

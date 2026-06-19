"""Fixtures compartidos para tests unitarios del módulo catalogo."""
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
from src.shared.events.event_bus import InMemoryEventBus


@pytest.fixture
def repo() -> InMemoryRepuestoRepository:
    return InMemoryRepuestoRepository()


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def repuesto_mototaxi() -> Repuesto:
    return Repuesto(
        codigo="REP-001",
        nombre="Filtro de aceite Bajaj RE",
        universo=UniversoRepuesto.MOTOTAXI,
        modelo="Bajaj RE",
        año=2019,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("45.00"),
        descripcion="Filtro original Bajaj",
    )


@pytest.fixture
def repuesto_tecnico_especializado() -> Repuesto:
    return Repuesto(
        codigo="REP-060",
        nombre="Sensor ABS especializado",
        universo=UniversoRepuesto.MOTOTAXI,
        modelo="Bajaj RE",
        año=2021,
        categoria=CategoriaRepuesto.TECNICO_ESPECIALIZADO,
        precio_venta=Decimal("120.00"),
    )


@pytest.fixture
def repuesto_motolineal() -> Repuesto:
    return Repuesto(
        codigo="REP-100",
        nombre="Cadena TVS",
        universo=UniversoRepuesto.MOTOLINEAL,
        modelo="TVS Apache",
        año=2022,
        categoria=CategoriaRepuesto.TRANSMISION,
        precio_venta=Decimal("85.00"),
    )

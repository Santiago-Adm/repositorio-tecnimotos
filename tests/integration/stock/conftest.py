"""Fixtures compartidos para tests de integración del módulo stock."""
import pytest
from decimal import Decimal

from src.stock.domain.models.stock import (
    Reabastecimiento,
    ReabastecimientoItem,
    StockRepuesto,
)


@pytest.fixture
async def stock_client(app_client):
    """Cliente con stock precargado para los 8 endpoints EP-STK-01..08."""
    repo = app_client.app.state.stock_repo

    await repo.guardar(StockRepuesto(
        repuesto_id="rp-001",
        codigo="REP-001",
        cantidad_disponible=20,
        cantidad_apartada=0,
        cantidad_en_transito=5,
        umbral_minimo=5,
    ))
    await repo.guardar(StockRepuesto(
        repuesto_id="rp-002",
        codigo="REP-002",
        cantidad_disponible=3,
        cantidad_apartada=2,
        umbral_minimo=5,
    ))
    await repo.guardar(StockRepuesto(
        repuesto_id="rp-003",
        codigo="REP-003",
        cantidad_disponible=0,
        umbral_minimo=2,
    ))

    return app_client

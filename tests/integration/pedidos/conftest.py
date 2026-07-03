"""Fixtures compartidos para tests de integración del módulo pedidos."""
import pytest
from decimal import Decimal

from src.pedidos.domain.ports.catalogo_pedidos_port import RepuestoInfo


@pytest.fixture
async def pedidos_client(app_client):
    """Cliente con datos precargados para tests de pedidos."""
    catalogo_adapter = app_client.app.state.catalogo_adapter
    stock_adapter = app_client.app.state.stock_adapter

    catalogo_adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id="rp-001",
        codigo="REP-001",
        precio_venta=Decimal("45.00"),
        nombre="Filtro aceite",
        categoria="motor",
        universo="mototaxi_3r",
        activo=True,
    ))
    catalogo_adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id="rp-002",
        codigo="REP-002",
        precio_venta=Decimal("30.00"),
        nombre="Cadena",
        categoria="transmision",
        universo="motolineal",
        activo=True,
    ))
    catalogo_adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id="rp-baja",
        codigo="REP-BAJA",
        precio_venta=Decimal("20.00"),
        nombre="Repuesto baja",
        categoria="otro",
        universo="mototaxi_3r",
        activo=False,
    ))

    stock_adapter.establecer_stock("rp-001", 20)
    stock_adapter.establecer_stock("rp-002", 10)

    return app_client

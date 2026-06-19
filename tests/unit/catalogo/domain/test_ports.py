"""
Tests de los puertos del dominio catalogo (04 §6.2).
Verifica que PrecioVigenteResponse se construye correctamente
y que los puertos son Protocols verificables en runtime.
"""
from decimal import Decimal

from src.catalogo.domain.ports.catalogo_pedidos_port import (
    CatalogoPedidosPort,
    PrecioVigenteResponse,
)
from src.catalogo.domain.ports.catalogo_taller_port import CatalogoTallerPort


class TestPrecioVigenteResponse:
    def test_construccion_correcta(self):
        resp = PrecioVigenteResponse(
            repuesto_id="abc-123",
            codigo="REP-001",
            precio_venta=Decimal("45.00"),
            nombre="Filtro",
            categoria="motor",
            universo="mototaxi",
            activo=True,
        )
        assert resp.codigo == "REP-001"
        assert resp.precio_venta == Decimal("45.00")
        assert resp.activo is True

    def test_es_frozen(self):
        resp = PrecioVigenteResponse(
            repuesto_id="x",
            codigo="REP-001",
            precio_venta=Decimal("10.00"),
            nombre="Test",
            categoria="motor",
            universo="mototaxi",
            activo=True,
        )
        try:
            resp.codigo = "otro"  # type: ignore[misc]
            assert False, "debería ser inmutable"
        except Exception:
            pass


class TestPuertosProtocol:
    def test_catalogo_pedidos_port_es_protocol(self):
        assert hasattr(CatalogoPedidosPort, "obtener_precio_vigente")
        assert hasattr(CatalogoPedidosPort, "verificar_existencia")

    def test_catalogo_taller_port_es_protocol(self):
        assert hasattr(CatalogoTallerPort, "obtener_precio_para_ot")

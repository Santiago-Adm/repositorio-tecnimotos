"""
Tests de integración — GET /v1/analitica/stock-radar (Pieza G, sesión
catálogo/UI 2026-07-05). Antes de esta sesión el endpoint no tenía tests.
"""
from decimal import Decimal

from src.catalogo.domain.models.repuesto import Repuesto, UniversoRepuesto
from src.stock.domain.models.stock import StockRepuesto


class TestStockRadar:
    async def test_clasifica_por_nivel_y_categoria(self, app_client):
        catalogo_repo = app_client.app.state.catalogo_repo
        stock_repo = app_client.app.state.stock_repo

        critico = Repuesto(
            codigo="RADAR-CRIT", nombre="Critico", universo=UniversoRepuesto.MOTOTAXI_3R,
            modelo="X", año=None, categoria="motor", precio_venta=Decimal("10.00"),
        )
        bajo = Repuesto(
            codigo="RADAR-BAJO", nombre="Bajo", universo=UniversoRepuesto.MOTOTAXI_3R,
            modelo="X", año=None, categoria="motor", precio_venta=Decimal("10.00"),
        )
        optimo = Repuesto(
            codigo="RADAR-OPT", nombre="Optimo", universo=UniversoRepuesto.MOTOTAXI_3R,
            modelo="X", año=None, categoria="frenos", precio_venta=Decimal("10.00"),
        )
        for r in (critico, bajo, optimo):
            await catalogo_repo.guardar(r)

        # umbral_minimo=10 → CRITICO si disponible <= 5, BAJO si <= 10, si no OPTIMO
        # (regla exacta de StockRepuesto.esta_bajo_umbral + corte CRITICO en //2).
        await stock_repo.guardar(StockRepuesto(repuesto_id=critico.id, codigo="RADAR-CRIT", cantidad_disponible=2, umbral_minimo=10))
        await stock_repo.guardar(StockRepuesto(repuesto_id=bajo.id, codigo="RADAR-BAJO", cantidad_disponible=8, umbral_minimo=10))
        await stock_repo.guardar(StockRepuesto(repuesto_id=optimo.id, codigo="RADAR-OPT", cantidad_disponible=50, umbral_minimo=10))

        response = await app_client.get("/v1/analitica/stock-radar")
        assert response.status_code == 200
        radar = {item["categoria"]: item for item in response.json()["data"]["radar"]}

        assert radar["motor"]["CRITICO"] == 1
        assert radar["motor"]["BAJO"] == 1
        assert radar["motor"]["OPTIMO"] == 0
        assert radar["frenos"]["OPTIMO"] == 1
        assert radar["frenos"]["CRITICO"] == 0

    async def test_umbral_cero_es_siempre_optimo(self, app_client):
        """umbral_minimo=0 desactiva la alerta (regla de negocio ya existente
        en StockRepuesto.esta_bajo_umbral) — nunca debe contar como CRITICO/BAJO."""
        catalogo_repo = app_client.app.state.catalogo_repo
        stock_repo = app_client.app.state.stock_repo

        r = Repuesto(
            codigo="RADAR-SINUMBRAL", nombre="Sin umbral", universo=UniversoRepuesto.MOTOLINEAL,
            modelo="X", año=None, categoria="consumible", precio_venta=Decimal("5.00"),
        )
        await catalogo_repo.guardar(r)
        await stock_repo.guardar(StockRepuesto(repuesto_id=r.id, codigo="RADAR-SINUMBRAL", cantidad_disponible=0, umbral_minimo=0))

        response = await app_client.get("/v1/analitica/stock-radar")
        assert response.status_code == 200
        radar = {item["categoria"]: item for item in response.json()["data"]["radar"]}
        assert radar["consumible"]["OPTIMO"] == 1
        assert radar["consumible"]["CRITICO"] == 0
        assert radar["consumible"]["BAJO"] == 0

    async def test_requiere_rol_admin(self, app_client):
        from tests.integration.conftest import make_test_token
        token = make_test_token(app_client._test_private_pem, "VENDEDOR")
        response = await app_client.get(
            "/v1/analitica/stock-radar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

"""
Tests de integración — API de stock (EP-STK-01 a EP-STK-08).
Usan AsyncClient contra la app FastAPI con repositorios en memoria.
"""
import pytest
from decimal import Decimal

from src.stock.domain.models.stock import EstadoReabastecimiento, StockRepuesto


class TestEPSTK01ConsultarStock:
    async def test_consultar_stock_existente(self, stock_client):
        response = await stock_client.get("/v1/stock/REP-001")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["codigo"] == "REP-001"
        assert data["data"]["cantidad_disponible"] == 20

    async def test_consultar_stock_inexistente(self, stock_client):
        response = await stock_client.get("/v1/stock/NINGUNO")
        assert response.status_code == 404

    async def test_respuesta_incluye_request_id(self, stock_client):
        response = await stock_client.get("/v1/stock/REP-001")
        assert "request_id" in response.json()["meta"]

    async def test_respuesta_incluye_flags_estado(self, stock_client):
        response = await stock_client.get("/v1/stock/REP-003")
        data = response.json()["data"]
        assert data["esta_agotado"] is True
        assert data["esta_bajo_umbral"] is True


class TestEPSTK02ListarStock:
    async def test_listar_devuelve_todos(self, stock_client):
        response = await stock_client.get("/v1/stock")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 3
        assert len(data["stocks"]) == 3

    async def test_listar_vacio(self, app_client):
        response = await app_client.get("/v1/stock")
        assert response.status_code == 200
        assert response.json()["data"]["total"] == 0


class TestEPSTK03Movimientos:
    async def test_movimientos_vacios_al_inicio(self, stock_client):
        response = await stock_client.get("/v1/stock/REP-001/movimientos")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 0

    async def test_movimientos_tras_ajuste(self, stock_client):
        await stock_client.post(
            "/v1/stock/REP-001/ajuste",
            json={"cantidad": 5, "actor_id": "user-1"},
        )
        response = await stock_client.get("/v1/stock/REP-001/movimientos")
        data = response.json()["data"]
        assert data["total"] == 1

    async def test_movimientos_stock_inexistente(self, stock_client):
        response = await stock_client.get("/v1/stock/NINGUNO/movimientos")
        assert response.status_code == 404


class TestEPSTK04AjusteStock:
    async def test_ajuste_positivo(self, stock_client):
        response = await stock_client.post(
            "/v1/stock/REP-001/ajuste",
            json={"cantidad": 10, "actor_id": "user-1", "motivo": "reposicion"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["cantidad_disponible"] == 30

    async def test_ajuste_negativo(self, stock_client):
        response = await stock_client.post(
            "/v1/stock/REP-001/ajuste",
            json={"cantidad": -5, "actor_id": "user-1"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["cantidad_disponible"] == 15

    async def test_ajuste_stock_inexistente(self, stock_client):
        response = await stock_client.post(
            "/v1/stock/NINGUNO/ajuste",
            json={"cantidad": 5, "actor_id": "user-1"},
        )
        assert response.status_code == 404

    async def test_ajuste_negativo_excede_disponible(self, stock_client):
        response = await stock_client.post(
            "/v1/stock/REP-001/ajuste",
            json={"cantidad": -100, "actor_id": "user-1"},
        )
        assert response.status_code == 422

    async def test_ajuste_cero_no_genera_movimiento(self, stock_client):
        response = await stock_client.post(
            "/v1/stock/REP-001/ajuste",
            json={"cantidad": 0, "actor_id": "user-1"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["cantidad_disponible"] == 20


class TestEPSTK05ActualizarUmbral:
    async def test_actualizar_umbral(self, stock_client):
        response = await stock_client.patch(
            "/v1/stock/REP-001/umbral",
            json={"umbral_minimo": 10, "actor_id": "user-1"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["umbral_minimo"] == 10

    async def test_umbral_a_cero(self, stock_client):
        response = await stock_client.patch(
            "/v1/stock/REP-001/umbral",
            json={"umbral_minimo": 0, "actor_id": "user-1"},
        )
        assert response.status_code == 200

    async def test_umbral_stock_inexistente(self, stock_client):
        response = await stock_client.patch(
            "/v1/stock/NINGUNO/umbral",
            json={"umbral_minimo": 5, "actor_id": "user-1"},
        )
        assert response.status_code == 404


class TestEPSTK06CrearReabastecimiento:
    async def test_crear_reabastecimiento(self, stock_client):
        response = await stock_client.post(
            "/v1/reabastecimientos",
            json={
                "proveedor": "Bajaj Perú SAC",
                "items": [
                    {
                        "repuesto_id": "rp-001",
                        "codigo": "REP-001",
                        "cantidad_solicitada": 20,
                        "precio_costo_unitario": "30.00",
                    }
                ],
                "notas": "Pedido urgente",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert "reabastecimiento_id" in data
        assert data["estado"] == EstadoReabastecimiento.SOLICITADO
        assert data["proveedor"] == "Bajaj Perú SAC"

    async def test_crear_reabastecimiento_sin_items_falla(self, stock_client):
        response = await stock_client.post(
            "/v1/reabastecimientos",
            json={"proveedor": "X", "items": []},
        )
        assert response.status_code == 422

    async def test_crear_reabastecimiento_sin_proveedor_falla(self, stock_client):
        response = await stock_client.post(
            "/v1/reabastecimientos",
            json={
                "proveedor": "",
                "items": [
                    {
                        "repuesto_id": "rp-001",
                        "codigo": "REP-001",
                        "cantidad_solicitada": 5,
                        "precio_costo_unitario": "25.00",
                    }
                ],
            },
        )
        assert response.status_code == 422


class TestEPSTK07ActualizarEstadoReabastecimiento:
    @pytest.fixture
    async def reab_id(self, stock_client) -> str:
        response = await stock_client.post(
            "/v1/reabastecimientos",
            json={
                "proveedor": "TVS Perú",
                "items": [
                    {
                        "repuesto_id": "rp-001",
                        "codigo": "REP-001",
                        "cantidad_solicitada": 10,
                        "precio_costo_unitario": "28.00",
                    }
                ],
            },
        )
        return response.json()["data"]["reabastecimiento_id"]

    async def test_avanzar_a_confirmado(self, stock_client, reab_id):
        response = await stock_client.patch(
            f"/v1/reabastecimientos/{reab_id}/estado",
            json={"estado": "CONFIRMADO_PROVEEDOR", "actor_id": "user-1"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "CONFIRMADO_PROVEEDOR"

    async def test_transicion_invalida(self, stock_client, reab_id):
        response = await stock_client.patch(
            f"/v1/reabastecimientos/{reab_id}/estado",
            json={"estado": "RECIBIDO", "actor_id": "user-1"},
        )
        assert response.status_code == 422

    async def test_reabastecimiento_inexistente(self, stock_client):
        response = await stock_client.patch(
            "/v1/reabastecimientos/id-99999/estado",
            json={"estado": "CONFIRMADO_PROVEEDOR", "actor_id": "user-1"},
        )
        assert response.status_code == 404

    async def test_flujo_completo_hasta_recibido(self, stock_client, reab_id):
        """Ciclo completo SOLICITADO → CONFIRMADO → EN_TRANSITO → RECIBIDO."""
        await stock_client.patch(
            f"/v1/reabastecimientos/{reab_id}/estado",
            json={"estado": "CONFIRMADO_PROVEEDOR", "actor_id": "user-1"},
        )
        await stock_client.patch(
            f"/v1/reabastecimientos/{reab_id}/estado",
            json={"estado": "EN_TRANSITO", "actor_id": "user-1"},
        )
        response = await stock_client.patch(
            f"/v1/reabastecimientos/{reab_id}/estado",
            json={"estado": "RECIBIDO", "actor_id": "user-1"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "RECIBIDO"

    async def test_recepcion_incrementa_stock(self, stock_client, reab_id):
        """Al recibir, el stock disponible de rp-001 sube en 10."""
        antes = (await stock_client.get("/v1/stock/REP-001")).json()["data"][
            "cantidad_disponible"
        ]
        await stock_client.patch(
            f"/v1/reabastecimientos/{reab_id}/estado",
            json={"estado": "CONFIRMADO_PROVEEDOR", "actor_id": "user-1"},
        )
        await stock_client.patch(
            f"/v1/reabastecimientos/{reab_id}/estado",
            json={"estado": "EN_TRANSITO", "actor_id": "user-1"},
        )
        await stock_client.patch(
            f"/v1/reabastecimientos/{reab_id}/estado",
            json={"estado": "RECIBIDO", "actor_id": "user-1"},
        )
        despues = (await stock_client.get("/v1/stock/REP-001")).json()["data"][
            "cantidad_disponible"
        ]
        assert despues == antes + 10


class TestEPSTK08ObtenerReabastecimiento:
    async def test_obtener_reabastecimiento(self, stock_client):
        crear = await stock_client.post(
            "/v1/reabastecimientos",
            json={
                "proveedor": "Bajaj",
                "items": [
                    {
                        "repuesto_id": "rp-002",
                        "codigo": "REP-002",
                        "cantidad_solicitada": 5,
                        "precio_costo_unitario": "20.00",
                    }
                ],
            },
        )
        reab_id = crear.json()["data"]["reabastecimiento_id"]

        response = await stock_client.get(f"/v1/reabastecimientos/{reab_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["proveedor"] == "Bajaj"
        assert len(data["items"]) == 1

    async def test_obtener_reabastecimiento_inexistente(self, stock_client):
        response = await stock_client.get("/v1/reabastecimientos/id-99999")
        assert response.status_code == 404

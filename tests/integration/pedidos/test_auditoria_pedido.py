"""
Tests de integración — FASE 2 (R29): auditoría transversal de Pedido.
EP-PED-20: GET /v1/pedidos/{pedido_id}/eventos.
"""
from __future__ import annotations

import pytest

from tests.integration.conftest import make_test_token


class TestAuditoriaPedido:
    async def test_crear_pedido_registra_evento(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/pedidos", json={"canal_origen": "presencial", "items": []},
        )
        pedido_id = crear.json()["data"]["pedido_id"]

        response = await pedidos_client.get(f"/v1/pedidos/{pedido_id}/eventos")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 1
        assert data["eventos"][0]["evento"] == "EP-PED-01-CREADO"
        assert data["eventos"][0]["actor_id"]

    async def test_confirmar_y_cancelar_agregan_eventos(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "presencial", "items": [{"codigo": "REP-001", "cantidad": 1}]},
        )
        pedido_id = crear.json()["data"]["pedido_id"]
        await pedidos_client.post(f"/v1/pedidos/{pedido_id}/confirmar")

        response = await pedidos_client.get(f"/v1/pedidos/{pedido_id}/eventos")
        data = response.json()["data"]
        eventos = [e["evento"] for e in data["eventos"]]
        assert eventos == ["EP-PED-01-CREADO", "EP-PED-04-CONFIRMAR"]
        assert data["eventos"][1]["estado_anterior"] == "BORRADOR"
        assert data["eventos"][1]["estado_nuevo"] == "CONFIRMADO"

    async def test_eventos_pedido_rechaza_rol_no_admin(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/pedidos", json={"canal_origen": "presencial", "items": []},
        )
        pedido_id = crear.json()["data"]["pedido_id"]
        token = make_test_token(pedidos_client._test_private_pem, "VENDEDOR")
        response = await pedidos_client.get(
            f"/v1/pedidos/{pedido_id}/eventos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_eventos_pedido_inexistente_404(self, pedidos_client):
        response = await pedidos_client.get("/v1/pedidos/pedido-99999/eventos")
        assert response.status_code == 404

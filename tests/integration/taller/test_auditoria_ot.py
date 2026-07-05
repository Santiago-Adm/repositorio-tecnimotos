"""
Tests de integración — FASE 2 (R29): auditoría transversal de OrdenTrabajo.
EP-TAL-15: GET /v1/ordenes-trabajo/{ot_id}/eventos.
"""
from __future__ import annotations

import pytest

from tests.integration.conftest import make_test_token


class TestAuditoriaOT:
    async def test_abrir_ot_registra_evento(self, taller_client):
        crear = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = crear.json()["data"]["ot_id"]

        response = await taller_client.get(f"/v1/ordenes-trabajo/{ot_id}/eventos")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 1
        assert data["eventos"][0]["evento"] == "EP-TAL-01-ABRIR"
        assert data["eventos"][0]["estado_nuevo"] == "ABIERTA"
        assert data["eventos"][0]["actor_id"]

    async def test_cancelar_ot_agrega_segundo_evento(self, taller_client):
        crear = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = crear.json()["data"]["ot_id"]
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/cancelar", json={"motivo": "cliente desistió"})

        response = await taller_client.get(f"/v1/ordenes-trabajo/{ot_id}/eventos")
        data = response.json()["data"]
        assert data["total"] == 2
        eventos = [e["evento"] for e in data["eventos"]]
        assert eventos == ["EP-TAL-01-ABRIR", "EP-TAL-09-CANCELAR"]
        assert data["eventos"][1]["estado_anterior"] == "ABIERTA"
        assert data["eventos"][1]["estado_nuevo"] == "CANCELADA"

    async def test_eventos_ot_rechaza_rol_no_admin(self, taller_client):
        crear = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = crear.json()["data"]["ot_id"]
        token = make_test_token(taller_client._test_private_pem, "MECANICO_MASTER")
        response = await taller_client.get(
            f"/v1/ordenes-trabajo/{ot_id}/eventos",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_eventos_ot_inexistente_404(self, taller_client):
        response = await taller_client.get("/v1/ordenes-trabajo/ot-99999/eventos")
        assert response.status_code == 404

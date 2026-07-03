"""
Tests de integración — EP-TAL-13: prueba de ruta post-reparación.

Casos cubiertos:
  - Sin observaciones: salud_estimada = 100 automático
  - Con observaciones: mecánico declara valor menor, persistido en OT y vehículo
  - Salud visible para cliente en EP-TAL-12 tras la prueba de ruta
  - Con observaciones sin salud_declarada → 422
  - OT no CERRADA → 422
  - Roles: MECANICO_MASTER puede ejecutar · CLIENTE_CONDUCTOR no puede (403)
"""
from __future__ import annotations

import pytest

from tests.integration.conftest import make_test_token


@pytest.fixture
async def ot_cerrada(taller_client):
    """OT completa hasta estado CERRADA."""
    r = await taller_client.post(
        "/v1/ordenes-trabajo",
        json={
            "vehiculo_id": taller_client._vehiculo_id,
            "mecanico_master_id": taller_client._mecanico_id,
            "modalidad": "correctivo",
            "urgencia": "media",
        },
    )
    ot_id = r.json()["data"]["ot_id"]
    await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/repuestos", json={"codigo": "REP-001", "cantidad": 1})
    await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
    await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/revision-final", json={"costo_mano_obra": "50.00"})
    await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/cobro-parcial", json={"monto_pagado": "75.00", "plazo_dias": 1})
    await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/cerrar")
    taller_client._ot_id = ot_id
    return taller_client


# ── Sin observaciones → salud 100 automático ─────────────────────────────────

@pytest.mark.asyncio
async def test_prueba_ruta_sin_observaciones_asigna_100(ot_cerrada):
    r = await ot_cerrada.post(
        f"/v1/ordenes-trabajo/{ot_cerrada._ot_id}/prueba-ruta",
        json={},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["prueba_ruta_completada"] is True
    assert data["salud_resultado"] == 100
    assert data["vehiculo_salud_estimada"] == 100
    assert data["observaciones_prueba_ruta"] is None


# ── Con observaciones → mecánico declara valor ───────────────────────────────

@pytest.mark.asyncio
async def test_prueba_ruta_con_observaciones_persiste_valor_declarado(ot_cerrada):
    r = await ot_cerrada.post(
        f"/v1/ordenes-trabajo/{ot_cerrada._ot_id}/prueba-ruta",
        json={
            "observaciones": "Vibración leve en segunda marcha, pendiente revisión.",
            "salud_declarada": 75,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["prueba_ruta_completada"] is True
    assert data["salud_resultado"] == 75
    assert data["vehiculo_salud_estimada"] == 75
    assert data["observaciones_prueba_ruta"] == "Vibración leve en segunda marcha, pendiente revisión."


# ── Salud visible en EP-TAL-12 (cliente puede ver su historial) ───────────────

@pytest.mark.asyncio
async def test_salud_visible_en_ep_tal_12(ot_cerrada):
    await ot_cerrada.post(
        f"/v1/ordenes-trabajo/{ot_cerrada._ot_id}/prueba-ruta",
        json={"observaciones": "Freno trasero algo duro.", "salud_declarada": 85},
    )
    r = await ot_cerrada.get(f"/v1/ordenes-trabajo/{ot_cerrada._ot_id}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["prueba_ruta_completada"] is True
    assert data["salud_resultado"] == 85
    assert data["observaciones_prueba_ruta"] is not None


# ── Validaciones de negocio ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_observaciones_sin_salud_declarada_rechaza_422(ot_cerrada):
    """Observaciones presentes pero sin salud_declarada → 422."""
    r = await ot_cerrada.post(
        f"/v1/ordenes-trabajo/{ot_cerrada._ot_id}/prueba-ruta",
        json={"observaciones": "Hay algo raro en el motor."},
    )
    assert r.status_code == 422, r.text
    assert "salud_declarada" in r.json()["detail"]["error"]["message"]


@pytest.mark.asyncio
async def test_ot_no_cerrada_rechaza_422(taller_client):
    """OT en estado ABIERTA → 422 al intentar registrar prueba de ruta."""
    r = await taller_client.post(
        "/v1/ordenes-trabajo",
        json={
            "vehiculo_id": taller_client._vehiculo_id,
            "mecanico_master_id": taller_client._mecanico_id,
            "modalidad": "correctivo",
            "urgencia": "alta",
        },
    )
    ot_id = r.json()["data"]["ot_id"]

    r2 = await taller_client.post(
        f"/v1/ordenes-trabajo/{ot_id}/prueba-ruta",
        json={},
    )
    assert r2.status_code == 422
    assert "CERRADA" in r2.json()["detail"]["error"]["message"]


@pytest.mark.asyncio
async def test_ot_inexistente_retorna_404(taller_client):
    r = await taller_client.post("/v1/ordenes-trabajo/no-existe/prueba-ruta", json={})
    assert r.status_code == 404


# ── RBAC ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cliente_conductor_no_puede_registrar_prueba_ruta(ot_cerrada):
    token = make_test_token(ot_cerrada._test_private_pem, "CLIENTE_CONDUCTOR")
    r = await ot_cerrada.post(
        f"/v1/ordenes-trabajo/{ot_cerrada._ot_id}/prueba-ruta",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_mecanico_junior_no_puede_registrar_prueba_ruta(ot_cerrada):
    token = make_test_token(ot_cerrada._test_private_pem, "MECANICO_JUNIOR")
    r = await ot_cerrada.post(
        f"/v1/ordenes-trabajo/{ot_cerrada._ot_id}/prueba-ruta",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


# ── Visibilidad desde perspectiva del CLIENTE (EP-TAL-12) ────────────────────

@pytest.mark.asyncio
async def test_cliente_ve_campos_salud_en_ep_tal_12(ot_cerrada):
    """
    NUEVO — verificación de cierre (no contabilizado en los 8/8 originales).
    Un CLIENTE_CONDUCTOR autenticado consulta su propia OT (EP-TAL-12) y
    ve los tres campos nuevos de prueba de ruta con los valores correctos.
    """
    # Registrar prueba de ruta como MECANICO_MASTER (rol por defecto del fixture)
    await ot_cerrada.post(
        f"/v1/ordenes-trabajo/{ot_cerrada._ot_id}/prueba-ruta",
        json={"observaciones": "Aceite quemado leve.", "salud_declarada": 80},
    )

    # Consultar como CLIENTE_CONDUCTOR
    token_cliente = make_test_token(ot_cerrada._test_private_pem, "CLIENTE_CONDUCTOR")
    r = await ot_cerrada.get(
        f"/v1/ordenes-trabajo/{ot_cerrada._ot_id}",
        headers={"Authorization": f"Bearer {token_cliente}"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    # Los tres campos nuevos deben estar presentes y correctos
    assert data["prueba_ruta_completada"] is True
    assert data["salud_resultado"] == 80
    assert data["observaciones_prueba_ruta"] == "Aceite quemado leve."

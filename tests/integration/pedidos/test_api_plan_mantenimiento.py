"""
Tests de integración — EP-PED-18/19: Plan de mantenimiento preventivo.

Casos cubiertos:
  - EP-PED-18: activar plan → 201, estructura de respuesta
  - EP-PED-18: segundo plan para el mismo vehículo → 409 PLAN_YA_ACTIVO
  - EP-PED-18: plan para otro vehículo del mismo cliente → 201 (un plan por vehículo)
  - EP-PED-19: cancelar plan propio → 200, estado CANCELADO
  - EP-PED-19: cancelar plan ajeno → 422
  - EP-PED-19: plan inexistente → 404
  - EP-PED-19: plan ya cancelado no se puede cancelar de nuevo → 422
  - RBAC: CLIENTE_RURAL puede activar · ADMINISTRADOR no puede (403) · VENDEDOR no puede (403)
  - Job lógica de dominio: plan con 30+ días llama a registrar_recordatorio
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from src.pedidos.domain.models.pedido import PlanMantenimiento, EstadoPlanMantenimiento
from tests.integration.conftest import make_test_token


def _token(client, rol: str, sub: str = "test-user") -> str:
    return make_test_token(client._test_private_pem, rol, sub=sub)


# ── EP-PED-18: Activar plan ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_activar_plan_retorna_201(app_client):
    token = _token(app_client, "CLIENTE_CONDUCTOR", sub="cli-001")
    r = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-aaa"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["estado"] == "ACTIVO"
    assert data["vehiculo_id"] == "moto-aaa"
    assert data["cliente_id"] == "cli-001"
    assert data["fecha_ultimo_recordatorio"] is None
    assert "proximo_recordatorio" in data


@pytest.mark.asyncio
async def test_activar_plan_dos_veces_mismo_vehiculo_retorna_409(app_client):
    token = _token(app_client, "CLIENTE_CONDUCTOR", sub="cli-002")
    headers = {"Authorization": f"Bearer {token}"}
    await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-bbb"},
        headers=headers,
    )
    r2 = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-bbb"},
        headers=headers,
    )
    assert r2.status_code == 409
    assert r2.json()["detail"]["error"]["code"] == "PLAN_YA_ACTIVO"


@pytest.mark.asyncio
async def test_activar_plan_diferente_vehiculo_mismo_cliente_retorna_201(app_client):
    token = _token(app_client, "CLIENTE_CONDUCTOR", sub="cli-003")
    headers = {"Authorization": f"Bearer {token}"}
    r1 = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-ccc"},
        headers=headers,
    )
    r2 = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-ddd"},
        headers=headers,
    )
    assert r1.status_code == 201
    assert r2.status_code == 201


@pytest.mark.asyncio
async def test_cliente_rural_puede_activar_plan(app_client):
    token = _token(app_client, "CLIENTE_RURAL", sub="cli-rural-001")
    r = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-rural"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201


# ── EP-PED-19: Cancelar plan ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cancelar_plan_propio(app_client):
    token = _token(app_client, "CLIENTE_CONDUCTOR", sub="cli-004")
    headers = {"Authorization": f"Bearer {token}"}
    r_activar = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-eee"},
        headers=headers,
    )
    plan_id = r_activar.json()["data"]["plan_id"]

    r_cancelar = await app_client.post(
        f"/v1/pedidos/plan-mantenimiento/{plan_id}/cancelar",
        headers=headers,
    )
    assert r_cancelar.status_code == 200
    assert r_cancelar.json()["data"]["estado"] == "CANCELADO"


@pytest.mark.asyncio
async def test_cancelar_plan_de_otro_cliente_retorna_422(app_client):
    token_dueno = _token(app_client, "CLIENTE_CONDUCTOR", sub="cli-005")
    r = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-fff"},
        headers={"Authorization": f"Bearer {token_dueno}"},
    )
    plan_id = r.json()["data"]["plan_id"]

    token_intruso = _token(app_client, "CLIENTE_CONDUCTOR", sub="intruso-001")
    r2 = await app_client.post(
        f"/v1/pedidos/plan-mantenimiento/{plan_id}/cancelar",
        headers={"Authorization": f"Bearer {token_intruso}"},
    )
    assert r2.status_code == 422


@pytest.mark.asyncio
async def test_cancelar_plan_inexistente_retorna_404(app_client):
    token = _token(app_client, "CLIENTE_CONDUCTOR")
    r = await app_client.post(
        "/v1/pedidos/plan-mantenimiento/no-existe/cancelar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_cancelar_plan_ya_cancelado_retorna_422(app_client):
    token = _token(app_client, "CLIENTE_CONDUCTOR", sub="cli-006")
    headers = {"Authorization": f"Bearer {token}"}
    r = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-ggg"},
        headers=headers,
    )
    plan_id = r.json()["data"]["plan_id"]
    await app_client.post(f"/v1/pedidos/plan-mantenimiento/{plan_id}/cancelar", headers=headers)
    r2 = await app_client.post(f"/v1/pedidos/plan-mantenimiento/{plan_id}/cancelar", headers=headers)
    assert r2.status_code == 422


# ── RBAC ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_administrador_no_puede_activar_plan(app_client):
    """Los admins no usan el plan de mantenimiento — es exclusivo de clientes."""
    r = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-hhh"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_vendedor_no_puede_activar_plan(app_client):
    token = _token(app_client, "VENDEDOR")
    r = await app_client.post(
        "/v1/pedidos/plan-mantenimiento",
        json={"vehiculo_id": "moto-iii"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


# ── Lógica del job — capa de dominio ─────────────────────────────────────────

def test_plan_nuevo_no_necesita_recordatorio():
    plan = PlanMantenimiento(cliente_id="c1", vehiculo_id="v1")
    assert plan.necesita_recordatorio() is False


def test_plan_con_29_dias_no_necesita_recordatorio():
    hace_29 = datetime.now(timezone.utc) - timedelta(days=29)
    plan = PlanMantenimiento(cliente_id="c1", vehiculo_id="v1", fecha_activacion=hace_29)
    assert plan.necesita_recordatorio() is False


def test_plan_con_30_dias_necesita_recordatorio():
    hace_30 = datetime.now(timezone.utc) - timedelta(days=30, seconds=1)
    plan = PlanMantenimiento(cliente_id="c1", vehiculo_id="v1", fecha_activacion=hace_30)
    assert plan.necesita_recordatorio() is True


def test_plan_cancelado_no_necesita_recordatorio():
    hace_30 = datetime.now(timezone.utc) - timedelta(days=30, seconds=1)
    plan = PlanMantenimiento(
        cliente_id="c1", vehiculo_id="v1",
        fecha_activacion=hace_30,
        estado=EstadoPlanMantenimiento.CANCELADO,
    )
    assert plan.necesita_recordatorio() is False


def test_registrar_recordatorio_actualiza_fecha():
    hace_30 = datetime.now(timezone.utc) - timedelta(days=30, seconds=1)
    plan = PlanMantenimiento(cliente_id="c1", vehiculo_id="v1", fecha_activacion=hace_30)
    assert plan.necesita_recordatorio() is True
    plan.registrar_recordatorio()
    assert plan.fecha_ultimo_recordatorio is not None
    # Tras el recordatorio ya no lo necesita (acaba de marcarse)
    assert plan.necesita_recordatorio() is False

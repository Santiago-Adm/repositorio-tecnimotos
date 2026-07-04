"""
Tests de integración EP-ADM-09 (listado general de usuarios)
y EP-ADM-10 (métricas de negocio agregadas).
"""
from __future__ import annotations

import decimal
from decimal import Decimal

import pytest

from tests.integration.conftest import make_test_token


# ── EP-ADM-09 — GET /v1/admin/usuarios ───────────────────────────────────────

@pytest.mark.asyncio
async def test_adm09_lista_todos_los_usuarios(app_client):
    """Sin filtros retorna todos los usuarios (al menos el seed ADMINISTRADOR)."""
    r = await app_client.get("/v1/admin/usuarios")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 1
    assert any(u["rol"] == "ADMINISTRADOR" for u in data["usuarios"])


@pytest.mark.asyncio
async def test_adm09_filtra_por_rol(app_client):
    """Filtro ?rol= devuelve solo usuarios con ese rol exacto."""
    # Crear usuario VENDEDOR para tener datos distintos
    token = make_test_token(app_client._test_private_pem, "SUPERADMIN")
    await app_client.post(
        "/v1/admin/usuarios",
        json={"email": "v@test.com", "nombre": "Vend", "rol": "VENDEDOR", "password": "pass1234"},
        headers={"Authorization": f"Bearer {token}"},
    )
    r = await app_client.get("/v1/admin/usuarios?rol=VENDEDOR")
    assert r.status_code == 200
    data = r.json()["data"]
    assert all(u["rol"] == "VENDEDOR" for u in data["usuarios"])
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_adm09_filtra_por_estado(app_client):
    """Filtro ?estado=ACTIVO devuelve solo usuarios ACTIVO."""
    r = await app_client.get("/v1/admin/usuarios?estado=ACTIVO")
    assert r.status_code == 200
    data = r.json()["data"]
    assert all(u["estado_cuenta"] == "ACTIVO" for u in data["usuarios"])


@pytest.mark.asyncio
async def test_adm09_respuesta_incluye_variante_tema(app_client):
    """Cada usuario expone variante_tema en el listado."""
    r = await app_client.get("/v1/admin/usuarios")
    assert r.status_code == 200
    for u in r.json()["data"]["usuarios"]:
        assert "variante_tema" in u


@pytest.mark.asyncio
async def test_adm09_rbac_vendedor_bloqueado(app_client):
    """VENDEDOR no puede acceder al listado general."""
    token = make_test_token(app_client._test_private_pem, "VENDEDOR")
    r = await app_client.get("/v1/admin/usuarios", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_adm09_superadmin_puede_listar(app_client):
    """SUPERADMIN también puede listar."""
    token = make_test_token(app_client._test_private_pem, "SUPERADMIN")
    r = await app_client.get("/v1/admin/usuarios", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


# ── EP-ADM-10 — GET /v1/admin/metricas-negocio ───────────────────────────────

@pytest.mark.asyncio
async def test_adm10_respuesta_200_con_estructura(app_client):
    """Sin datos extra retorna las 4 claves esperadas con valores numéricos."""
    r = await app_client.get("/v1/admin/metricas-negocio")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "ots_activas" in data
    assert "pedidos_activos_hoy" in data
    assert "repuestos_bajo_umbral" in data
    assert "comprobantes_emitidos_periodo" in data
    assert "periodo_comprobantes" in data
    assert isinstance(data["ots_activas"], int)
    assert isinstance(data["pedidos_activos_hoy"], int)
    assert isinstance(data["repuestos_bajo_umbral"], int)


@pytest.mark.asyncio
async def test_adm10_ots_activas_coincide_con_seed(app_client, taller_client):
    """El conteo de OTs activas coincide con las OTs en estado activo del seed."""
    from src.taller.domain.models.orden_trabajo import (
        OrdenTrabajo, ModalidadIntervencion, NivelUrgencia,
    )
    repo = taller_client.app.state.taller_repo

    ot1 = OrdenTrabajo(
        vehiculo_id="v-001", mecanico_master_id="m-001",
        modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
    )
    ot2 = OrdenTrabajo(
        vehiculo_id="v-001", mecanico_master_id="m-001",
        modalidad=ModalidadIntervencion.PREVENTIVO, urgencia=NivelUrgencia.BAJA,
    )
    await repo.guardar_ot(ot1)
    await repo.guardar_ot(ot2)

    token = make_test_token(taller_client._test_private_pem, "SUPERADMIN")
    r = await taller_client.get("/v1/admin/metricas-negocio", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["data"]["ots_activas"] == 2


@pytest.mark.asyncio
async def test_adm10_repuestos_bajo_umbral_coincide_con_seed(app_client):
    """El conteo de repuestos bajo umbral coincide con lo que tiene el stock."""
    from src.stock.domain.models.stock import StockRepuesto
    repo = app_client.app.state.stock_repo

    s = StockRepuesto(repuesto_id="rp-umbral", codigo="UMB-001")
    s.ajustar_umbral(10)
    s.cantidad_disponible = 3  # 3 < umbral 10 → bajo umbral
    await repo.guardar(s)

    r = await app_client.get("/v1/admin/metricas-negocio")
    assert r.status_code == 200
    assert r.json()["data"]["repuestos_bajo_umbral"] >= 1


@pytest.mark.asyncio
async def test_adm10_comprobantes_mes_actual_suma_correcta(app_client):
    """La suma de comprobantes EMITIDO del mes actual es exacta."""
    from src.pedidos.domain.models.pedido import Comprobante, TipoComprobante
    repo = app_client.app.state.pedidos_repo

    comp = Comprobante(
        pedido_id="p-001", monto=Decimal("150.00"),
        tipo=TipoComprobante.BOLETA, emitido_por="user-admin-seed",
    )
    comp.aprobar()  # → EMITIDO
    await repo.guardar_comprobante(comp)

    r = await app_client.get("/v1/admin/metricas-negocio")
    assert r.status_code == 200
    assert r.json()["data"]["comprobantes_emitidos_periodo"] == 150.0


@pytest.mark.asyncio
async def test_adm10_rbac_vendedor_bloqueado(app_client):
    """VENDEDOR no puede acceder a métricas de negocio."""
    token = make_test_token(app_client._test_private_pem, "VENDEDOR")
    r = await app_client.get("/v1/admin/metricas-negocio", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_adm10_superadmin_puede_consultar(app_client):
    """SUPERADMIN puede consultar métricas de negocio."""
    token = make_test_token(app_client._test_private_pem, "SUPERADMIN")
    r = await app_client.get("/v1/admin/metricas-negocio", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


# ── EP-ADM-11 — GET /v1/admin/metricas ────────────────────────────────────────

@pytest.mark.asyncio
async def test_adm11_respuesta_200_con_estructura(app_client):
    """Sin datos extra retorna las 3 claves esperadas con valores numéricos."""
    token = make_test_token(app_client._test_private_pem, "SUPERADMIN")
    r = await app_client.get("/v1/admin/metricas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "rotacion_stock" in data
    assert "margen_promedio" in data
    assert "tasa_conversion" in data
    assert isinstance(data["rotacion_stock"], float)
    assert isinstance(data["margen_promedio"], float)
    assert isinstance(data["tasa_conversion"], float)


@pytest.mark.asyncio
async def test_adm11_rbac_vendedor_bloqueado(app_client):
    """VENDEDOR no puede acceder a métricas operacionales."""
    token = make_test_token(app_client._test_private_pem, "VENDEDOR")
    r = await app_client.get("/v1/admin/metricas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_adm11_tasa_conversion_calculo(app_client):
    """Verifica que la tasa de conversión se calcula correctamente basándose en entradas y OTs."""
    from src.taller.domain.models.orden_trabajo import Entrada, EstadoEntrada
    taller_repo = app_client.app.state.taller_repo

    e1 = Entrada(vehiculo_id="v-100", orden_trabajo_id="ot-100", estado=EstadoEntrada.ACTIVA)
    e2 = Entrada(vehiculo_id="v-101", orden_trabajo_id=None, estado=EstadoEntrada.ACTIVA)

    await taller_repo.guardar_entrada(e1)
    await taller_repo.guardar_entrada(e2)

    token = make_test_token(app_client._test_private_pem, "SUPERADMIN")
    r = await app_client.get("/v1/admin/metricas", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    # 1 de 2 convertido = 50.0%
    assert r.json()["data"]["tasa_conversion"] == 50.0


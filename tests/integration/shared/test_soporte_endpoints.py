"""
Tests de integración EP-SOP-01 y EP-SOP-02 (HU-INT-08, 02 §5.1).
Gherkin Escenario 1: cliente reporta error → 201, reporte en ABIERTO.
Gherkin Escenario 2 (mitad backend): transición ABIERTO → EN_INVESTIGACION via SoporteService.
"""
from __future__ import annotations

import pytest
from tests.integration.conftest import make_test_token


# ══════════════════════════════════════════════════════════════════════
# EP-SOP-01 — POST /v1/soporte/reportes
# Gherkin Escenario 1 (02 §5.1 HU-INT-08)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_sop01_escenario1_cliente_reporta_error_retorna_201_en_abierto(app_client):
    """
    Gherkin Escenario 1:
    Given el CLIENTE_RURAL experimentó un error al confirmar una reserva
    When envía POST /soporte/reportes con body {"descripcion": "..."}
    Then el sistema retorna HTTP 201
      And el reporte existe en estado ABIERTO
      And queda vinculado a usuario_reportante_id y rol_usuario_reportante
    """
    token = make_test_token(app_client._test_private_pem, "CLIENTE_RURAL", sub="cli-rural-005")
    r = await app_client.post(
        "/v1/soporte/reportes",
        json={"descripcion": "No pude confirmar mi reserva, salió error"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["estado"] == "ABIERTO"
    assert data["usuario_reportante_id"] == "cli-rural-005"
    assert data["rol_usuario_reportante"] == "CLIENTE_RURAL"
    assert data["descripcion"] == "No pude confirmar mi reserva, salió error"
    assert data["id"]
    assert data["creado_en"]
    assert data["resuelto_en"] is None
    assert data["resuelto_por"] is None


@pytest.mark.asyncio
async def test_sop01_todos_los_roles_internos_pueden_crear_reporte(app_client):
    """Cualquier rol autenticado puede usar EP-SOP-01."""
    for rol in ("SUPERADMIN", "ADMINISTRADOR", "VENDEDOR", "MECANICO_MASTER", "MECANICO_JUNIOR"):
        token = make_test_token(app_client._test_private_pem, rol)
        r = await app_client.post(
            "/v1/soporte/reportes",
            json={"descripcion": f"Error reportado por {rol}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201, f"Falló para rol {rol}: {r.text}"


@pytest.mark.asyncio
async def test_sop01_todos_los_roles_cliente_pueden_crear_reporte(app_client):
    for rol in ("CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
                "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL"):
        token = make_test_token(app_client._test_private_pem, rol)
        r = await app_client.post(
            "/v1/soporte/reportes",
            json={"descripcion": f"Problema reportado por {rol}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201, f"Falló para rol {rol}: {r.text}"


@pytest.mark.asyncio
async def test_sop01_sin_token_retorna_401(app_client):
    r = await app_client.post(
        "/v1/soporte/reportes",
        json={"descripcion": "intento sin auth"},
        headers={"Authorization": ""},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_sop01_descripcion_vacia_retorna_422(app_client):
    token = make_test_token(app_client._test_private_pem, "CLIENTE_RURAL")
    r = await app_client.post(
        "/v1/soporte/reportes",
        json={"descripcion": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


# ══════════════════════════════════════════════════════════════════════
# EP-SOP-02 — GET /v1/soporte/reportes
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_sop02_superadmin_lista_reportes_activos(app_client):
    """SUPERADMIN puede listar reportes ABIERTO y EN_INVESTIGACION."""
    # Crear un reporte como cliente
    token_cliente = make_test_token(app_client._test_private_pem, "CLIENTE_RURAL", sub="cli-001")
    await app_client.post(
        "/v1/soporte/reportes",
        json={"descripcion": "Error en pago"},
        headers={"Authorization": f"Bearer {token_cliente}"},
    )

    token_sa = make_test_token(app_client._test_private_pem, "SUPERADMIN")
    r = await app_client.get(
        "/v1/soporte/reportes",
        headers={"Authorization": f"Bearer {token_sa}"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert "reportes" in data
    assert "total" in data
    assert data["total"] >= 1
    estados_activos = {"ABIERTO", "EN_INVESTIGACION"}
    for rep in data["reportes"]:
        assert rep["estado"] in estados_activos


@pytest.mark.asyncio
async def test_sop02_no_superadmin_retorna_403(app_client):
    """Solo SUPERADMIN puede acceder a EP-SOP-02."""
    for rol in ("ADMINISTRADOR", "VENDEDOR", "MECANICO_MASTER", "CLIENTE_RURAL"):
        token = make_test_token(app_client._test_private_pem, rol)
        r = await app_client.get(
            "/v1/soporte/reportes",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403, f"Esperaba 403 para rol {rol}, obtuvo {r.status_code}"


@pytest.mark.asyncio
async def test_sop02_sin_token_retorna_401(app_client):
    r = await app_client.get(
        "/v1/soporte/reportes",
        headers={"Authorization": ""},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_sop02_lista_vacia_cuando_no_hay_reportes(app_client):
    token_sa = make_test_token(app_client._test_private_pem, "SUPERADMIN")
    r = await app_client.get(
        "/v1/soporte/reportes",
        headers={"Authorization": f"Bearer {token_sa}"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] == 0
    assert data["reportes"] == []


# ══════════════════════════════════════════════════════════════════════
# Gherkin Escenario 2 — mitad backend construida
# Transición ABIERTO → EN_INVESTIGACION via SoporteService
# El endpoint de impersonación (DEP-10-001) no existe aún.
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_sop_escenario2_activar_investigacion_transiciona_estado(app_client):
    """
    Gherkin Escenario 2 (mitad backend):
    Given existe reporte_soporte en estado ABIERTO
    When se invoca activar_investigacion(reporte_soporte_id)
    Then el reporte pasa a EN_INVESTIGACION
    """
    from src.shared.application.use_cases.soporte_use_cases import SoporteService

    repo = app_client.app.state.soporte_repo
    svc = SoporteService(repo)

    reporte = await svc.crear_reporte(
        usuario_reportante_id="cli-rural-005",
        rol_usuario_reportante="CLIENTE_RURAL",
        descripcion="No pude confirmar mi reserva",
    )
    assert reporte.estado.value == "ABIERTO"

    actualizado = await svc.activar_investigacion(reporte.id)
    assert actualizado.estado.value == "EN_INVESTIGACION"


@pytest.mark.asyncio
async def test_sop_escenario2_sin_reporte_valido_lanza_no_encontrado(app_client):
    """
    Gherkin Escenario 2:
    And sin un reporte_soporte_id válido → error (HTTP 422 cuando se exponga via impersonación).
    La excepción domain-level es ReporteSoporteNoEncontradoError.
    """
    from src.shared.application.use_cases.soporte_use_cases import SoporteService
    from src.shared.domain.models.reporte_soporte import ReporteSoporteNoEncontradoError

    repo = app_client.app.state.soporte_repo
    svc = SoporteService(repo)

    with pytest.raises(ReporteSoporteNoEncontradoError):
        await svc.activar_investigacion("reporte-id-inexistente")


@pytest.mark.asyncio
async def test_sop02_reportes_cerrados_no_aparecen_en_listado(app_client):
    """Reportes RESUELTO y CERRADO_SIN_RESOLUCION no aparecen en EP-SOP-02."""
    from src.shared.application.use_cases.soporte_use_cases import SoporteService

    repo = app_client.app.state.soporte_repo
    svc = SoporteService(repo)

    # Crear y cerrar un reporte
    r_cerrado = await svc.crear_reporte("u-001", "CLIENTE_RURAL", "ya resuelto")
    r_cerrado.cerrar_sin_resolucion()
    await repo.guardar(r_cerrado)

    # Crear uno activo
    r_activo = await svc.crear_reporte("u-002", "CLIENTE_CONDUCTOR", "aún abierto")

    token_sa = make_test_token(app_client._test_private_pem, "SUPERADMIN")
    resp = await app_client.get(
        "/v1/soporte/reportes",
        headers={"Authorization": f"Bearer {token_sa}"},
    )
    data = resp.json()["data"]
    ids_en_lista = {rep["id"] for rep in data["reportes"]}
    assert r_activo.id in ids_en_lista
    assert r_cerrado.id not in ids_en_lista

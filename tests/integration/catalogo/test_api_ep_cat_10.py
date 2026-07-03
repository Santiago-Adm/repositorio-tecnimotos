"""
Tests de integración — EP-CAT-10: PATCH /v1/repuestos/{codigo}
Edición de datos descriptivos (nombre, descripcion, categoria, modelo, año).
Confirma que precio_venta y repuesto.precio_actualizado no se ven afectados.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    UniversoRepuesto,
)
from src.shared.events.event_bus import InMemoryEventBus
from tests.integration.conftest import make_test_token


@pytest.fixture
async def repuesto_fixture(app_client):
    """Repuesto de prueba precargado con precio y datos iniciales."""
    repo = app_client.app.state.catalogo_repo
    repuesto = Repuesto(
        codigo="REP-EDIT-001",
        nombre="Filtro original",
        universo=UniversoRepuesto.MOTOTAXI_3R,
        modelo="Bajaj RE",
        año=2021,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("75.00"),
        descripcion="Descripción original",
    )
    await repo.guardar(repuesto)
    app_client._codigo = repuesto.codigo
    app_client._precio_original = repuesto.precio_venta
    app_client._repuesto_id = repuesto.id
    return app_client


# ── Edición exitosa de campos individuales ────────────────────────────────────

@pytest.mark.asyncio
async def test_editar_nombre(repuesto_fixture):
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"nombre": "Filtro actualizado"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["nombre"] == "Filtro actualizado"
    assert data["codigo"] == repuesto_fixture._codigo


@pytest.mark.asyncio
async def test_editar_descripcion(repuesto_fixture):
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"descripcion": "Nueva descripción corregida"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["descripcion"] == "Nueva descripción corregida"


@pytest.mark.asyncio
async def test_editar_categoria(repuesto_fixture):
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"categoria": "frenos"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["categoria"] == "frenos"


@pytest.mark.asyncio
async def test_editar_modelo(repuesto_fixture):
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"modelo": "Honda Wave"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["modelo"] == "Honda Wave"


@pytest.mark.asyncio
async def test_editar_año(repuesto_fixture):
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"año": 2023},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["año"] == 2023


@pytest.mark.asyncio
async def test_editar_varios_campos_en_una_llamada(repuesto_fixture):
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"nombre": "Filtro v2", "modelo": "Yamaha FZ", "año": 2022},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["nombre"] == "Filtro v2"
    assert data["modelo"] == "Yamaha FZ"
    assert data["año"] == 2022


# ── Precio intacto — garantía de separación EP-CAT-04 / EP-CAT-10 ────────────

@pytest.mark.asyncio
async def test_precio_no_se_modifica_ni_se_devuelve(repuesto_fixture):
    """precio_venta no aparece en la respuesta ni se modifica."""
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"nombre": "Nombre nuevo"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert "precio_venta" not in data

    # Confirmar en repo que el precio no cambió
    repo = repuesto_fixture.app.state.catalogo_repo
    repuesto = await repo.obtener_por_codigo(repuesto_fixture._codigo)
    assert repuesto.precio_venta == repuesto_fixture._precio_original


@pytest.mark.asyncio
async def test_evento_precio_no_se_dispara(repuesto_fixture):
    """repuesto.precio_actualizado NO se publica al editar datos descriptivos."""
    event_bus: InMemoryEventBus = repuesto_fixture.app.state.event_bus
    publicados_antes = event_bus.conteo_publicaciones("repuesto.precio_actualizado")

    await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"nombre": "Otro nombre"},
    )
    publicados_despues = event_bus.conteo_publicaciones("repuesto.precio_actualizado")
    nuevos = publicados_despues - publicados_antes
    assert nuevos == 0, f"No debería publicarse repuesto.precio_actualizado; se publicaron {nuevos}"
    # sentinel — mantiene el assert dentro del bloque correcto
    nuevos = []


# ── codigo y universo → rechazo explícito 422 ────────────────────────────────
# Comportamiento anterior: ignorar silenciosamente (PCT 2026-06-28).
# Comportamiento corregido (PCT corrección 2026-06-28): rechazar con 422 específico
# para que errores de script/integración externa sean visibles inmediatamente.

@pytest.mark.asyncio
async def test_codigo_en_body_rechaza_422(repuesto_fixture):
    """codigo en body → 422 con mensaje que identifica el campo no editable."""
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"nombre": "Nuevo nombre", "codigo": "REP-CAMBIADO"},
    )
    assert r.status_code == 422, r.text
    msg = r.json()["detail"]["error"]["message"]
    assert "codigo" in msg


@pytest.mark.asyncio
async def test_universo_en_body_rechaza_422(repuesto_fixture):
    """universo en body → 422 con mensaje que identifica el campo no editable."""
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"nombre": "Nuevo nombre", "universo": "motolineal"},
    )
    assert r.status_code == 422, r.text
    msg = r.json()["detail"]["error"]["message"]
    assert "universo" in msg


@pytest.mark.asyncio
async def test_codigo_y_universo_juntos_listan_ambos(repuesto_fixture):
    """Ambos campos no editables en el mismo body → 422 con ambos mencionados en el mensaje."""
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"nombre": "Nuevo nombre", "codigo": "REP-X", "universo": "motolineal"},
    )
    assert r.status_code == 422, r.text
    msg = r.json()["detail"]["error"]["message"]
    assert "codigo" in msg
    assert "universo" in msg


# ── RBAC ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_vendedor_no_puede_editar_datos(repuesto_fixture):
    token = make_test_token(repuesto_fixture._test_private_pem, "VENDEDOR")
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"nombre": "Intento vendedor"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_cliente_no_puede_editar_datos(repuesto_fixture):
    token = make_test_token(repuesto_fixture._test_private_pem, "CLIENTE_CONDUCTOR")
    r = await repuesto_fixture.patch(
        f"/v1/repuestos/{repuesto_fixture._codigo}",
        json={"nombre": "Intento cliente"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


# ── Errores ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_repuesto_no_encontrado_retorna_404(app_client):
    r = await app_client.patch(
        "/v1/repuestos/REP-NO-EXISTE",
        json={"nombre": "X"},
    )
    assert r.status_code == 404

"""
Tests de integración — EP-CAT-11 (reemplazar imagen) y EP-CAT-12 (reordenar galería).

Casos cubiertos:
  EP-CAT-11:
    - Reemplazo exitoso: nuevo URL en registro, id/orden/repuesto_id sin cambio
    - updated_at poblado tras reemplazo
    - Rechazo por tipo de archivo inválido (422)
    - Rechazo por tamaño > 5 MB (422)
    - Rechazo por rol no autorizado — VENDEDOR (403)
    - Rechazo por imagen_id no encontrado (404)
    - Rechazo por imagen que no pertenece al repuesto (404)
  EP-CAT-12:
    - Reordenamiento exitoso: nuevo orden reflejado en EP-CAT-02 siguiente llamada
    - Rechazo por lista con IDs faltantes — mensaje incluye cuáles
    - Rechazo por lista con IDs foráneos — mensaje incluye cuáles
    - Rechazo por lista con mezcla faltantes + foráneos
    - Rechazo por rol no autorizado — VENDEDOR (403)
    - Rechazo por repuesto no encontrado (404)
"""
from __future__ import annotations

import pytest
from decimal import Decimal

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    UniversoRepuesto,
)
from tests.integration.conftest import make_test_token

_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16
_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


@pytest.fixture
async def repuesto_con_imagenes(app_client):
    """Repuesto con 3 imágenes pre-cargadas. Expone imagen_ids en orden de creación."""
    repo = app_client.app.state.catalogo_repo
    repuesto = Repuesto(
        codigo="REP-REORD-001",
        nombre="Filtro reordenable",
        universo=UniversoRepuesto.MOTOTAXI_3R,
        modelo="Bajaj RE",
        año=2022,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("30.00"),
    )
    await repo.guardar(repuesto)
    app_client._codigo = repuesto.codigo

    imagen_ids = []
    for i in range(3):
        r = await app_client.post(
            f"/v1/repuestos/{repuesto.codigo}/imagenes",
            files={"archivo": (f"img{i}.jpg", _JPEG, "image/jpeg")},
        )
        assert r.status_code == 201, r.text
        imagen_ids.append(r.json()["data"]["imagen_id"])

    app_client._imagen_ids = imagen_ids
    return app_client


@pytest.fixture
async def repuesto_simple(app_client):
    """Repuesto con 1 imagen."""
    repo = app_client.app.state.catalogo_repo
    repuesto = Repuesto(
        codigo="REP-SIMPLE-001",
        nombre="Repuesto simple",
        universo=UniversoRepuesto.MOTOTAXI_3R,
        modelo="Bajaj RE",
        año=2021,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("20.00"),
    )
    await repo.guardar(repuesto)

    r = await app_client.post(
        f"/v1/repuestos/{repuesto.codigo}/imagenes",
        files={"archivo": ("original.jpg", _JPEG, "image/jpeg")},
    )
    assert r.status_code == 201
    app_client._codigo = repuesto.codigo
    app_client._imagen_id = r.json()["data"]["imagen_id"]
    app_client._url_original = r.json()["data"]["url"]
    return app_client


# ── EP-CAT-11 — Reemplazar imagen ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reemplazo_exitoso_mantiene_id_y_orden(repuesto_simple):
    """Reemplazo exitoso: mismo imagen_id y orden, URL cambiada."""
    imagen_id = repuesto_simple._imagen_id
    url_original = repuesto_simple._url_original

    r = await repuesto_simple.put(
        f"/v1/repuestos/{repuesto_simple._codigo}/imagenes/{imagen_id}",
        files={"archivo": ("nueva.jpg", _JPEG, "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]

    assert data["imagen_id"] == imagen_id
    assert data["orden"] == 0
    assert data["url"] != url_original
    assert data["updated_at"] is not None


@pytest.mark.asyncio
async def test_reemplazo_url_anterior_no_aparece_en_catalogo(repuesto_simple):
    """Tras el reemplazo, EP-CAT-02 devuelve la nueva URL, no la original."""
    imagen_id = repuesto_simple._imagen_id
    url_original = repuesto_simple._url_original

    r_replace = await repuesto_simple.put(
        f"/v1/repuestos/{repuesto_simple._codigo}/imagenes/{imagen_id}",
        files={"archivo": ("nueva.png", _PNG, "image/png")},
    )
    nueva_url = r_replace.json()["data"]["url"]

    r_detalle = await repuesto_simple.get(f"/v1/repuestos/{repuesto_simple._codigo}")
    imagenes = r_detalle.json()["data"]["imagenes"]

    urls = [img["url"] for img in imagenes]
    assert nueva_url in urls
    assert url_original not in urls


@pytest.mark.asyncio
async def test_reemplazo_rechaza_tipo_invalido(repuesto_simple):
    """EP-CAT-11: tipo de archivo inválido → 422 VALIDACION_FALLIDA."""
    r = await repuesto_simple.put(
        f"/v1/repuestos/{repuesto_simple._codigo}/imagenes/{repuesto_simple._imagen_id}",
        files={"archivo": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "VALIDACION_FALLIDA"


@pytest.mark.asyncio
async def test_reemplazo_rechaza_tamanio_excedido(repuesto_simple):
    """EP-CAT-11: archivo > 5 MB → 422 VALIDACION_FALLIDA."""
    cinco_mb_mas_uno = b"\xff\xd8\xff\xe0" + b"X" * (5 * 1024 * 1024 + 1)
    r = await repuesto_simple.put(
        f"/v1/repuestos/{repuesto_simple._codigo}/imagenes/{repuesto_simple._imagen_id}",
        files={"archivo": ("grande.jpg", cinco_mb_mas_uno, "image/jpeg")},
    )
    assert r.status_code == 422
    assert "5 MB" in r.json()["detail"]["error"]["message"]


@pytest.mark.asyncio
async def test_reemplazo_rechaza_rol_no_autorizado(repuesto_simple):
    """EP-CAT-11: VENDEDOR → 403."""
    token = make_test_token(repuesto_simple._test_private_pem, "VENDEDOR")
    r = await repuesto_simple.put(
        f"/v1/repuestos/{repuesto_simple._codigo}/imagenes/{repuesto_simple._imagen_id}",
        files={"archivo": ("nueva.jpg", _JPEG, "image/jpeg")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reemplazo_imagen_inexistente(repuesto_simple):
    """EP-CAT-11: imagen_id no encontrado → 404."""
    r = await repuesto_simple.put(
        f"/v1/repuestos/{repuesto_simple._codigo}/imagenes/id-no-existe",
        files={"archivo": ("nueva.jpg", _JPEG, "image/jpeg")},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_reemplazo_imagen_de_otro_repuesto(app_client):
    """EP-CAT-11: imagen que pertenece a otro repuesto → 404."""
    repo = app_client.app.state.catalogo_repo

    rep_a = Repuesto(
        codigo="REP-A-001", nombre="A", universo=UniversoRepuesto.MOTOTAXI_3R,
        modelo="M", año=2020, categoria=CategoriaRepuesto.MOTOR, precio_venta=Decimal("10.00"),
    )
    rep_b = Repuesto(
        codigo="REP-B-001", nombre="B", universo=UniversoRepuesto.MOTOTAXI_3R,
        modelo="M", año=2020, categoria=CategoriaRepuesto.MOTOR, precio_venta=Decimal("10.00"),
    )
    await repo.guardar(rep_a)
    await repo.guardar(rep_b)

    r_img = await app_client.post(
        "/v1/repuestos/REP-A-001/imagenes",
        files={"archivo": ("img.jpg", _JPEG, "image/jpeg")},
    )
    imagen_id_de_a = r_img.json()["data"]["imagen_id"]

    r = await app_client.put(
        f"/v1/repuestos/REP-B-001/imagenes/{imagen_id_de_a}",
        files={"archivo": ("nueva.jpg", _JPEG, "image/jpeg")},
    )
    assert r.status_code == 404


# ── EP-CAT-12 — Reordenar imágenes ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_reordenamiento_exitoso_persistido(repuesto_con_imagenes):
    """EP-CAT-12: orden invertido → EP-CAT-02 devuelve el nuevo orden."""
    codigo = repuesto_con_imagenes._codigo
    ids_originales = repuesto_con_imagenes._imagen_ids  # [id0, id1, id2]
    ids_invertidos = list(reversed(ids_originales))

    r = await repuesto_con_imagenes.put(
        f"/v1/repuestos/{codigo}/imagenes/orden",
        json={"imagenes_ordenadas": ids_invertidos},
    )
    assert r.status_code == 200, r.text

    # Verificar que el orden nuevo se refleja en EP-CAT-02
    r_detalle = await repuesto_con_imagenes.get(f"/v1/repuestos/{codigo}")
    imagenes = r_detalle.json()["data"]["imagenes"]

    ids_devueltos = [img["imagen_id"] for img in imagenes]
    assert ids_devueltos == ids_invertidos

    # Orden numérico asignado correctamente
    assert imagenes[0]["orden"] == 0
    assert imagenes[1]["orden"] == 1
    assert imagenes[2]["orden"] == 2


@pytest.mark.asyncio
async def test_reordenamiento_imagen_principal_cambia(repuesto_con_imagenes):
    """EP-CAT-12: el id que pasa a orden=0 se convierte en imagen principal."""
    codigo = repuesto_con_imagenes._codigo
    ids = repuesto_con_imagenes._imagen_ids
    nuevo_orden = [ids[2], ids[0], ids[1]]

    await repuesto_con_imagenes.put(
        f"/v1/repuestos/{codigo}/imagenes/orden",
        json={"imagenes_ordenadas": nuevo_orden},
    )

    r = await repuesto_con_imagenes.get(f"/v1/repuestos/{codigo}")
    imagenes = r.json()["data"]["imagenes"]
    assert imagenes[0]["imagen_id"] == ids[2]
    assert imagenes[0]["orden"] == 0


@pytest.mark.asyncio
async def test_reordenamiento_rechaza_lista_incompleta(repuesto_con_imagenes):
    """EP-CAT-12: lista con IDs faltantes → 422 con detalle de cuáles faltan."""
    codigo = repuesto_con_imagenes._codigo
    ids = repuesto_con_imagenes._imagen_ids

    r = await repuesto_con_imagenes.put(
        f"/v1/repuestos/{codigo}/imagenes/orden",
        json={"imagenes_ordenadas": [ids[0], ids[1]]},  # falta ids[2]
    )
    assert r.status_code == 422, r.text
    msg = r.json()["detail"]["error"]["message"]
    assert "faltantes" in msg
    assert ids[2] in msg


@pytest.mark.asyncio
async def test_reordenamiento_rechaza_id_foraneo(repuesto_con_imagenes):
    """EP-CAT-12: lista con ID que no pertenece al repuesto → 422 con detalle."""
    codigo = repuesto_con_imagenes._codigo
    ids = repuesto_con_imagenes._imagen_ids

    r = await repuesto_con_imagenes.put(
        f"/v1/repuestos/{codigo}/imagenes/orden",
        json={"imagenes_ordenadas": [ids[0], ids[1], "id-de-otro-repuesto"]},
    )
    assert r.status_code == 422, r.text
    msg = r.json()["detail"]["error"]["message"]
    assert "no pertenecen" in msg
    assert "id-de-otro-repuesto" in msg


@pytest.mark.asyncio
async def test_reordenamiento_rechaza_mezcla_faltante_y_foraneo(repuesto_con_imagenes):
    """EP-CAT-12: mezcla de faltantes + foráneos → 422 con ambos en el mensaje."""
    codigo = repuesto_con_imagenes._codigo
    ids = repuesto_con_imagenes._imagen_ids

    r = await repuesto_con_imagenes.put(
        f"/v1/repuestos/{codigo}/imagenes/orden",
        json={"imagenes_ordenadas": [ids[0], ids[1], "id-foraneo"]},  # falta ids[2], hay foráneo
    )
    assert r.status_code == 422
    msg = r.json()["detail"]["error"]["message"]
    assert "faltantes" in msg
    assert "no pertenecen" in msg


@pytest.mark.asyncio
async def test_reordenamiento_rechaza_rol_no_autorizado(repuesto_con_imagenes):
    """EP-CAT-12: VENDEDOR → 403."""
    token = make_test_token(repuesto_con_imagenes._test_private_pem, "VENDEDOR")
    codigo = repuesto_con_imagenes._codigo
    ids = repuesto_con_imagenes._imagen_ids

    r = await repuesto_con_imagenes.put(
        f"/v1/repuestos/{codigo}/imagenes/orden",
        json={"imagenes_ordenadas": ids},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_reordenamiento_repuesto_inexistente(app_client):
    """EP-CAT-12: repuesto no encontrado → 404."""
    r = await app_client.put(
        "/v1/repuestos/REP-NO-EXISTE/imagenes/orden",
        json={"imagenes_ordenadas": ["id1", "id2"]},
    )
    assert r.status_code == 404

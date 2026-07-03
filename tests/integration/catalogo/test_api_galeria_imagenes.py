"""
Tests de integración — EP-CAT-08 y EP-CAT-09 (galería de imágenes por repuesto).
También verifica que EP-CAT-01 y EP-CAT-02 incluyen imágenes en su respuesta.

Casos cubiertos:
  - Subida exitosa de imagen (jpg, png, webp)
  - Rechazo por tipo de archivo inválido
  - Rechazo por tamaño superior a 5 MB
  - Rechazo por rol no autorizado (VENDEDOR no puede subir)
  - Eliminación exitosa de imagen
  - Orden de visualización tras múltiples subidas (la primera es imagen principal)
  - EP-CAT-01 incluye imagen_principal_url de la primera imagen
  - EP-CAT-02 incluye lista completa de imágenes ordenadas
"""
import pytest
from decimal import Decimal
from httpx import AsyncClient

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    UniversoRepuesto,
)
from tests.integration.conftest import make_test_token

_JPEG_MINIMO = b"\xff\xd8\xff\xe0" + b"\x00" * 16  # cabecera JPEG mínima válida


@pytest.fixture
async def catalogo_con_repuesto(app_client):
    """Repuesto de prueba pre-cargado."""
    repo = app_client.app.state.catalogo_repo
    repuesto = Repuesto(
        codigo="REP-IMG-001",
        nombre="Filtro con galería",
        universo=UniversoRepuesto.MOTOTAXI_3R,
        modelo="Bajaj RE",
        año=2021,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("45.00"),
    )
    await repo.guardar(repuesto)
    app_client._repuesto_codigo = repuesto.codigo
    return app_client


# ── EP-CAT-08 — Subir imagen ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_subir_imagen_exitosa_jpg(catalogo_con_repuesto):
    """EP-CAT-08: subida exitosa de imagen JPG."""
    codigo = catalogo_con_repuesto._repuesto_codigo
    response = await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("foto.jpg", _JPEG_MINIMO, "image/jpeg")},
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert "imagen_id" in data
    assert "url" in data
    assert data["orden"] == 0


@pytest.mark.asyncio
async def test_subir_imagen_exitosa_png(catalogo_con_repuesto):
    """EP-CAT-08: subida exitosa de imagen PNG."""
    codigo = catalogo_con_repuesto._repuesto_codigo
    response = await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("foto.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 8, "image/png")},
    )
    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_subir_imagen_rechaza_tipo_invalido(catalogo_con_repuesto):
    """EP-CAT-08: tipo de archivo inválido (PDF) → 422."""
    codigo = catalogo_con_repuesto._repuesto_codigo
    response = await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 422
    error = response.json()["detail"]["error"]
    assert error["code"] == "VALIDACION_FALLIDA"
    assert "image/jpeg" in error["message"]


@pytest.mark.asyncio
async def test_subir_imagen_rechaza_tamanio_excedido(catalogo_con_repuesto):
    """EP-CAT-08: imagen > 5 MB → 422."""
    codigo = catalogo_con_repuesto._repuesto_codigo
    cinco_mb_mas_uno = b"\xff\xd8\xff\xe0" + b"X" * (5 * 1024 * 1024 + 1)
    response = await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("grande.jpg", cinco_mb_mas_uno, "image/jpeg")},
    )
    assert response.status_code == 422
    error = response.json()["detail"]["error"]
    assert error["code"] == "VALIDACION_FALLIDA"
    assert "5 MB" in error["message"]


@pytest.mark.asyncio
async def test_subir_imagen_rechaza_rol_no_autorizado(catalogo_con_repuesto):
    """EP-CAT-08: VENDEDOR no puede subir imágenes → 403."""
    codigo = catalogo_con_repuesto._repuesto_codigo
    token_vendedor = make_test_token(
        catalogo_con_repuesto._test_private_pem, "VENDEDOR"
    )
    response = await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("foto.jpg", _JPEG_MINIMO, "image/jpeg")},
        headers={"Authorization": f"Bearer {token_vendedor}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_subir_imagen_repuesto_inexistente(catalogo_con_repuesto):
    """EP-CAT-08: repuesto no encontrado → 404."""
    response = await catalogo_con_repuesto.post(
        "/v1/repuestos/REP-NO-EXISTE/imagenes",
        files={"archivo": ("foto.jpg", _JPEG_MINIMO, "image/jpeg")},
    )
    assert response.status_code == 404


# ── Orden de visualización ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_orden_imagenes_tras_multiples_subidas(catalogo_con_repuesto):
    """Primera imagen subida tiene orden=0 (imagen principal); la segunda orden=1."""
    codigo = catalogo_con_repuesto._repuesto_codigo

    r1 = await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("foto1.jpg", _JPEG_MINIMO, "image/jpeg")},
    )
    r2 = await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("foto2.jpg", _JPEG_MINIMO, "image/jpeg")},
    )
    assert r1.json()["data"]["orden"] == 0
    assert r2.json()["data"]["orden"] == 1


# ── EP-CAT-09 — Eliminar imagen ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_eliminar_imagen_exitosa(catalogo_con_repuesto):
    """EP-CAT-09: eliminar imagen existente → 200."""
    codigo = catalogo_con_repuesto._repuesto_codigo
    r_subida = await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("foto.jpg", _JPEG_MINIMO, "image/jpeg")},
    )
    imagen_id = r_subida.json()["data"]["imagen_id"]

    r_elimina = await catalogo_con_repuesto.delete(
        f"/v1/repuestos/{codigo}/imagenes/{imagen_id}"
    )
    assert r_elimina.status_code == 200
    assert r_elimina.json()["data"]["eliminada"] is True


@pytest.mark.asyncio
async def test_eliminar_imagen_inexistente(catalogo_con_repuesto):
    """EP-CAT-09: imagen no encontrada → 404."""
    codigo = catalogo_con_repuesto._repuesto_codigo
    response = await catalogo_con_repuesto.delete(
        f"/v1/repuestos/{codigo}/imagenes/id-no-existe"
    )
    assert response.status_code == 404


# ── EP-CAT-01 y EP-CAT-02 incluyen imágenes ──────────────────────────────────

@pytest.mark.asyncio
async def test_ep_cat_01_incluye_imagen_principal(catalogo_con_repuesto):
    """EP-CAT-01: imagen_principal_url aparece tras subir la primera imagen."""
    codigo = catalogo_con_repuesto._repuesto_codigo

    # Sin imagen aún — imagen_principal_url debe ser null
    r_sin = await catalogo_con_repuesto.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r"}
    )
    item_sin = next(
        (r for r in r_sin.json()["data"]["repuestos"] if r["codigo"] == codigo), None
    )
    assert item_sin is not None
    assert item_sin["imagen_principal_url"] is None

    # Subir imagen
    r_sub = await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("foto.jpg", _JPEG_MINIMO, "image/jpeg")},
    )
    url_esperada = r_sub.json()["data"]["url"]

    # Con imagen — imagen_principal_url debe estar poblada
    r_con = await catalogo_con_repuesto.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r"}
    )
    item_con = next(
        (r for r in r_con.json()["data"]["repuestos"] if r["codigo"] == codigo), None
    )
    assert item_con["imagen_principal_url"] == url_esperada


@pytest.mark.asyncio
async def test_ep_cat_02_incluye_lista_imagenes(catalogo_con_repuesto):
    """EP-CAT-02: imagenes aparece como lista tras subir imágenes."""
    codigo = catalogo_con_repuesto._repuesto_codigo

    # Sin imágenes — lista vacía
    r_sin = await catalogo_con_repuesto.get(f"/v1/repuestos/{codigo}")
    assert r_sin.json()["data"]["imagenes"] == []

    # Subir dos imágenes
    await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("a.jpg", _JPEG_MINIMO, "image/jpeg")},
    )
    await catalogo_con_repuesto.post(
        f"/v1/repuestos/{codigo}/imagenes",
        files={"archivo": ("b.jpg", _JPEG_MINIMO, "image/jpeg")},
    )

    r_con = await catalogo_con_repuesto.get(f"/v1/repuestos/{codigo}")
    imagenes = r_con.json()["data"]["imagenes"]
    assert len(imagenes) == 2
    assert imagenes[0]["orden"] == 0
    assert imagenes[1]["orden"] == 1
    assert "imagen_id" in imagenes[0]
    assert "url" in imagenes[0]

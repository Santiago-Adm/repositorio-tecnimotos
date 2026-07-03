"""
Tests de integración — subida de imagen única de repuesto (campo imagen_url).
Distinto de la galería EP-CAT-08/09/11/12 (tabla imagen_repuesto, no usada
por este endpoint). Usa InMemoryImagenStorage — no golpea R2 real.
"""
import pytest
from decimal import Decimal

from tests.integration.conftest import make_test_token
from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    UniversoRepuesto,
)

_JPEG_1X1 = bytes.fromhex(
    "ffd8ffe000104a46494600010101006000600000ffdb004300030202020"
    "202030202020303030304060404040404080605050609080a0a09080909"
    "0a0c0f0c0a0b0e0b09090d110d0e0f101011100a0c12131210130f101010"
    "ffc9000b080001000101011100ffcc000600101005ffda0008010100003f00d2cf20"
    "ffd9"
)


@pytest.fixture
async def client_con_repuesto(app_client):
    repo = app_client.app.state.catalogo_repo
    repuesto = Repuesto(
        codigo="IMG-001",
        nombre="Repuesto con imagen",
        universo=UniversoRepuesto.MOTOLINEAL,
        modelo="TVS Apache",
        año=2022,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("50.00"),
    )
    await repo.guardar(repuesto)
    return app_client


class TestSubirImagenUnica:
    async def test_admin_sube_imagen_exitosamente(self, client_con_repuesto):
        token = make_test_token(client_con_repuesto._test_private_pem, "ADMINISTRADOR")
        response = await client_con_repuesto.post(
            "/v1/repuestos/IMG-001/imagen",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("foto.jpg", _JPEG_1X1, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["codigo"] == "IMG-001"
        assert data["imagen_url"].endswith("repuestos/IMG-001/1.jpg")

    async def test_superadmin_sube_imagen_exitosamente(self, client_con_repuesto):
        token = make_test_token(client_con_repuesto._test_private_pem, "SUPERADMIN")
        response = await client_con_repuesto.post(
            "/v1/repuestos/IMG-001/imagen",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("foto.png", _JPEG_1X1, "image/png")},
        )
        assert response.status_code == 200
        assert response.json()["data"]["imagen_url"].endswith("repuestos/IMG-001/1.png")

    async def test_reemplazo_pisa_la_key_anterior(self, client_con_repuesto):
        token = make_test_token(client_con_repuesto._test_private_pem, "ADMINISTRADOR")
        r1 = await client_con_repuesto.post(
            "/v1/repuestos/IMG-001/imagen",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("a.jpg", _JPEG_1X1, "image/jpeg")},
        )
        r2 = await client_con_repuesto.post(
            "/v1/repuestos/IMG-001/imagen",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("b.jpg", _JPEG_1X1, "image/jpeg")},
        )
        assert r1.json()["data"]["imagen_url"] == r2.json()["data"]["imagen_url"]

    async def test_rol_no_autorizado_403(self, client_con_repuesto):
        token = make_test_token(client_con_repuesto._test_private_pem, "VENDEDOR")
        response = await client_con_repuesto.post(
            "/v1/repuestos/IMG-001/imagen",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("foto.jpg", _JPEG_1X1, "image/jpeg")},
        )
        assert response.status_code == 403

    async def test_tipo_invalido_422(self, client_con_repuesto):
        token = make_test_token(client_con_repuesto._test_private_pem, "ADMINISTRADOR")
        response = await client_con_repuesto.post(
            "/v1/repuestos/IMG-001/imagen",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("foto.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert response.status_code == 422

    async def test_tamanio_excedido_422(self, client_con_repuesto):
        token = make_test_token(client_con_repuesto._test_private_pem, "ADMINISTRADOR")
        contenido_grande = b"\xff" * (5 * 1024 * 1024 + 1)
        response = await client_con_repuesto.post(
            "/v1/repuestos/IMG-001/imagen",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("foto.jpg", contenido_grande, "image/jpeg")},
        )
        assert response.status_code == 422

    async def test_repuesto_inexistente_404(self, client_con_repuesto):
        token = make_test_token(client_con_repuesto._test_private_pem, "ADMINISTRADOR")
        response = await client_con_repuesto.post(
            "/v1/repuestos/NO-EXISTE/imagen",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("foto.jpg", _JPEG_1X1, "image/jpeg")},
        )
        assert response.status_code == 404

    async def test_get_repuesto_refleja_imagen_url(self, client_con_repuesto):
        token = make_test_token(client_con_repuesto._test_private_pem, "ADMINISTRADOR")
        await client_con_repuesto.post(
            "/v1/repuestos/IMG-001/imagen",
            headers={"Authorization": f"Bearer {token}"},
            files={"archivo": ("foto.jpg", _JPEG_1X1, "image/jpeg")},
        )
        response = await client_con_repuesto.get("/v1/repuestos/IMG-001")
        assert response.json()["data"]["imagen_url"].endswith("repuestos/IMG-001/1.jpg")

    async def test_repuesto_sin_imagen_devuelve_null(self, client_con_repuesto):
        response = await client_con_repuesto.get("/v1/repuestos/IMG-001")
        assert response.json()["data"]["imagen_url"] is None

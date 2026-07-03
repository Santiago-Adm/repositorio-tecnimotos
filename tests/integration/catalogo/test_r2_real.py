"""
Tests de integración real contra Cloudflare R2.
Se saltan automáticamente si las credenciales R2 no están presentes
en el entorno — no fallan ni hacen mock silencioso.

Para ejecutar localmente con credenciales reales:
  pytest tests/integration/catalogo/test_r2_real.py -v
"""
from __future__ import annotations

import os

import httpx
import pytest
from dotenv import load_dotenv

from src.catalogo.infrastructure.storage.r2_imagen_storage import R2ImagenStorage

# pydantic_settings lee .env en tiempo de ejecución, pero pytestmark se evalúa
# al importar el módulo (antes del primer fixture). load_dotenv() asegura que
# os.getenv() vea las variables definidas en .env local.
load_dotenv()

_R2_VARS = [
    "R2_ENDPOINT",
    "R2_BUCKET_NAME",
    "R2_PUBLIC_URL",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
]

_SKIP_REASON = (
    "requiere credenciales R2 reales, no disponibles en este entorno "
    f"(faltan: {', '.join(v for v in _R2_VARS if not os.getenv(v))})"
)

pytestmark = pytest.mark.skipif(
    not all(os.getenv(v) for v in _R2_VARS),
    reason=_SKIP_REASON,
)

_JPEG_MINIMO = b"\xff\xd8\xff\xe0" + b"\x00" * 16


@pytest.fixture
def r2_storage() -> R2ImagenStorage:
    return R2ImagenStorage(
        endpoint_url=os.environ["R2_ENDPOINT"],
        access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        bucket_name=os.environ["R2_BUCKET_NAME"],
        public_url=os.environ["R2_PUBLIC_URL"],
    )


@pytest.mark.asyncio
async def test_subir_objeto_url_publica_responde_200(r2_storage: R2ImagenStorage) -> None:
    """Sube archivo de prueba y confirma que la URL pública retornada responde 200."""
    url = await r2_storage.subir(_JPEG_MINIMO, "test_integracion.jpg", "image/jpeg")

    assert url.startswith(os.environ["R2_PUBLIC_URL"])
    assert "R2_ENDPOINT" not in url
    assert "r2.cloudflarestorage.com" not in url

    async with httpx.AsyncClient(follow_redirects=True) as client:
        r = await client.get(url)
    assert r.status_code == 200
    assert r.content == _JPEG_MINIMO

    # Limpieza
    await r2_storage.eliminar(url)


@pytest.mark.asyncio
async def test_eliminar_objeto_url_ya_no_responde(r2_storage: R2ImagenStorage) -> None:
    """Sube, elimina y confirma que la URL pública retorna 403/404 tras la eliminación."""
    url = await r2_storage.subir(_JPEG_MINIMO, "test_eliminar.jpg", "image/jpeg")

    await r2_storage.eliminar(url)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        r = await client.get(url)
    assert r.status_code in (403, 404), (
        f"Se esperaba 403 o 404 tras eliminar, pero la URL retornó {r.status_code}"
    )


_PNG_MINIMO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


@pytest.mark.asyncio
async def test_reemplazo_referencia_anterior_invalida_nueva_accesible(
    r2_storage: R2ImagenStorage,
) -> None:
    """EP-CAT-11 real: sube imagen inicial, sube reemplazo, confirma que:
    - la URL anterior deja de responder (403/404)
    - la URL nueva responde 200 con el contenido correcto."""
    # 1. Subir imagen inicial
    url_original = await r2_storage.subir(_JPEG_MINIMO, "ep11_original.jpg", "image/jpeg")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        r_antes = await client.get(url_original)
    assert r_antes.status_code == 200, "URL original debe responder 200 antes del reemplazo"

    # 2. Subir imagen de reemplazo (key nueva)
    url_nueva = await r2_storage.subir(_PNG_MINIMO, "ep11_reemplazo.png", "image/png")
    assert url_nueva != url_original, "El reemplazo debe generar una key distinta en R2"

    # 3. Eliminar objeto anterior (simula lo que hace ReemplazarImagenUseCase tras actualizar DB)
    await r2_storage.eliminar(url_original)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        r_viejo = await client.get(url_original)
        r_nuevo = await client.get(url_nueva)

    assert r_viejo.status_code in (403, 404), (
        f"URL anterior debe ser inaccesible tras eliminar (got {r_viejo.status_code})"
    )
    assert r_nuevo.status_code == 200, (
        f"URL nueva debe responder 200 (got {r_nuevo.status_code})"
    )
    assert r_nuevo.content == _PNG_MINIMO, "Contenido nuevo debe coincidir exactamente"

    # Limpieza
    await r2_storage.eliminar(url_nueva)

"""
Tests unitarios para R2ImagenStorage — no requieren red ni credenciales reales.
Verifican la lógica de construcción de keys y URLs.
"""
from __future__ import annotations

import re

import pytest

from src.catalogo.infrastructure.storage.r2_imagen_storage import R2ImagenStorage


@pytest.fixture
def storage() -> R2ImagenStorage:
    return R2ImagenStorage(
        endpoint_url="https://fake.r2.cloudflarestorage.com",
        access_key_id="fake-key",
        secret_access_key="fake-secret",
        bucket_name="fake-bucket",
        public_url="https://pub.example.r2.dev",
    )


class TestBuildKey:
    def test_formato_repuestos_prefix(self, storage: R2ImagenStorage) -> None:
        key = storage._build_key("foto.jpg")
        assert key.startswith("repuestos/")

    def test_extension_preservada_en_minusculas(self, storage: R2ImagenStorage) -> None:
        assert storage._build_key("foto.JPG").endswith(".jpg")
        assert storage._build_key("imagen.PNG").endswith(".png")
        assert storage._build_key("foto.WebP").endswith(".webp")

    def test_nombre_original_no_aparece_en_key(self, storage: R2ImagenStorage) -> None:
        key = storage._build_key("nombre_cliente_secreto.jpg")
        assert "nombre_cliente_secreto" not in key

    def test_keys_distintas_para_mismo_nombre(self, storage: R2ImagenStorage) -> None:
        k1 = storage._build_key("foto.jpg")
        k2 = storage._build_key("foto.jpg")
        assert k1 != k2

    def test_formato_uuid_hex(self, storage: R2ImagenStorage) -> None:
        key = storage._build_key("foto.jpg")
        # repuestos/{32 chars hex}.jpg
        assert re.fullmatch(r"repuestos/[0-9a-f]{32}\.jpg", key)

    def test_sin_extension_usa_bin(self, storage: R2ImagenStorage) -> None:
        key = storage._build_key("archivo_sin_extension")
        assert key.endswith(".bin")


class TestKeyFromUrl:
    def test_extrae_key_correctamente(self, storage: R2ImagenStorage) -> None:
        url = "https://pub.example.r2.dev/repuestos/abc123.jpg"
        assert storage._key_from_url(url) == "repuestos/abc123.jpg"

    def test_public_url_sin_trailing_slash(self) -> None:
        s = R2ImagenStorage(
            endpoint_url="https://fake.r2.cloudflarestorage.com",
            access_key_id="x",
            secret_access_key="x",
            bucket_name="b",
            public_url="https://pub.example.r2.dev/",  # trailing slash
        )
        url = "https://pub.example.r2.dev/repuestos/abc123.jpg"
        assert s._key_from_url(url) == "repuestos/abc123.jpg"

    def test_round_trip_subir_key_url(self, storage: R2ImagenStorage) -> None:
        """La key que genera _build_key se recupera íntegra desde la URL pública."""
        key = storage._build_key("foto.jpg")
        url = f"{storage._public_url}/{key}"
        assert storage._key_from_url(url) == key

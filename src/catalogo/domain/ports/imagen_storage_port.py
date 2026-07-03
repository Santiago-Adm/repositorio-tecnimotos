"""
Puerto para almacenamiento de objetos de imagen (03 §3.5 patrón env var).
Proveedor: Cloudflare R2 (compatible S3) — implementado en sesión 2026-06-28
via R2ImagenStorage (infrastructure/storage/r2_imagen_storage.py).
Fallback a InMemoryImagenStorage cuando R2_ENDPOINT no está configurado.
Variables de entorno:
  R2_ACCOUNT_ID, R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
  R2_BUCKET_NAME, R2_PUBLIC_URL
"""
from __future__ import annotations

from typing import Protocol


class ImagenStoragePort(Protocol):
    async def subir(
        self, contenido: bytes, nombre_archivo: str, tipo_contenido: str
    ) -> str:
        """Sube el archivo y retorna la URL pública permanente."""
        ...

    async def eliminar(self, url: str) -> None:
        """Elimina el objeto referenciado por la URL."""
        ...

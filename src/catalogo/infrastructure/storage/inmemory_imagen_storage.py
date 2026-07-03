"""
Adaptador InMemory para ImagenStoragePort.
No persiste archivos — genera URLs ficticias para tests.
En producción reemplazar por el adaptador Cloudflare R2.
"""
from __future__ import annotations

import uuid


class InMemoryImagenStorage:
    async def subir(self, contenido: bytes, nombre_archivo: str, tipo_contenido: str) -> str:
        token = uuid.uuid4().hex[:8]
        return f"inmemory://storage/{token}/{nombre_archivo}"

    async def subir_con_key(self, contenido: bytes, key: str, tipo_contenido: str) -> str:
        return f"inmemory://storage/{key}"

    async def eliminar(self, url: str) -> None:
        pass  # noop en InMemory

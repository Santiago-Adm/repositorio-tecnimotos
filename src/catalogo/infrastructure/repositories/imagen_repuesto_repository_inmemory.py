"""InMemoryImagenRepuestoRepository — implementación en memoria para tests."""
from __future__ import annotations

from typing import Optional

from src.catalogo.domain.models.imagen_repuesto import ImagenRepuesto


class InMemoryImagenRepuestoRepository:
    def __init__(self) -> None:
        self._store: dict[str, ImagenRepuesto] = {}

    async def guardar(self, imagen: ImagenRepuesto) -> ImagenRepuesto:
        self._store[imagen.id] = imagen
        return imagen

    async def actualizar(self, imagen: ImagenRepuesto) -> ImagenRepuesto:
        self._store[imagen.id] = imagen
        return imagen

    async def listar_por_repuesto(self, repuesto_id: str) -> list[ImagenRepuesto]:
        imagenes = [img for img in self._store.values() if img.repuesto_id == repuesto_id]
        return sorted(imagenes, key=lambda img: img.orden)

    async def obtener_por_id(self, imagen_id: str) -> Optional[ImagenRepuesto]:
        return self._store.get(imagen_id)

    async def eliminar(self, imagen_id: str) -> None:
        self._store.pop(imagen_id, None)

    async def siguiente_orden(self, repuesto_id: str) -> int:
        existentes = await self.listar_por_repuesto(repuesto_id)
        return len(existentes)

    async def reordenar_imagenes(self, actualizaciones: list[tuple[str, int]]) -> None:
        for imagen_id, nuevo_orden in actualizaciones:
            if imagen_id in self._store:
                self._store[imagen_id].orden = nuevo_orden

    def limpiar(self) -> None:
        self._store.clear()

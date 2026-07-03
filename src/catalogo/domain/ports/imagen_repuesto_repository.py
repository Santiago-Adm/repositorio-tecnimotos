"""Puerto de repositorio para ImagenRepuesto."""
from __future__ import annotations

from typing import Optional, Protocol

from src.catalogo.domain.models.imagen_repuesto import ImagenRepuesto


class ImagenRepuestoRepository(Protocol):
    async def guardar(self, imagen: ImagenRepuesto) -> ImagenRepuesto: ...

    async def actualizar(self, imagen: ImagenRepuesto) -> ImagenRepuesto:
        """Persiste cambios sobre una imagen existente (EP-CAT-11 reemplazo de URL)."""
        ...

    async def listar_por_repuesto(self, repuesto_id: str) -> list[ImagenRepuesto]:
        """Retorna imágenes ordenadas por campo `orden` ASC."""
        ...

    async def obtener_por_id(self, imagen_id: str) -> Optional[ImagenRepuesto]: ...

    async def eliminar(self, imagen_id: str) -> None: ...

    async def siguiente_orden(self, repuesto_id: str) -> int:
        """Retorna el próximo valor de orden disponible para el repuesto."""
        ...

    async def reordenar_imagenes(self, actualizaciones: list[tuple[str, int]]) -> None:
        """Aplica los nuevos valores de orden a las imágenes indicadas de forma atómica.
        actualizaciones: lista de (imagen_id, nuevo_orden)."""
        ...

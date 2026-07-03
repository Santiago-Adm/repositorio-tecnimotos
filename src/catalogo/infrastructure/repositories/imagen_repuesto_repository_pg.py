"""
Repositorio PostgreSQL para ImagenRepuesto — implementa ImagenRepuestoRepository Protocol.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.catalogo.domain.models.imagen_repuesto import ImagenRepuesto
from src.catalogo.infrastructure.repositories.models.imagen_repuesto_model import (
    ImagenRepuestoModel,
)


class ImagenRepuestoRepositoryPG:
    """Implementación SQLAlchemy del Protocol ImagenRepuestoRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, imagen: ImagenRepuesto) -> ImagenRepuesto:
        model = self._to_model(imagen)
        self._session.add(model)
        await self._session.flush()
        return imagen

    async def actualizar(self, imagen: ImagenRepuesto) -> ImagenRepuesto:
        stmt = select(ImagenRepuestoModel).where(ImagenRepuestoModel.id == imagen.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Imagen {imagen.id} no encontrada para actualizar")
        model.url = imagen.url
        model.orden = imagen.orden
        model.updated_at = imagen.updated_at
        await self._session.flush()
        return imagen

    async def listar_por_repuesto(self, repuesto_id: str) -> list[ImagenRepuesto]:
        stmt = (
            select(ImagenRepuestoModel)
            .where(ImagenRepuestoModel.repuesto_id == repuesto_id)
            .order_by(ImagenRepuestoModel.orden.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def obtener_por_id(self, imagen_id: str) -> Optional[ImagenRepuesto]:
        stmt = select(ImagenRepuestoModel).where(ImagenRepuestoModel.id == imagen_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def eliminar(self, imagen_id: str) -> None:
        stmt = select(ImagenRepuestoModel).where(ImagenRepuestoModel.id == imagen_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    async def siguiente_orden(self, repuesto_id: str) -> int:
        existentes = await self.listar_por_repuesto(repuesto_id)
        return len(existentes)

    async def reordenar_imagenes(self, actualizaciones: list[tuple[str, int]]) -> None:
        for imagen_id, nuevo_orden in actualizaciones:
            stmt = select(ImagenRepuestoModel).where(ImagenRepuestoModel.id == imagen_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            if model is not None:
                model.orden = nuevo_orden
        await self._session.flush()

    def _to_model(self, imagen: ImagenRepuesto) -> ImagenRepuestoModel:
        return ImagenRepuestoModel(
            id=imagen.id,
            repuesto_id=imagen.repuesto_id,
            url=imagen.url,
            orden=imagen.orden,
            subido_por=imagen.subido_por,
            subido_en=imagen.subido_en,
            updated_at=imagen.updated_at,
        )

    def _to_domain(self, model: ImagenRepuestoModel) -> ImagenRepuesto:
        return ImagenRepuesto(
            id=model.id,
            repuesto_id=model.repuesto_id,
            url=model.url,
            orden=model.orden,
            subido_por=model.subido_por,
            subido_en=model.subido_en,
            updated_at=model.updated_at,
        )

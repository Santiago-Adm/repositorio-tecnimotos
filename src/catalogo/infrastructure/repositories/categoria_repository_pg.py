"""Repositorio PostgreSQL para Categoria — implementa CategoriaRepository Protocol."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.catalogo.domain.models.categoria import Categoria
from src.catalogo.infrastructure.repositories.models.categoria_model import CategoriaModel
from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel


class CategoriaRepositoryPG:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, categoria: Categoria) -> Categoria:
        model = CategoriaModel(id=categoria.id, nombre=categoria.nombre, orden=categoria.orden)
        self._session.add(model)
        await self._session.flush()
        return categoria

    async def obtener_por_id(self, categoria_id: str) -> Optional[Categoria]:
        stmt = select(CategoriaModel).where(CategoriaModel.id == categoria_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def obtener_por_nombre(self, nombre: str) -> Optional[Categoria]:
        stmt = select(CategoriaModel).where(CategoriaModel.nombre == nombre.strip().lower())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def listar(self) -> list[Categoria]:
        stmt = select(CategoriaModel).order_by(CategoriaModel.orden, CategoriaModel.nombre)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def actualizar(self, categoria: Categoria) -> Categoria:
        stmt = select(CategoriaModel).where(CategoriaModel.id == categoria.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Categoria {categoria.id} no encontrada")
        model.nombre = categoria.nombre
        model.orden = categoria.orden
        await self._session.flush()
        return categoria

    async def eliminar(self, categoria_id: str) -> None:
        stmt = select(CategoriaModel).where(CategoriaModel.id == categoria_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    async def contar_repuestos_usando(self, nombre: str) -> int:
        stmt = select(func.count()).select_from(RepuestoModel).where(
            RepuestoModel.categoria == nombre.strip().lower()
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    def _to_domain(self, model: CategoriaModel) -> Categoria:
        return Categoria(
            id=model.id,
            nombre=model.nombre,
            orden=model.orden,
            created_at=model.created_at if isinstance(model.created_at, datetime)
            else datetime.fromisoformat(str(model.created_at)),
            updated_at=model.updated_at if isinstance(model.updated_at, datetime)
            else datetime.fromisoformat(str(model.updated_at)),
        )

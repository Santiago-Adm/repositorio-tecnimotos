"""
Repositorio PostgreSQL para Repuesto — implementa RepuestoRepository Protocol.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.catalogo.domain.models.repuesto import (
    HistorialPrecio,
    Repuesto,
    UniversoRepuesto,
)
from src.catalogo.infrastructure.repositories.models.historial_precio_model import (
    HistorialPrecioModel,
)
from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel


class RepuestoRepositoryPG:
    """Implementación SQLAlchemy del Protocol RepuestoRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, repuesto: Repuesto) -> Repuesto:
        model = self._to_model(repuesto)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def obtener_por_codigo(self, codigo: str) -> Optional[Repuesto]:
        stmt = select(RepuestoModel).where(RepuestoModel.codigo == codigo)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def obtener_por_id(self, repuesto_id: str) -> Optional[Repuesto]:
        stmt = select(RepuestoModel).where(RepuestoModel.id == repuesto_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def buscar(
        self,
        universo: UniversoRepuesto,
        modelo: Optional[str] = None,
        año: Optional[int] = None,
        solo_disponibles: bool = True,
        destacado: Optional[bool] = None,
        random_order: bool = False,
        limit: Optional[int] = None,
        q: Optional[str] = None,
    ) -> list[Repuesto]:
        conditions = [
            RepuestoModel.universo == universo.value,
            RepuestoModel.activo == True,
        ]
        if modelo:
            conditions.append(
                func.lower(RepuestoModel.modelo).contains(modelo.lower())
            )
        if año:
            conditions.append(RepuestoModel.año == año)
        if destacado is not None:
            conditions.append(RepuestoModel.destacado == destacado)
        if q:
            conditions.append(
                or_(RepuestoModel.nombre.ilike(f"%{q}%"), RepuestoModel.codigo.ilike(f"%{q}%"))
            )

        stmt = select(RepuestoModel).where(and_(*conditions))
        if random_order:
            stmt = stmt.order_by(func.random())
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def listar_modelos_distintos(self, universo: UniversoRepuesto) -> list[str]:
        stmt = (
            select(RepuestoModel.modelo)
            .where(RepuestoModel.universo == universo.value, RepuestoModel.activo == True)
            .distinct()
            .order_by(RepuestoModel.modelo)
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def buscar_por_lista_codigos(
        self,
        codigos: list[str],
        universo: Optional[UniversoRepuesto] = None,
    ) -> list[Repuesto]:
        conditions = [RepuestoModel.codigo.in_(codigos)]
        if universo:
            conditions.append(RepuestoModel.universo == universo.value)
        stmt = select(RepuestoModel).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def obtener_historial_precio(self, repuesto_id: str) -> list[HistorialPrecio]:
        stmt = (
            select(HistorialPrecioModel)
            .where(HistorialPrecioModel.repuesto_id == repuesto_id)
            .order_by(HistorialPrecioModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [
            HistorialPrecio(
                id=m.id,
                precio_anterior=m.precio_anterior,
                precio_nuevo=m.precio_nuevo,
                modificado_por=m.modificado_por,
                timestamp=m.created_at if isinstance(m.created_at, datetime)
                else datetime.fromisoformat(str(m.created_at)),
            )
            for m in models
        ]

    async def actualizar(self, repuesto: Repuesto) -> Repuesto:
        stmt = select(RepuestoModel).where(RepuestoModel.id == repuesto.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Repuesto {repuesto.id} no encontrado para actualizar")

        model.nombre = repuesto.nombre
        model.descripcion = repuesto.descripcion
        model.precio_venta = repuesto.precio_venta
        model.activo = repuesto.activo
        model.imagen_url = repuesto.imagen_url
        model.destacado = repuesto.destacado
        model.eliminado_en = repuesto.eliminado_en
        model.updated_at = repuesto.updated_at

        # Persistir historial nuevo
        for entrada in repuesto.historial_precio:
            hist_model = HistorialPrecioModel(
                id=entrada.id,
                repuesto_id=repuesto.id,
                precio_anterior=entrada.precio_anterior,
                precio_nuevo=entrada.precio_nuevo,
                modificado_por=entrada.modificado_por,
            )
            self._session.add(hist_model)

        await self._session.flush()
        return repuesto

    async def contar_disponibles(self, repuesto_id: str) -> int:
        """
        Consulta stock_repuesto.cantidad_disponible para el repuesto.
        Retorna 0 si no existe registro — catalogo no posee tabla stock_repuesto.
        Por diseño: catalogo consulta a stock vía evento, no por join directo.
        En esta implementación de catalogo retornamos el valor que el módulo
        stock mantiene y que catalogo recibe vía evento stock.agotado/disponible
        reflejado en el campo activo del repuesto.
        """
        stmt = select(RepuestoModel).where(RepuestoModel.id == repuesto_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return 0
        # catalogo solo sabe si el repuesto está activo — el stock real vive en stock
        return 1 if model.activo else 0

    def _to_model(self, repuesto: Repuesto) -> RepuestoModel:
        return RepuestoModel(
            id=repuesto.id,
            codigo=repuesto.codigo,
            nombre=repuesto.nombre,
            descripcion=repuesto.descripcion,
            universo=repuesto.universo.value,
            modelo=repuesto.modelo,
            año=repuesto.año,
            categoria=repuesto.categoria,
            precio_venta=repuesto.precio_venta,
            activo=repuesto.activo,
            imagen_url=repuesto.imagen_url,
            destacado=repuesto.destacado,
            eliminado_en=repuesto.eliminado_en,
        )

    def _to_domain(self, model: RepuestoModel) -> Repuesto:
        return Repuesto(
            id=model.id,
            codigo=model.codigo,
            nombre=model.nombre,
            descripcion=model.descripcion or "",
            universo=UniversoRepuesto(model.universo),
            modelo=model.modelo,
            año=model.año,
            categoria=model.categoria,
            precio_venta=Decimal(str(model.precio_venta)),
            activo=model.activo,
            imagen_url=model.imagen_url,
            destacado=model.destacado,
            eliminado_en=model.eliminado_en if isinstance(model.eliminado_en, datetime)
            else (datetime.fromisoformat(str(model.eliminado_en)) if model.eliminado_en else None),
        )

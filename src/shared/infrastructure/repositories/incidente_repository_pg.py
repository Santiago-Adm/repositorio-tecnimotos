"""Repositorio PostgreSQL de incidentes del sistema — ADR-019."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.models.incidente_sistema import (
    EstadoIncidente,
    IncidenteSistema,
    SeveridadIncidente,
)
from src.shared.domain.ports.incidente_repository import IncidenteRepository
from src.shared.infrastructure.models.incidente_sistema_model import IncidenteSistemaModel


def _dt(value) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _to_domain(model: IncidenteSistemaModel) -> IncidenteSistema:
    return IncidenteSistema(
        id=model.id,
        descripcion=model.descripcion,
        severidad=SeveridadIncidente(model.severidad),
        estado=EstadoIncidente(model.estado),
        reportado_por=model.reportado_por,
        resuelto_por=model.resuelto_por,
        created_at=_dt(model.created_at),
        resuelto_at=_dt(model.resuelto_at) if model.resuelto_at else None,
    )


class IncidenteRepositoryPG(IncidenteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def guardar(self, incidente: IncidenteSistema) -> IncidenteSistema:
        self._session.add(IncidenteSistemaModel(
            id=incidente.id,
            descripcion=incidente.descripcion,
            severidad=incidente.severidad.value,
            estado=incidente.estado.value,
            reportado_por=incidente.reportado_por,
            resuelto_por=incidente.resuelto_por,
        ))
        await self._session.flush()
        return incidente

    async def obtener_por_id(self, incidente_id: str) -> Optional[IncidenteSistema]:
        stmt = select(IncidenteSistemaModel).where(IncidenteSistemaModel.id == incidente_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def listar(self, estado: Optional[str] = None) -> list[IncidenteSistema]:
        stmt = select(IncidenteSistemaModel)
        if estado is not None:
            stmt = stmt.where(IncidenteSistemaModel.estado == estado)
        stmt = stmt.order_by(IncidenteSistemaModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [_to_domain(m) for m in result.scalars().all()]

    async def actualizar(self, incidente: IncidenteSistema) -> IncidenteSistema:
        stmt = select(IncidenteSistemaModel).where(IncidenteSistemaModel.id == incidente.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.estado = incidente.estado.value
        model.resuelto_por = incidente.resuelto_por
        model.resuelto_at = incidente.resuelto_at
        await self._session.flush()
        return incidente

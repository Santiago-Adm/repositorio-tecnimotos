"""Puerto abstracto — IncidenteRepository (ADR-019, DIP)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.shared.domain.models.incidente_sistema import IncidenteSistema


class IncidenteRepository(ABC):
    @abstractmethod
    async def guardar(self, incidente: IncidenteSistema) -> IncidenteSistema: ...

    @abstractmethod
    async def obtener_por_id(self, incidente_id: str) -> Optional[IncidenteSistema]: ...

    @abstractmethod
    async def listar(self, estado: Optional[str] = None) -> list[IncidenteSistema]: ...

    @abstractmethod
    async def actualizar(self, incidente: IncidenteSistema) -> IncidenteSistema: ...

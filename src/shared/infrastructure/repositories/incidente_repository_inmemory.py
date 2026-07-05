"""InMemory IncidenteRepository — sustituido por PG en producción."""
from __future__ import annotations

from typing import Optional

from src.shared.domain.models.incidente_sistema import IncidenteSistema
from src.shared.domain.ports.incidente_repository import IncidenteRepository


class InMemoryIncidenteRepository(IncidenteRepository):
    def __init__(self) -> None:
        self._store: dict[str, IncidenteSistema] = {}

    async def guardar(self, incidente: IncidenteSistema) -> IncidenteSistema:
        self._store[incidente.id] = incidente
        return incidente

    async def obtener_por_id(self, incidente_id: str) -> Optional[IncidenteSistema]:
        return self._store.get(incidente_id)

    async def listar(self, estado: Optional[str] = None) -> list[IncidenteSistema]:
        items = list(self._store.values())
        if estado is not None:
            items = [i for i in items if i.estado.value == estado]
        return sorted(items, key=lambda i: i.created_at, reverse=True)

    async def actualizar(self, incidente: IncidenteSistema) -> IncidenteSistema:
        self._store[incidente.id] = incidente
        return incidente

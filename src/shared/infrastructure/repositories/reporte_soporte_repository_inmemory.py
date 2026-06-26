"""InMemory ReporteSoporteRepository — sustituido por PG en producción."""
from __future__ import annotations

from typing import Optional

from src.shared.domain.models.reporte_soporte import EstadoReporteSoporte, ReporteSoporte
from src.shared.domain.ports.reporte_soporte_repository import ReporteSoporteRepository

_ESTADOS_ACTIVOS = {EstadoReporteSoporte.ABIERTO, EstadoReporteSoporte.EN_INVESTIGACION}


class InMemoryReporteSoporteRepository(ReporteSoporteRepository):
    def __init__(self) -> None:
        self._store: dict[str, ReporteSoporte] = {}

    async def guardar(self, reporte: ReporteSoporte) -> None:
        self._store[reporte.id] = reporte

    async def obtener_por_id(self, reporte_id: str) -> Optional[ReporteSoporte]:
        return self._store.get(reporte_id)

    async def listar_activos(self) -> list[ReporteSoporte]:
        return [r for r in self._store.values() if r.estado in _ESTADOS_ACTIVOS]

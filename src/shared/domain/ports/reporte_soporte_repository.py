"""Puerto abstracto — ReporteSoporteRepository (03 §2.3, DIP)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.shared.domain.models.reporte_soporte import ReporteSoporte


class ReporteSoporteRepository(ABC):
    @abstractmethod
    async def guardar(self, reporte: ReporteSoporte) -> None: ...

    @abstractmethod
    async def obtener_por_id(self, reporte_id: str) -> Optional[ReporteSoporte]: ...

    @abstractmethod
    async def listar_activos(self) -> list[ReporteSoporte]: ...

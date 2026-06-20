"""StockTallerPort — implementado por stock, consumido por taller (03 §8.2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DisponibilidadOTResponse:
    repuesto_id: str
    cantidad_disponible: int
    cantidad_apartada: int


class StockTallerPort(Protocol):
    async def verificar_disponibilidad_ot(
        self, repuesto_id: str
    ) -> DisponibilidadOTResponse: ...

    async def consultar_apartado(self, repuesto_id: str) -> int: ...

"""
StockPedidosPort — implementado por stock, consumido por pedidos (03 §8.2, Contrato 3).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DisponibilidadResponse:
    repuesto_id: str
    cantidad_disponible: int


class StockPedidosPort(Protocol):
    """Contrato 3: pedidos consulta y aparta stock (02 §2.2)."""

    async def consultar_disponibilidad(self, repuesto_id: str) -> DisponibilidadResponse: ...
    async def apartar_stock(
        self, repuesto_id: str, cantidad: int, actor_id: str, referencia_id: str
    ) -> bool: ...
    async def liberar_stock(
        self, repuesto_id: str, cantidad: int, actor_id: str, referencia_id: str
    ) -> bool: ...

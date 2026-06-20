"""
TallerPedidosPort — implementado por pedidos, consumido por taller (03 §8.2).
Cuándo: taller necesita verificar que el cobro está confirmado antes de cerrar OT.
"""
from __future__ import annotations

from typing import Protocol


class TallerPedidosPort(Protocol):
    """
    Contrato: taller verifica cobro confirmado en pedidos.
    Cuándo: al cerrar orden_trabajo — taller no puede cerrar sin cobro.
    """

    async def verificar_cobro_confirmado(self, orden_trabajo_id: str) -> bool: ...

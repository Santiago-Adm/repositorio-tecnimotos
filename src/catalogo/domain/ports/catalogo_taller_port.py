"""
CatalogoTallerPort — implementado por catalogo, consumido por taller (03 §8.2).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from src.catalogo.domain.ports.catalogo_pedidos_port import PrecioVigenteResponse


class CatalogoTallerPort(Protocol):
    """
    Puerto síncrono: taller consulta precio a catalogo.
    Cuándo: al armar lista de orden_trabajo · al agregar repuesto en EN_EJECUCION (02 §2.2 Contrato 2).
    """

    async def obtener_precio_para_ot(self, codigo: str) -> PrecioVigenteResponse: ...

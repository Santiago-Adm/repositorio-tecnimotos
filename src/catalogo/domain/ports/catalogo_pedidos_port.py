"""
CatalogoPedidosPort — implementado por catalogo, consumido por pedidos (03 §8.2).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class PrecioVigenteResponse:
    repuesto_id: str
    codigo: str
    precio_venta: Decimal
    nombre: str
    categoria: str
    universo: str
    activo: bool


class CatalogoPedidosPort(Protocol):
    """
    Puerto síncrono: pedidos consulta precio a catalogo.
    Cuándo: al crear pedido · al emitir proforma (02 §2.2 Contrato 1).
    """

    async def obtener_precio_vigente(self, codigo: str) -> PrecioVigenteResponse: ...

    async def verificar_existencia(self, codigo: str) -> bool: ...

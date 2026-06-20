"""
CatalogoPedidosPort — implementado por catalogo, consumido por pedidos (03 §8.2, Contrato 1).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class RepuestoInfo:
    repuesto_id: str
    codigo: str
    precio_venta: Decimal
    nombre: str
    categoria: str
    universo: str
    activo: bool


class CatalogoPedidosPort(Protocol):
    """Contrato 1: pedidos consulta precio a catalogo (02 §2.2)."""

    async def obtener_precio_vigente(self, codigo: str) -> RepuestoInfo: ...
    async def verificar_existencia(self, codigo: str) -> bool: ...

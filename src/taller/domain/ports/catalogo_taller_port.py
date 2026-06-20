"""CatalogoTallerPort — implementado por catalogo, consumido por taller (Contrato 2)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class RepuestoInfoTaller:
    repuesto_id: str
    codigo: str
    precio_venta: Decimal
    nombre: str
    activo: bool


class CatalogoTallerPort(Protocol):
    async def obtener_precio_para_ot(self, codigo: str) -> RepuestoInfoTaller: ...

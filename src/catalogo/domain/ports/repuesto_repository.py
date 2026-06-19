"""
Puerto de repositorio para Repuesto (02 §2, 03 §8).
Protocol mínimo — un Protocol por necesidad real del use case.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional, Protocol

from src.catalogo.domain.models.repuesto import HistorialPrecio, Repuesto, UniversoRepuesto


class RepuestoRepository(Protocol):
    async def guardar(self, repuesto: Repuesto) -> Repuesto: ...

    async def obtener_por_codigo(self, codigo: str) -> Optional[Repuesto]: ...

    async def obtener_por_id(self, repuesto_id: str) -> Optional[Repuesto]: ...

    async def buscar(
        self,
        universo: UniversoRepuesto,
        modelo: Optional[str] = None,
        año: Optional[int] = None,
        solo_disponibles: bool = True,
    ) -> list[Repuesto]: ...

    async def buscar_por_lista_codigos(
        self,
        codigos: list[str],
        universo: Optional[UniversoRepuesto] = None,
    ) -> list[Repuesto]: ...

    async def obtener_historial_precio(self, repuesto_id: str) -> list[HistorialPrecio]: ...

    async def actualizar(self, repuesto: Repuesto) -> Repuesto: ...

    async def contar_disponibles(self, repuesto_id: str) -> int: ...

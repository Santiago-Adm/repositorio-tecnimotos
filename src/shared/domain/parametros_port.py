"""
ParametrosSistemaPort — servicio transversal (03 §8.2, §8.4).
Implementado por shared, consumido por todos los módulos.
Caché Redis DB-1 con TTL configurable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ParametroResponse:
    clave: str
    valor: Any
    desde_cache: bool = False


class ParametroNoEncontradoError(Exception):
    pass


class ParametrosSistemaPort(Protocol):
    async def obtener_parametro(self, clave: str) -> ParametroResponse: ...

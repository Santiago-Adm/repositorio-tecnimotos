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
    modificable_por: str = "ADMINISTRADOR"


class ParametroNoEncontradoError(Exception):
    pass


class ParametrosSistemaPort(Protocol):
    """
    ADR-015: listar()/establecer() formalizados en el Protocol para que un
    backend PG lo pueda implementar sin que las rutas se apoyen en atributos
    privados de una implementación concreta (bug encontrado en la sesión
    de ADR-015 — api/routes/admin.py accedía a `svc._parametros` directo).
    """

    async def obtener_parametro(self, clave: str) -> ParametroResponse: ...

    async def listar(self) -> list[ParametroResponse]: ...

    async def establecer(self, clave: str, valor: Any) -> ParametroResponse: ...

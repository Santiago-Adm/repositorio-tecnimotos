"""
Implementaciones de ParametrosSistemaPort (03 §8.2, §8.4).
InMemoryParametros (tests) · ParametrosServiceImpl (producción con Redis DB-1).
"""
from __future__ import annotations

from typing import Any

from src.shared.domain.parametros_port import (
    ParametroNoEncontradoError,
    ParametroResponse,
)

_DEFAULTS: dict[str, Any] = {
    "max_consultas_precio_sesion": 3,
    "reintentos_notificacion": 3,
    "intervalo_reintento_notif_min": 10,
    "ttl_cache_parametros_segundos": 300,
    "umbral_margen_alerta": 0.10,
}


class InMemoryParametrosService:
    """
    Fake de ParametrosSistemaPort para tests de contrato LSP (04 §6.2).
    Cargado con valores por defecto del sistema.
    """

    def __init__(self, parametros: dict[str, Any] | None = None) -> None:
        self._parametros: dict[str, Any] = {**_DEFAULTS, **(parametros or {})}

    def establecer(self, clave: str, valor: Any) -> None:
        self._parametros[clave] = valor

    async def obtener_parametro(self, clave: str) -> ParametroResponse:
        if clave not in self._parametros:
            raise ParametroNoEncontradoError(f"Parámetro {clave!r} no encontrado")
        return ParametroResponse(
            clave=clave,
            valor=self._parametros[clave],
            desde_cache=False,
        )


class ParametrosServiceImpl:
    """
    Implementación real de ParametrosSistemaPort.
    En producción: PostgreSQL + caché Redis DB-1 con TTL configurable.
    En tests de contrato LSP: usa InMemoryParametros como backend.
    """

    def __init__(self, backend: InMemoryParametrosService | None = None) -> None:
        self._backend = backend or InMemoryParametrosService()

    async def obtener_parametro(self, clave: str) -> ParametroResponse:
        resultado = await self._backend.obtener_parametro(clave)
        return ParametroResponse(
            clave=resultado.clave,
            valor=resultado.valor,
            desde_cache=True,
        )

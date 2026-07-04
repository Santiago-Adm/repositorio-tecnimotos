"""
Implementaciones de ParametrosSistemaPort (03 §8.2, §8.4, ADR-015).
InMemoryParametrosService (tests / fallback sin BD) · ParametrosRepositoryPG
(producción, tabla `parametros_sistema` real).
"""
from __future__ import annotations

from typing import Any

from src.shared.domain.parametros_port import (
    ParametroNoEncontradoError,
    ParametroResponse,
)

# (valor, modificable_por) — ADR-015: los 5 parámetros originales (antes solo
# en memoria) + los 2 nuevos de "OT activa" (glosario ADR-015). modulo se usa
# solo en el backend PG (columna real); aquí no aporta comportamiento.
_DEFAULTS: dict[str, tuple[Any, str]] = {
    "max_consultas_precio_sesion": (3, "ADMINISTRADOR"),
    "reintentos_notificacion": (3, "ADMINISTRADOR"),
    "intervalo_reintento_notif_min": (10, "ADMINISTRADOR"),
    "ttl_cache_parametros_segundos": (300, "SUPERADMIN"),
    "umbral_margen_alerta": (0.10, "ADMINISTRADOR"),
    "taller.ot_activa.estados": ("ABIERTA,LISTA_REPUESTOS,EN_EJECUCION,REVISION_FINAL", "ADMINISTRADOR"),
    "taller.ot_activa.dias_maximo": (7, "ADMINISTRADOR"),
}


class InMemoryParametrosService:
    """
    Fake de ParametrosSistemaPort para tests de contrato LSP (04 §6.2) y
    fallback sin BD (mismo patrón que los demás módulos — nunca fallar si
    Postgres no está disponible, ver `_get_parametros` en api/routes/admin.py).
    """

    def __init__(self, parametros: dict[str, Any] | None = None) -> None:
        self._parametros: dict[str, tuple[Any, str]] = dict(_DEFAULTS)
        for clave, valor in (parametros or {}).items():
            modificable_por = self._parametros.get(clave, (None, "ADMINISTRADOR"))[1]
            self._parametros[clave] = (valor, modificable_por)

    async def establecer(self, clave: str, valor: Any) -> ParametroResponse:
        modificable_por = self._parametros.get(clave, (None, "ADMINISTRADOR"))[1]
        self._parametros[clave] = (valor, modificable_por)
        return ParametroResponse(clave=clave, valor=valor, modificable_por=modificable_por)

    async def obtener_parametro(self, clave: str) -> ParametroResponse:
        if clave not in self._parametros:
            raise ParametroNoEncontradoError(f"Parámetro {clave!r} no encontrado")
        valor, modificable_por = self._parametros[clave]
        return ParametroResponse(clave=clave, valor=valor, desde_cache=False, modificable_por=modificable_por)

    async def listar(self) -> list[ParametroResponse]:
        return [
            ParametroResponse(clave=clave, valor=valor, modificable_por=modificable_por)
            for clave, (valor, modificable_por) in self._parametros.items()
        ]

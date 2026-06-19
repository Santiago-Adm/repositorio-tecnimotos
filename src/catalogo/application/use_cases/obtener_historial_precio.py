"""
Caso de uso: obtener historial de precio de un repuesto (EP-CAT-06).
"""
from __future__ import annotations

from dataclasses import dataclass

from src.catalogo.domain.models.repuesto import HistorialPrecio, RepuestoNoEncontradoError
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository


@dataclass
class ObtenerHistorialPrecioQuery:
    codigo: str


class ObtenerHistorialPrecioUseCase:
    """
    EP-CAT-06: GET /v1/repuestos/{codigo}/historial-precio
    Solo ADMINISTRADOR y SUPERADMIN (02 §4.1).
    """

    def __init__(self, repo: RepuestoRepository) -> None:
        self._repo = repo

    async def execute(self, query: ObtenerHistorialPrecioQuery) -> list[HistorialPrecio]:
        repuesto = await self._repo.obtener_por_codigo(query.codigo)
        if repuesto is None:
            raise RepuestoNoEncontradoError(
                f"Repuesto con código {query.codigo} no encontrado"
            )
        return await self._repo.obtener_historial_precio(repuesto.id)

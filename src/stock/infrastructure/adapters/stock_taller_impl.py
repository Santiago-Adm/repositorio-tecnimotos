"""
Implementación de StockTallerPort (03 §8.2).
Consumido por taller para verificar disponibilidad de repuestos en OT.
"""
from __future__ import annotations

from src.stock.domain.models.stock import StockNoEncontradoError
from src.stock.domain.ports.stock_repository import StockRepository
from src.taller.domain.ports.stock_taller_port import DisponibilidadOTResponse


class StockTallerServiceImpl:
    """
    Implementación real de StockTallerPort usando StockRepository.
    """

    def __init__(self, repo: StockRepository) -> None:
        self._repo = repo

    async def verificar_disponibilidad_ot(self, repuesto_id: str) -> DisponibilidadOTResponse:
        stock = await self._repo.obtener_por_repuesto_id(repuesto_id)
        if stock is None:
            raise StockNoEncontradoError(
                f"Stock no encontrado para repuesto {repuesto_id}"
            )
        return DisponibilidadOTResponse(
            repuesto_id=stock.repuesto_id,
            cantidad_disponible=stock.cantidad_disponible,
            cantidad_apartada=stock.cantidad_apartada,
        )

    async def consultar_apartado(self, repuesto_id: str) -> int:
        stock = await self._repo.obtener_por_repuesto_id(repuesto_id)
        if stock is None:
            return 0
        return stock.cantidad_apartada

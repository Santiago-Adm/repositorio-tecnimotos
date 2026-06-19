"""
Implementación de StockPedidosPort (03 §8.2, Contrato 3).
Consumido por pedidos vía inyección de dependencias.
"""
from __future__ import annotations

from src.stock.domain.models.stock import StockInsuficienteError, StockNoEncontradoError
from src.stock.domain.ports.stock_pedidos_port import DisponibilidadResponse
from src.stock.domain.ports.stock_repository import StockRepository


class StockServiceImpl:
    """
    Implementa StockPedidosPort.
    Expuesta a pedidos sin import directo entre módulos.
    """

    def __init__(self, repo: StockRepository) -> None:
        self._repo = repo

    async def consultar_disponibilidad(self, repuesto_id: str) -> DisponibilidadResponse:
        stock = await self._repo.obtener_por_repuesto_id(repuesto_id)
        if stock is None:
            raise StockNoEncontradoError(
                f"Stock no encontrado para repuesto {repuesto_id}"
            )
        return DisponibilidadResponse(
            repuesto_id=stock.repuesto_id,
            cantidad_disponible=stock.cantidad_disponible,
        )

    async def apartar_stock(
        self,
        repuesto_id: str,
        cantidad: int,
        actor_id: str,
        referencia_id: str,
    ) -> bool:
        stock = await self._repo.obtener_por_repuesto_id(repuesto_id)
        if stock is None:
            raise StockNoEncontradoError(
                f"Stock no encontrado para repuesto {repuesto_id}"
            )
        try:
            stock.apartar(cantidad, actor_id, referencia_id)
            await self._repo.actualizar(stock)
            return True
        except StockInsuficienteError:
            return False

    async def liberar_stock(
        self,
        repuesto_id: str,
        cantidad: int,
        actor_id: str,
        referencia_id: str,
    ) -> bool:
        stock = await self._repo.obtener_por_repuesto_id(repuesto_id)
        if stock is None:
            return False
        try:
            stock.liberar_apartado(cantidad, actor_id, referencia_id)
            await self._repo.actualizar(stock)
            return True
        except Exception:
            return False


class InMemoryStockService:
    """
    Implementación en memoria para tests de contrato LSP (04 §6.2).
    Implementa StockPedidosPort.
    """

    def __init__(self) -> None:
        self._stocks: dict[str, int] = {}

    def agregar_stock(self, repuesto_id: str, cantidad_disponible: int) -> None:
        self._stocks[repuesto_id] = cantidad_disponible

    async def consultar_disponibilidad(self, repuesto_id: str) -> DisponibilidadResponse:
        if repuesto_id not in self._stocks:
            raise StockNoEncontradoError(
                f"Stock no encontrado para repuesto {repuesto_id}"
            )
        return DisponibilidadResponse(
            repuesto_id=repuesto_id,
            cantidad_disponible=self._stocks[repuesto_id],
        )

    async def apartar_stock(
        self,
        repuesto_id: str,
        cantidad: int,
        actor_id: str,
        referencia_id: str,
    ) -> bool:
        disponible = self._stocks.get(repuesto_id, 0)
        if disponible < cantidad:
            return False
        self._stocks[repuesto_id] = disponible - cantidad
        return True

    async def liberar_stock(
        self,
        repuesto_id: str,
        cantidad: int,
        actor_id: str,
        referencia_id: str,
    ) -> bool:
        self._stocks[repuesto_id] = self._stocks.get(repuesto_id, 0) + cantidad
        return True

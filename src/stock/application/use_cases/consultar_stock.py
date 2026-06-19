"""
EP-STK-01: Consultar stock por código de repuesto.
EP-STK-02: Listar todo el stock.
EP-STK-03: Listar movimientos de un repuesto.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.stock.domain.models.stock import MovimientoStock, StockNoEncontradoError, StockRepuesto
from src.stock.domain.ports.stock_repository import StockRepository


@dataclass
class ConsultarStockQuery:
    codigo: str


@dataclass
class ListarMovimientosQuery:
    codigo: str


class ConsultarStockUseCase:
    """EP-STK-01: GET /v1/stock/{codigo}"""

    def __init__(self, repo: StockRepository) -> None:
        self._repo = repo

    async def execute(self, query: ConsultarStockQuery) -> StockRepuesto:
        stock = await self._repo.obtener_por_codigo(query.codigo)
        if stock is None:
            raise StockNoEncontradoError(
                f"Stock para código {query.codigo!r} no encontrado"
            )
        return stock


class ListarStockUseCase:
    """EP-STK-02: GET /v1/stock"""

    def __init__(self, repo: StockRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[StockRepuesto]:
        return await self._repo.listar_todos()


class ListarMovimientosUseCase:
    """EP-STK-03: GET /v1/stock/{codigo}/movimientos"""

    def __init__(self, repo: StockRepository) -> None:
        self._repo = repo

    async def execute(self, query: ListarMovimientosQuery) -> list[MovimientoStock]:
        stock = await self._repo.obtener_por_codigo(query.codigo)
        if stock is None:
            raise StockNoEncontradoError(
                f"Stock para código {query.codigo!r} no encontrado"
            )
        return await self._repo.obtener_movimientos(stock.repuesto_id)

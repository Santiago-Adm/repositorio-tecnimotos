"""
InMemoryStockRepository — Fake para tests (04 §4.2).
"""
from __future__ import annotations

from typing import Optional

from src.stock.domain.models.stock import MovimientoStock, Reabastecimiento, StockRepuesto


class InMemoryStockRepository:
    """Implementación en memoria del Protocol StockRepository."""

    def __init__(self) -> None:
        self._stocks: dict[str, StockRepuesto] = {}
        self._movimientos: dict[str, list[MovimientoStock]] = {}
        self._reabastecimientos: dict[str, Reabastecimiento] = {}

    async def guardar(self, stock: StockRepuesto) -> StockRepuesto:
        self._stocks[stock.repuesto_id] = stock
        if stock.repuesto_id not in self._movimientos:
            self._movimientos[stock.repuesto_id] = []
        return stock

    async def obtener_por_repuesto_id(self, repuesto_id: str) -> Optional[StockRepuesto]:
        return self._stocks.get(repuesto_id)

    async def obtener_por_codigo(self, codigo: str) -> Optional[StockRepuesto]:
        return next(
            (s for s in self._stocks.values() if s.codigo == codigo), None
        )

    async def listar_todos(self) -> list[StockRepuesto]:
        return list(self._stocks.values())

    async def actualizar(self, stock: StockRepuesto) -> StockRepuesto:
        if stock.repuesto_id not in self._stocks:
            raise ValueError(f"StockRepuesto {stock.repuesto_id} no encontrado")
        self._stocks[stock.repuesto_id] = stock
        movs = self._movimientos.setdefault(stock.repuesto_id, [])
        for mov in stock.movimientos:
            if not any(m.id == mov.id for m in movs):
                movs.append(mov)
        return stock

    async def obtener_movimientos(self, repuesto_id: str) -> list[MovimientoStock]:
        return list(self._movimientos.get(repuesto_id, []))

    async def guardar_reabastecimiento(self, reab: Reabastecimiento) -> Reabastecimiento:
        self._reabastecimientos[reab.id] = reab
        return reab

    async def obtener_reabastecimiento(self, reab_id: str) -> Optional[Reabastecimiento]:
        return self._reabastecimientos.get(reab_id)

    async def actualizar_reabastecimiento(self, reab: Reabastecimiento) -> Reabastecimiento:
        if reab.id not in self._reabastecimientos:
            raise ValueError(f"Reabastecimiento {reab.id} no encontrado")
        self._reabastecimientos[reab.id] = reab
        return reab

    def limpiar(self) -> None:
        self._stocks.clear()
        self._movimientos.clear()
        self._reabastecimientos.clear()

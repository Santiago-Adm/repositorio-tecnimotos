"""
Adaptadores para los puertos externos del módulo pedidos.
InMemoryCatalogoAdapter y InMemoryStockAdapter — para tests.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.pedidos.domain.models.pedido import DomainError
from src.pedidos.domain.ports.catalogo_pedidos_port import RepuestoInfo
from src.pedidos.domain.ports.stock_pedidos_port import DisponibilidadResponse


class InMemoryCatalogoAdapter:
    """Fake CatalogoPedidosPort para tests."""

    def __init__(self) -> None:
        self._repuestos: dict[str, RepuestoInfo] = {}

    def agregar_repuesto(self, info: RepuestoInfo) -> None:
        self._repuestos[info.codigo] = info

    async def obtener_precio_vigente(self, codigo: str) -> RepuestoInfo:
        info = self._repuestos.get(codigo)
        if info is None:
            raise DomainError(f"Repuesto {codigo!r} no encontrado en catálogo")
        return info

    async def verificar_existencia(self, codigo: str) -> bool:
        return codigo in self._repuestos


class InMemoryStockAdapter:
    """Fake StockPedidosPort para tests."""

    def __init__(self) -> None:
        self._disponible: dict[str, int] = {}
        self._apartado: dict[str, int] = {}

    def establecer_stock(self, repuesto_id: str, cantidad: int) -> None:
        self._disponible[repuesto_id] = cantidad

    async def consultar_disponibilidad(self, repuesto_id: str) -> DisponibilidadResponse:
        return DisponibilidadResponse(
            repuesto_id=repuesto_id,
            cantidad_disponible=self._disponible.get(repuesto_id, 0),
        )

    async def apartar_stock(
        self, repuesto_id: str, cantidad: int, actor_id: str, referencia_id: str
    ) -> bool:
        disponible = self._disponible.get(repuesto_id, 0)
        if disponible < cantidad:
            return False
        self._disponible[repuesto_id] = disponible - cantidad
        self._apartado[repuesto_id] = self._apartado.get(repuesto_id, 0) + cantidad
        return True

    async def liberar_stock(
        self, repuesto_id: str, cantidad: int, actor_id: str, referencia_id: str
    ) -> bool:
        apartado = self._apartado.get(repuesto_id, 0)
        if apartado < cantidad:
            return False
        self._apartado[repuesto_id] = apartado - cantidad
        self._disponible[repuesto_id] = self._disponible.get(repuesto_id, 0) + cantidad
        return True

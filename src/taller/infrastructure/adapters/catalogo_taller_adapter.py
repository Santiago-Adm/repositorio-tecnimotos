"""Adaptadores fake para tests del módulo taller."""
from __future__ import annotations

from decimal import Decimal

from src.taller.domain.models.orden_trabajo import DomainError
from src.taller.domain.ports.catalogo_taller_port import RepuestoInfoTaller
from src.taller.domain.ports.stock_taller_port import DisponibilidadOTResponse


class InMemoryCatalogoTallerAdapter:
    """Fake CatalogoTallerPort para tests."""

    def __init__(self) -> None:
        self._repuestos: dict[str, RepuestoInfoTaller] = {}

    def agregar_repuesto(self, info: RepuestoInfoTaller) -> None:
        self._repuestos[info.codigo] = info

    async def obtener_precio_para_ot(self, codigo: str) -> RepuestoInfoTaller:
        info = self._repuestos.get(codigo)
        if info is None:
            raise DomainError(f"Repuesto {codigo!r} no encontrado en catálogo")
        return info


class InMemoryStockTallerAdapter:
    """Fake StockTallerPort para tests."""

    def __init__(self) -> None:
        self._disponible: dict[str, int] = {}
        self._apartado: dict[str, int] = {}

    def establecer_stock(self, repuesto_id: str, disponible: int, apartado: int = 0) -> None:
        self._disponible[repuesto_id] = disponible
        self._apartado[repuesto_id] = apartado

    async def verificar_disponibilidad_ot(self, repuesto_id: str) -> DisponibilidadOTResponse:
        return DisponibilidadOTResponse(
            repuesto_id=repuesto_id,
            cantidad_disponible=self._disponible.get(repuesto_id, 0),
            cantidad_apartada=self._apartado.get(repuesto_id, 0),
        )

    async def consultar_apartado(self, repuesto_id: str) -> int:
        return self._apartado.get(repuesto_id, 0)

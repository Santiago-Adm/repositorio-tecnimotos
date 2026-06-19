"""
Descuento atómico de stock al cierre de orden_trabajo (02 §3.2 regla crítica).
Si falla cualquier repuesto → rollback completo → ninguno se descuenta.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.shared.events.envelope import EventEnvelope
from src.stock.domain.models.stock import (
    MovimientoStock,
    StockNoEncontradoError,
    TipoMovimiento,
)
from src.stock.domain.ports.event_publisher import EventPublisher
from src.stock.domain.ports.stock_repository import StockRepository
from src.stock.domain.services.stock_service import StockService


@dataclass
class ItemDescuento:
    repuesto_id: str
    cantidad: int


@dataclass
class DescontarStockAtomicoCommand:
    orden_trabajo_id: str
    repuestos: list[ItemDescuento]
    actor_id: str


@dataclass
class DescontarStockAtomicoResult:
    orden_trabajo_id: str
    movimientos: list[MovimientoStock] = field(default_factory=list)


class DescontarStockAtomicoUseCase:
    """
    Descuento transaccional atómico: todos o ninguno.
    Consumido por taller al cerrar orden_trabajo (02 §3.2).
    """

    def __init__(self, repo: StockRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(
        self, command: DescontarStockAtomicoCommand
    ) -> DescontarStockAtomicoResult:
        # Fase 1: cargar todos los stocks necesarios
        stocks = []
        descuentos: dict[str, int] = {}
        for item in command.repuestos:
            stock = await self._repo.obtener_por_repuesto_id(item.repuesto_id)
            if stock is None:
                raise StockNoEncontradoError(
                    f"Stock no encontrado para repuesto {item.repuesto_id}"
                )
            stocks.append(stock)
            descuentos[item.repuesto_id] = item.cantidad

        # Fase 2: validar TODOS antes de descontar alguno (regla atómica)
        StockService.validar_descuento_atomico(stocks, descuentos)

        # Fase 3: ejecutar descuentos — no puede fallar tras la validación
        movimientos: list[MovimientoStock] = []
        repuestos_descontados = []

        for stock in stocks:
            cantidad = descuentos[stock.repuesto_id]
            if cantidad > 0:
                mov = stock.descontar_venta(
                    cantidad=cantidad,
                    actor_id=command.actor_id,
                    tipo=TipoMovimiento.SALIDA_TALLER,
                    referencia_id=command.orden_trabajo_id,
                )
                movimientos.append(mov)
                await self._repo.actualizar(stock)
                repuestos_descontados.append({
                    "repuesto_id": stock.repuesto_id,
                    "cantidad": cantidad,
                })

                if stock.esta_agotado():
                    await self._pub.publish(EventEnvelope(
                        tipo="stock.agotado", modulo_origen="stock",
                        payload={"repuesto_id": stock.repuesto_id, "codigo": stock.codigo},
                    ))
                elif stock.esta_bajo_umbral():
                    await self._pub.publish(EventEnvelope(
                        tipo="stock.bajo_umbral", modulo_origen="stock",
                        payload={
                            "repuesto_id": stock.repuesto_id,
                            "codigo": stock.codigo,
                            "cantidad_actual": stock.cantidad_disponible,
                            "umbral_minimo": stock.umbral_minimo,
                        },
                    ))

        await self._pub.publish(EventEnvelope(
            tipo="stock.consumo_registrado", modulo_origen="stock",
            payload={
                "orden_trabajo_id": command.orden_trabajo_id,
                "repuestos_descontados": repuestos_descontados,
            },
        ))

        return DescontarStockAtomicoResult(
            orden_trabajo_id=command.orden_trabajo_id,
            movimientos=movimientos,
        )

"""
EP-STK-06: Crear reabastecimiento.
EP-STK-07: Actualizar estado de reabastecimiento.
EP-STK-08: Obtener reabastecimiento.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from src.shared.events.envelope import EventEnvelope
from src.stock.domain.models.stock import (
    EstadoReabastecimiento,
    Reabastecimiento,
    ReabastecimientoItem,
    ReabastecimientoNoEncontradoError,
    StockNoEncontradoError,
)
from src.stock.domain.ports.event_publisher import EventPublisher
from src.stock.domain.ports.stock_repository import StockRepository
from src.stock.domain.services.stock_service import StockService


@dataclass
class ItemReabastecimientoInput:
    repuesto_id: str
    codigo: str
    cantidad_solicitada: int
    precio_costo_unitario: Decimal


@dataclass
class CrearReabastecimientoCommand:
    proveedor: str
    solicitado_por: str
    items: list[ItemReabastecimientoInput] = field(default_factory=list)
    notas: str = ""


@dataclass
class ActualizarEstadoReabastecimientoCommand:
    reabastecimiento_id: str
    nuevo_estado: EstadoReabastecimiento
    actor_id: str


class CrearReabastecimientoUseCase:
    """EP-STK-06: POST /v1/reabastecimientos"""

    def __init__(self, repo: StockRepository) -> None:
        self._repo = repo

    async def execute(self, command: CrearReabastecimientoCommand) -> Reabastecimiento:
        reab = Reabastecimiento(
            proveedor=command.proveedor,
            solicitado_por=command.solicitado_por,
            notas=command.notas,
        )
        for item_input in command.items:
            reab.agregar_item(
                ReabastecimientoItem(
                    repuesto_id=item_input.repuesto_id,
                    codigo=item_input.codigo,
                    cantidad_solicitada=item_input.cantidad_solicitada,
                    precio_costo_unitario=item_input.precio_costo_unitario,
                )
            )
        return await self._repo.guardar_reabastecimiento(reab)


class ActualizarEstadoReabastecimientoUseCase:
    """EP-STK-07: PATCH /v1/reabastecimientos/{id}/estado"""

    def __init__(self, repo: StockRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(
        self, command: ActualizarEstadoReabastecimientoCommand
    ) -> Reabastecimiento:
        reab = await self._repo.obtener_reabastecimiento(command.reabastecimiento_id)
        if reab is None:
            raise ReabastecimientoNoEncontradoError(
                f"Reabastecimiento {command.reabastecimiento_id} no encontrado"
            )

        reab.avanzar_estado(command.nuevo_estado)

        if reab.esta_recibido():
            await self._procesar_recepcion(reab, command.actor_id)

        await self._repo.actualizar_reabastecimiento(reab)
        return reab

    async def _procesar_recepcion(
        self, reab: Reabastecimiento, actor_id: str
    ) -> None:
        repuestos_recibidos = []
        for item in reab.items:
            stock = await self._repo.obtener_por_repuesto_id(item.repuesto_id)
            if stock is None:
                raise StockNoEncontradoError(
                    f"Stock no encontrado para repuesto {item.repuesto_id}"
                )

            stock_antes_disponible = stock.cantidad_disponible
            stock.registrar_entrada(
                cantidad=item.cantidad_solicitada,
                actor_id=actor_id,
                referencia_id=reab.id,
            )
            await self._repo.actualizar(stock)

            if stock_antes_disponible == 0 and stock.cantidad_disponible > 0:
                await self._pub.publish(EventEnvelope(
                    tipo="stock.disponible", modulo_origen="stock",
                    payload={
                        "repuesto_id": stock.repuesto_id,
                        "codigo": stock.codigo,
                        "cantidad_nueva": stock.cantidad_disponible,
                    },
                ))

            repuestos_recibidos.append({
                "repuesto_id": item.repuesto_id,
                "codigo": item.codigo,
                "cantidad": item.cantidad_solicitada,
                "precio_costo_unitario": str(item.precio_costo_unitario),
            })

            alerta = StockService.calcular_alerta_margen(
                reab.precio_costo_anterior,
                item.precio_costo_unitario,
            )
            if alerta:
                await self._pub.publish(EventEnvelope(
                    tipo="margen.alerta", modulo_origen="stock",
                    payload={
                        "repuesto_id": item.repuesto_id,
                        "codigo": item.codigo,
                        "precio_costo_nuevo": str(item.precio_costo_unitario),
                    },
                ))

        await self._pub.publish(EventEnvelope(
            tipo="reabastecimiento.recibido", modulo_origen="stock",
            payload={
                "reabastecimiento_id": reab.id,
                "repuestos_recibidos": repuestos_recibidos,
            },
        ))


class ObtenerReabastecimientoUseCase:
    """EP-STK-08: GET /v1/reabastecimientos/{id}"""

    def __init__(self, repo: StockRepository) -> None:
        self._repo = repo

    async def execute(self, reabastecimiento_id: str) -> Reabastecimiento:
        reab = await self._repo.obtener_reabastecimiento(reabastecimiento_id)
        if reab is None:
            raise ReabastecimientoNoEncontradoError(
                f"Reabastecimiento {reabastecimiento_id} no encontrado"
            )
        return reab

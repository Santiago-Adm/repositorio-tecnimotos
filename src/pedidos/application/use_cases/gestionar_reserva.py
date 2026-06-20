"""
EP-PED-06: Crear reserva.
EP-PED-07: Liberar reserva.
EP-PED-12: Notificar repuesto disponible.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.shared.events.envelope import EventEnvelope
from src.pedidos.domain.models.pedido import (
    DomainError,
    Reserva,
    ReservaNoEncontradaError,
    SegmentoCliente,
)
from src.pedidos.domain.ports.event_publisher import EventPublisher
from src.pedidos.domain.ports.pedido_repository import PedidoRepository
from src.pedidos.domain.ports.stock_pedidos_port import StockPedidosPort
from src.pedidos.domain.services.pedido_service import PedidoService


@dataclass
class CrearReservaCommand:
    cliente_id: str
    repuesto_id: str
    cantidad: int
    segmento: SegmentoCliente
    actor_id: str
    pedido_id: Optional[str] = None


@dataclass
class LiberarReservaCommand:
    reserva_id: str
    actor_id: str
    motivo: str = "LIBERADA_MANUAL"


class CrearReservaUseCase:
    """EP-PED-06: POST /v1/reservas"""

    def __init__(
        self,
        repo: PedidoRepository,
        stock: StockPedidosPort,
        event_publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._stock = stock
        self._pub = event_publisher

    async def execute(self, command: CrearReservaCommand) -> Reserva:
        disp = await self._stock.consultar_disponibilidad(command.repuesto_id)
        if disp.cantidad_disponible < command.cantidad:
            raise DomainError(
                f"Stock insuficiente: disponible={disp.cantidad_disponible}, "
                f"requerido={command.cantidad}"
            )

        reserva = Reserva(
            cliente_id=command.cliente_id,
            repuesto_id=command.repuesto_id,
            cantidad=command.cantidad,
            segmento=command.segmento,
            pedido_id=command.pedido_id,
        )
        await self._repo.guardar_reserva(reserva)

        ok = await self._stock.apartar_stock(
            repuesto_id=command.repuesto_id,
            cantidad=command.cantidad,
            actor_id=command.actor_id,
            referencia_id=reserva.id,
        )
        if not ok:
            raise DomainError("No se pudo apartar el stock")

        await self._pub.publish(EventEnvelope(
            tipo="reserva.creada",
            modulo_origen="pedidos",
            payload={
                "reserva_id": reserva.id,
                "repuesto_id": command.repuesto_id,
                "cantidad": command.cantidad,
                "cliente_id": command.cliente_id,
                "segmento": command.segmento.value,
                "expira_en": reserva.expira_en.isoformat(),
            },
        ))
        return reserva


class LiberarReservaUseCase:
    """EP-PED-07: POST /v1/reservas/{reserva_id}/liberar"""

    def __init__(
        self,
        repo: PedidoRepository,
        stock: StockPedidosPort,
        event_publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._stock = stock
        self._pub = event_publisher

    async def execute(self, command: LiberarReservaCommand) -> Reserva:
        reserva = await self._repo.obtener_reserva(command.reserva_id)
        if reserva is None:
            raise ReservaNoEncontradaError(
                f"Reserva {command.reserva_id} no encontrada"
            )

        libera_stock = PedidoService.reserva_libera_stock(reserva)
        reserva.liberar(command.motivo)
        await self._repo.actualizar_reserva(reserva)

        if libera_stock:
            await self._stock.liberar_stock(
                repuesto_id=reserva.repuesto_id,
                cantidad=reserva.cantidad,
                actor_id=command.actor_id,
                referencia_id=reserva.id,
            )

        tipo_evento = (
            "reserva.prioridad_taller"
            if command.motivo == "PRIORIDAD_TALLER"
            else "reserva.liberada"
        )
        await self._pub.publish(EventEnvelope(
            tipo=tipo_evento,
            modulo_origen="pedidos",
            payload={
                "reserva_id": reserva.id,
                "repuesto_id": reserva.repuesto_id,
                "cantidad": reserva.cantidad,
                "motivo": command.motivo,
            },
        ))
        return reserva

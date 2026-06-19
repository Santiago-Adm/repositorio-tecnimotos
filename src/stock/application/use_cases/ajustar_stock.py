"""
EP-STK-04: Ajuste manual de stock.
EP-STK-05: Actualizar umbral mínimo.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.events.envelope import EventEnvelope
from src.stock.domain.models.stock import (
    StockNoEncontradoError,
    StockRepuesto,
    TipoMovimiento,
)
from src.stock.domain.ports.event_publisher import EventPublisher
from src.stock.domain.ports.stock_repository import StockRepository
from src.stock.domain.services.stock_service import StockService


@dataclass
class AjustarStockCommand:
    codigo: str
    cantidad: int
    actor_id: str
    motivo: str = ""


@dataclass
class ActualizarUmbralCommand:
    codigo: str
    umbral_minimo: int
    actor_id: str


@dataclass
class AjusteResult:
    stock: StockRepuesto
    eventos_publicados: list[str]


class AjustarStockUseCase:
    """EP-STK-04: POST /v1/stock/{codigo}/ajuste — registra AJUSTE_MANUAL."""

    def __init__(self, repo: StockRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: AjustarStockCommand) -> AjusteResult:
        stock = await self._repo.obtener_por_codigo(command.codigo)
        if stock is None:
            raise StockNoEncontradoError(
                f"Stock para código {command.codigo!r} no encontrado"
            )

        stock_antes = StockRepuesto(
            repuesto_id=stock.repuesto_id,
            codigo=stock.codigo,
            cantidad_disponible=stock.cantidad_disponible,
            cantidad_apartada=stock.cantidad_apartada,
            umbral_minimo=stock.umbral_minimo,
        )

        if command.cantidad > 0:
            stock.registrar_entrada(
                cantidad=command.cantidad,
                actor_id=command.actor_id,
                referencia_id=command.motivo,
            )
            stock.movimientos[-1].tipo_movimiento = TipoMovimiento.AJUSTE_MANUAL
        elif command.cantidad < 0:
            stock.descontar_venta(
                cantidad=abs(command.cantidad),
                actor_id=command.actor_id,
                tipo=TipoMovimiento.AJUSTE_MANUAL,
                referencia_id=command.motivo,
            )

        eventos = StockService.detectar_eventos_necesarios(stock_antes, stock)
        await self._repo.actualizar(stock)

        for tipo_evento in eventos:
            payload: dict = {"repuesto_id": stock.repuesto_id, "codigo": stock.codigo}
            if tipo_evento == "stock.disponible":
                payload["cantidad_nueva"] = stock.cantidad_disponible
            elif tipo_evento == "stock.bajo_umbral":
                payload["cantidad_actual"] = stock.cantidad_disponible
                payload["umbral_minimo"] = stock.umbral_minimo
            await self._pub.publish(EventEnvelope(
                tipo=tipo_evento, modulo_origen="stock", payload=payload
            ))

        return AjusteResult(stock=stock, eventos_publicados=eventos)


class ActualizarUmbralUseCase:
    """EP-STK-05: PATCH /v1/stock/{codigo}/umbral"""

    def __init__(self, repo: StockRepository) -> None:
        self._repo = repo

    async def execute(self, command: ActualizarUmbralCommand) -> StockRepuesto:
        stock = await self._repo.obtener_por_codigo(command.codigo)
        if stock is None:
            raise StockNoEncontradoError(
                f"Stock para código {command.codigo!r} no encontrado"
            )
        stock.ajustar_umbral(command.umbral_minimo)
        return await self._repo.actualizar(stock)

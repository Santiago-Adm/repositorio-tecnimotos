"""
EP-PED-01: Crear pedido.
EP-PED-02: Listar pedidos.
EP-PED-03: Obtener pedido.
EP-PED-04: Confirmar pedido.
EP-PED-05: Cancelar pedido.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.shared.events.envelope import EventEnvelope
from src.pedidos.domain.models.pedido import (
    DomainError,
    EstadoPedido,
    Pedido,
    PedidoItem,
    PedidoNoEncontradoError,
)
from src.pedidos.domain.ports.catalogo_pedidos_port import CatalogoPedidosPort
from src.pedidos.domain.ports.event_publisher import EventPublisher
from src.pedidos.domain.ports.pedido_repository import PedidoRepository
from src.pedidos.domain.ports.stock_pedidos_port import StockPedidosPort
from src.pedidos.domain.services.pedido_service import PedidoService


@dataclass
class ItemPedidoInput:
    codigo: str
    cantidad: int


@dataclass
class CrearPedidoCommand:
    canal_origen: str
    actor_id: str
    items: list[ItemPedidoInput] = field(default_factory=list)
    cliente_id: Optional[str] = None
    orden_trabajo_id: Optional[str] = None


@dataclass
class ConfirmarPedidoCommand:
    pedido_id: str
    actor_id: str


@dataclass
class CancelarPedidoCommand:
    pedido_id: str
    actor_id: str
    motivo: str
    es_cliente: bool = False


class CrearPedidoUseCase:
    """EP-PED-01: POST /v1/pedidos"""

    def __init__(
        self,
        repo: PedidoRepository,
        catalogo: CatalogoPedidosPort,
        event_publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._catalogo = catalogo
        self._pub = event_publisher

    async def execute(self, command: CrearPedidoCommand) -> Pedido:
        pedido = Pedido(
            canal_origen=command.canal_origen,
            origen_actor=command.actor_id,
            cliente_id=command.cliente_id,
            ot_id=command.orden_trabajo_id,
        )
        for item_input in command.items:
            info = await self._catalogo.obtener_precio_vigente(item_input.codigo)
            if not info.activo:
                raise DomainError(
                    f"Repuesto {item_input.codigo!r} está dado de baja"
                )
            item = PedidoItem(
                pedido_id=pedido.id,
                repuesto_id=info.repuesto_id,
                codigo=info.codigo,
                cantidad=item_input.cantidad,
                precio_unitario=info.precio_venta,
            )
            pedido.agregar_item(item)

        return await self._repo.guardar(pedido)


class ListarPedidosUseCase:
    """EP-PED-02: GET /v1/pedidos"""

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self, cliente_id: Optional[str] = None, actor_id: Optional[str] = None) -> list[Pedido]:
        if cliente_id:
            return await self._repo.listar_por_cliente(cliente_id)
        if actor_id:
            return await self._repo.listar_por_actor(actor_id)
        return await self._repo.listar_todos()


class ObtenerPedidoUseCase:
    """EP-PED-03: GET /v1/pedidos/{pedido_id}"""

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self, pedido_id: str) -> Pedido:
        pedido = await self._repo.obtener_por_id(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(f"Pedido {pedido_id} no encontrado")
        return pedido


class ConfirmarPedidoUseCase:
    """EP-PED-04: POST /v1/pedidos/{pedido_id}/confirmar"""

    def __init__(
        self,
        repo: PedidoRepository,
        stock: StockPedidosPort,
        event_publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._stock = stock
        self._pub = event_publisher

    async def execute(self, command: ConfirmarPedidoCommand) -> Pedido:
        pedido = await self._repo.obtener_por_id(command.pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(f"Pedido {command.pedido_id} no encontrado")

        if pedido.estado != EstadoPedido.BORRADOR:
            raise DomainError(
                f"Solo se puede confirmar desde BORRADOR, estado actual: {pedido.estado.value}"
            )

        for item in pedido.items:
            disp = await self._stock.consultar_disponibilidad(item.repuesto_id)
            if disp.cantidad_disponible < item.cantidad:
                pedido.cancelar("Stock insuficiente al confirmar")
                await self._repo.actualizar(pedido)
                raise DomainError(
                    f"Stock insuficiente para {item.codigo}: "
                    f"disponible={disp.cantidad_disponible}, requerido={item.cantidad}"
                )

        pedido.confirmar()
        await self._repo.actualizar(pedido)

        await self._pub.publish(EventEnvelope(
            tipo="pedido.confirmado",
            modulo_origen="pedidos",
            payload={
                "pedido_id": pedido.id,
                "repuestos": [
                    {"repuesto_id": i.repuesto_id, "cantidad": i.cantidad}
                    for i in pedido.items
                ],
                "cliente_id": pedido.cliente_id or "",
                "canal_origen": pedido.canal_origen,
            },
        ))
        return pedido


class CancelarPedidoUseCase:
    """EP-PED-05: POST /v1/pedidos/{pedido_id}/cancelar"""

    def __init__(self, repo: PedidoRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: CancelarPedidoCommand) -> Pedido:
        pedido = await self._repo.obtener_por_id(command.pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(f"Pedido {command.pedido_id} no encontrado")

        PedidoService.verificar_cancelacion_permitida(pedido, command.es_cliente)
        pedido.cancelar(command.motivo)
        await self._repo.actualizar(pedido)

        await self._pub.publish(EventEnvelope(
            tipo="pedido.cancelado",
            modulo_origen="pedidos",
            payload={
                "pedido_id": pedido.id,
                "repuestos": [
                    {"repuesto_id": i.repuesto_id, "cantidad": i.cantidad}
                    for i in pedido.items
                ],
                "motivo": command.motivo,
            },
        ))
        return pedido

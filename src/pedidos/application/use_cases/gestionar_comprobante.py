"""
EP-PED-15: Generar comprobante (VENDEDOR → PENDIENTE_VALIDACION siempre).
EP-PED-16: Aprobar y emitir comprobante.
EP-PED-17: Anular comprobante.
EP-PED-08: Emitir proforma.
EP-PED-09: Registrar envío.
EP-PED-10: Confirmar recepción.
EP-PED-11: Registrar incidencia.
EP-PED-13: Crear lista de reserva progresiva.
EP-PED-14: Formalizar lista de reserva progresiva.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.shared.events.envelope import EventEnvelope
from src.pedidos.domain.models.pedido import (
    Comprobante,
    ComprobanteNoEncontradoError,
    ComprobanteYaEmitidoError,
    DeudaActiva,
    DomainError,
    Envio,
    EstadoComprobante,
    EstadoPedido,
    ListaReservaProg,
    ListaReservaProg_Item,
    ListaReservaNoEncontradaError,
    PedidoNoEncontradoError,
    Proforma,
    ProformaNoEncontradaError,
    TipoComprobante,
    TransicionEstadoInvalidaError,
)
from src.pedidos.domain.ports.event_publisher import EventPublisher
from src.pedidos.domain.ports.pedido_repository import PedidoRepository
from src.pedidos.domain.services.pedido_service import PedidoService


@dataclass
class GenerarComprobanteCommand:
    pedido_id: str
    tipo: TipoComprobante
    monto: Decimal
    emitido_por: str
    rol_emisor: str
    ruc_cliente: Optional[str] = None


@dataclass
class AprobarComprobanteCommand:
    comprobante_id: str
    actor_id: str


@dataclass
class AnularComprobanteCommand:
    comprobante_id: str
    actor_id: str


@dataclass
class EmitirProformaCommand:
    pedido_id: str
    actor_id: str


@dataclass
class RegistrarEnvioCommand:
    pedido_id: str
    empresa_encomienda: str
    direccion_destino: str
    actor_id: str


@dataclass
class ItemListaInput:
    repuesto_id: str
    codigo: str
    cantidad: int
    precio_referencia: Decimal


@dataclass
class CrearListaReservaCommand:
    cliente_id: str
    nombre: Optional[str] = None
    items: list[ItemListaInput] = field(default_factory=list)


@dataclass
class FormalizarListaReservaCommand:
    lista_id: str
    actor_id: str


class GenerarComprobanteUseCase:
    """EP-PED-15: POST /v1/pedidos/{id}/comprobante"""

    def __init__(self, repo: PedidoRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: GenerarComprobanteCommand) -> Comprobante:
        pedido = await self._repo.obtener_por_id(command.pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(f"Pedido {command.pedido_id} no encontrado")

        comp = Comprobante(
            pedido_id=command.pedido_id,
            tipo=command.tipo,
            monto=command.monto,
            emitido_por=command.emitido_por,
            ruc_cliente=command.ruc_cliente,
            # VENDEDOR SIEMPRE genera PENDIENTE_VALIDACION (07 ABAC-06 corregido)
            estado=EstadoComprobante.PENDIENTE_VALIDACION,
        )

        await self._repo.guardar_comprobante(comp)

        # VENDEDOR siempre publica para validación
        if PedidoService.comprobante_requiere_validacion(command.rol_emisor):
            await self._pub.publish(EventEnvelope(
                tipo="comprobante.pendiente_validacion",
                modulo_origen="pedidos",
                payload={
                    "comprobante_id": comp.id,
                    "pedido_id": command.pedido_id,
                    "monto": str(command.monto),
                    "tipo": command.tipo.value,
                },
            ))

        return comp


class AprobarComprobanteUseCase:
    """EP-PED-16: POST /v1/comprobantes/{id}/aprobar"""

    def __init__(self, repo: PedidoRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: AprobarComprobanteCommand) -> Comprobante:
        comp = await self._repo.obtener_comprobante(command.comprobante_id)
        if comp is None:
            raise ComprobanteNoEncontradoError(
                f"Comprobante {command.comprobante_id} no encontrado"
            )
        comp.aprobar()
        await self._repo.actualizar_comprobante(comp)
        return comp


class AnularComprobanteUseCase:
    """EP-PED-17: POST /v1/comprobantes/{id}/anular"""

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self, command: AnularComprobanteCommand) -> Comprobante:
        comp = await self._repo.obtener_comprobante(command.comprobante_id)
        if comp is None:
            raise ComprobanteNoEncontradoError(
                f"Comprobante {command.comprobante_id} no encontrado"
            )
        nota_credito_id = str(uuid.uuid4())
        comp.anular(nota_credito_id)
        await self._repo.actualizar_comprobante(comp)
        return comp


class EmitirProformaUseCase:
    """EP-PED-08: POST /v1/pedidos/{id}/proforma"""

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self, command: EmitirProformaCommand) -> Proforma:
        pedido = await self._repo.obtener_por_id(command.pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(f"Pedido {command.pedido_id} no encontrado")

        numero_ref = f"PRF-{pedido.id[:8].upper()}"
        proforma = Proforma(
            pedido_id=command.pedido_id,
            numero_referencia=numero_ref,
            monto_total=pedido.monto_efectivo(),
        )
        return await self._repo.guardar_proforma(proforma)


class RegistrarEnvioUseCase:
    """EP-PED-09: POST /v1/pedidos/{id}/envio → pedido pasa a DESPACHADO"""

    def __init__(self, repo: PedidoRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: RegistrarEnvioCommand) -> Envio:
        pedido = await self._repo.obtener_por_id(command.pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(f"Pedido {command.pedido_id} no encontrado")

        pedido.despachar()
        await self._repo.actualizar(pedido)

        envio = Envio(
            pedido_id=command.pedido_id,
            empresa_encomienda=command.empresa_encomienda,
            direccion_destino=command.direccion_destino,
        )
        return await self._repo.guardar_envio(envio)


class ConfirmarRecepcionUseCase:
    """EP-PED-10: POST /v1/pedidos/{id}/confirmar-recepcion → ENTREGADO"""

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self, pedido_id: str, actor_id: str) -> None:
        pedido = await self._repo.obtener_por_id(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(f"Pedido {pedido_id} no encontrado")
        pedido.entregar()
        await self._repo.actualizar(pedido)


class RegistrarIncidenciaUseCase:
    """EP-PED-11: POST /v1/pedidos/{id}/incidencia → INCIDENCIA"""

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self, pedido_id: str, actor_id: str) -> None:
        pedido = await self._repo.obtener_por_id(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(f"Pedido {pedido_id} no encontrado")
        pedido.registrar_incidencia()
        await self._repo.actualizar(pedido)


class CrearListaReservaUseCase:
    """EP-PED-13: POST /v1/lista-reserva-progresiva"""

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self, command: CrearListaReservaCommand) -> ListaReservaProg:
        lista = ListaReservaProg(
            cliente_id=command.cliente_id,
            nombre=command.nombre,
        )
        for item_input in command.items:
            lista.agregar_item(ListaReservaProg_Item(
                lista_id=lista.id,
                repuesto_id=item_input.repuesto_id,
                codigo=item_input.codigo,
                cantidad=item_input.cantidad,
                precio_referencia=item_input.precio_referencia,
            ))
        return await self._repo.guardar_lista_reserva(lista)


class FormalizarListaReservaUseCase:
    """EP-PED-14: POST /v1/lista-reserva-progresiva/{lista_id}/formalizar → crea pedido BORRADOR"""

    def __init__(self, repo: PedidoRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: FormalizarListaReservaCommand) -> None:
        lista = await self._repo.obtener_lista_reserva(command.lista_id)
        if lista is None:
            raise ListaReservaNoEncontradaError(
                f"Lista {command.lista_id} no encontrada"
            )
        lista.confirmar()
        lista.formalizar()
        await self._repo.actualizar_lista_reserva(lista)

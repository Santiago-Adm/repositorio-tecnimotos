"""
Entidades del dominio pedidos (02 §1.3, §2.2).
Sin imports de FastAPI, SQLAlchemy ni Redis.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


# ── Errores de dominio ────────────────────────────────────────────────────────

class DomainError(Exception):
    pass


class PedidoNoEncontradoError(DomainError):
    pass


class TransicionEstadoInvalidaError(DomainError):
    pass


class ReservaNoEncontradaError(DomainError):
    pass


class ReservaExpiradaError(DomainError):
    pass


class ComprobanteNoEncontradoError(DomainError):
    pass


class ComprobanteYaEmitidoError(DomainError):
    pass


class ProformaNoEncontradaError(DomainError):
    pass


class ListaReservaNoEncontradaError(DomainError):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class EstadoPedido(str, Enum):
    BORRADOR       = "BORRADOR"
    CONFIRMADO     = "CONFIRMADO"
    EN_PREPARACION = "EN_PREPARACION"
    DESPACHADO     = "DESPACHADO"
    ENTREGADO      = "ENTREGADO"
    INCIDENCIA     = "INCIDENCIA"
    CANCELADO      = "CANCELADO"


class EstadoReserva(str, Enum):
    ACTIVA     = "ACTIVA"
    CONFIRMADA = "CONFIRMADA"
    EXPIRADA   = "EXPIRADA"
    LIBERADA   = "LIBERADA"


class SegmentoCliente(str, Enum):
    CONDUCTOR       = "CLIENTE_CONDUCTOR"
    DISTRITO        = "CLIENTE_DISTRITO"
    FLOTA_DUENO     = "CLIENTE_FLOTA_DUENO"
    FLOTA_CONDUCTOR = "CLIENTE_FLOTA_CONDUCTOR"
    RURAL           = "CLIENTE_RURAL"
    MOTOLINEAL      = "CLIENTE_MOTOLINEAL"


class EstadoProforma(str, Enum):
    BORRADOR            = "BORRADOR"
    ENVIADA             = "ENVIADA"
    ACEPTADA            = "ACEPTADA"
    RECHAZADA           = "RECHAZADA"
    VENCIDA             = "VENCIDA"


class EstadoEnvio(str, Enum):
    PREPARADO         = "PREPARADO"
    ENTREGADO_AGENCIA = "ENTREGADO_AGENCIA"
    EN_TRANSITO       = "EN_TRANSITO"
    ENTREGADO_CLIENTE = "ENTREGADO_CLIENTE"
    INCIDENCIA        = "INCIDENCIA"
    RESUELTO          = "RESUELTO"


class EstadoComprobante(str, Enum):
    PENDIENTE_VALIDACION = "PENDIENTE_VALIDACION"
    EMITIDO              = "EMITIDO"
    ENVIADO_CLIENTE      = "ENVIADO_CLIENTE"
    ANULADO              = "ANULADO"


class TipoComprobante(str, Enum):
    BOLETA  = "boleta"
    FACTURA = "factura"
    TICKET  = "ticket"


class EstadoListaReserva(str, Enum):
    BORRADOR    = "BORRADOR"
    CONFIRMADA  = "CONFIRMADA"
    FORMALIZADA = "FORMALIZADA"


# ── TTL por segmento ──────────────────────────────────────────────────────────

_TTL_POR_SEGMENTO: dict[SegmentoCliente, timedelta] = {
    SegmentoCliente.CONDUCTOR:       timedelta(days=1),
    SegmentoCliente.FLOTA_DUENO:     timedelta(days=1),
    SegmentoCliente.FLOTA_CONDUCTOR: timedelta(days=1),
    SegmentoCliente.DISTRITO:        timedelta(days=3),
    SegmentoCliente.RURAL:           timedelta(days=3),
    SegmentoCliente.MOTOLINEAL:      timedelta(days=2),
}


def ttl_para_segmento(segmento: SegmentoCliente) -> timedelta:
    return _TTL_POR_SEGMENTO.get(segmento, timedelta(days=1))


# ── Value Objects ─────────────────────────────────────────────────────────────

@dataclass
class PedidoItem:
    pedido_id: str
    repuesto_id: str
    codigo: str
    cantidad: int
    precio_unitario: Decimal
    precio_ajustado_unit: Optional[Decimal] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise DomainError("cantidad del ítem debe ser > 0")
        if self.precio_unitario <= Decimal("0"):
            raise DomainError("precio_unitario debe ser > 0")

    @property
    def subtotal(self) -> Decimal:
        precio = self.precio_ajustado_unit or self.precio_unitario
        return precio * self.cantidad


@dataclass
class ListaReservaProg_Item:
    lista_id: str
    repuesto_id: str
    codigo: str
    cantidad: int
    precio_referencia: Decimal
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise DomainError("cantidad debe ser > 0")


# ── Agregados ─────────────────────────────────────────────────────────────────

@dataclass
class Reserva:
    """
    Apartamiento temporal de un repuesto del stock para un cliente (02 §1.1).
    TTL diferenciado por segmento de cliente (02 §2.2).
    """
    cliente_id: str
    repuesto_id: str
    cantidad: int
    segmento: SegmentoCliente
    estado: EstadoReserva = EstadoReserva.ACTIVA
    pedido_id: Optional[str] = None
    pago_registrado: bool = False
    notificaciones_enviadas: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    expira_en: datetime = field(init=False)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    _TRANSICIONES_VALIDAS: dict[EstadoReserva, list[EstadoReserva]] = field(
        default_factory=lambda: {
            EstadoReserva.ACTIVA: [EstadoReserva.CONFIRMADA, EstadoReserva.EXPIRADA, EstadoReserva.LIBERADA],
            EstadoReserva.CONFIRMADA: [EstadoReserva.LIBERADA, EstadoReserva.EXPIRADA],
            EstadoReserva.EXPIRADA: [],
            EstadoReserva.LIBERADA: [],
        },
        init=False,
    )

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise DomainError("cantidad de reserva debe ser > 0")
        self.expira_en = self.created_at + ttl_para_segmento(self.segmento)

    def esta_vigente(self) -> bool:
        return (
            self.estado in (EstadoReserva.ACTIVA, EstadoReserva.CONFIRMADA)
            and datetime.now(timezone.utc) < self.expira_en
        )

    def esta_expirada(self) -> bool:
        return datetime.now(timezone.utc) >= self.expira_en

    def avanzar_estado(self, nuevo_estado: EstadoReserva) -> None:
        permitidos = self._TRANSICIONES_VALIDAS.get(self.estado, [])
        if nuevo_estado not in permitidos:
            raise TransicionEstadoInvalidaError(
                f"Transición inválida: {self.estado.value} → {nuevo_estado.value}"
            )
        self.estado = nuevo_estado

    def liberar(self, motivo: str = "LIBERADA_MANUAL") -> None:
        self.avanzar_estado(EstadoReserva.LIBERADA)

    def expirar(self) -> None:
        self.avanzar_estado(EstadoReserva.EXPIRADA)

    def confirmar(self) -> None:
        self.avanzar_estado(EstadoReserva.CONFIRMADA)


@dataclass
class Proforma:
    """Cotización formal emitida antes de confirmar el pedido (02 §1.1)."""
    pedido_id: str
    numero_referencia: str
    monto_total: Decimal
    estado: EstadoProforma = EstadoProforma.BORRADOR
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.monto_total <= Decimal("0"):
            raise DomainError("monto_total de proforma debe ser > 0")
        if not self.numero_referencia.strip():
            raise DomainError("numero_referencia no puede estar vacío")

    def enviar(self) -> None:
        if self.estado != EstadoProforma.BORRADOR:
            raise TransicionEstadoInvalidaError(
                f"Solo se puede enviar desde BORRADOR, estado actual: {self.estado.value}"
            )
        self.estado = EstadoProforma.ENVIADA


@dataclass
class Envio:
    """Despacho físico hacia un cliente externo a la ciudad (02 §1.1)."""
    pedido_id: str
    empresa_encomienda: str
    direccion_destino: str
    estado: EstadoEnvio = EstadoEnvio.PREPARADO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    _TRANSICIONES_VALIDAS: dict[EstadoEnvio, list[EstadoEnvio]] = field(
        default_factory=lambda: {
            EstadoEnvio.PREPARADO: [EstadoEnvio.ENTREGADO_AGENCIA],
            EstadoEnvio.ENTREGADO_AGENCIA: [EstadoEnvio.EN_TRANSITO, EstadoEnvio.INCIDENCIA],
            EstadoEnvio.EN_TRANSITO: [EstadoEnvio.ENTREGADO_CLIENTE, EstadoEnvio.INCIDENCIA],
            EstadoEnvio.ENTREGADO_CLIENTE: [],
            EstadoEnvio.INCIDENCIA: [EstadoEnvio.RESUELTO],
            EstadoEnvio.RESUELTO: [],
        },
        init=False,
    )

    def __post_init__(self) -> None:
        if not self.empresa_encomienda.strip():
            raise DomainError("empresa_encomienda no puede estar vacía")
        if not self.direccion_destino.strip():
            raise DomainError("direccion_destino no puede estar vacía")

    def avanzar_estado(self, nuevo_estado: EstadoEnvio) -> None:
        permitidos = self._TRANSICIONES_VALIDAS.get(self.estado, [])
        if nuevo_estado not in permitidos:
            raise TransicionEstadoInvalidaError(
                f"Transición inválida: {self.estado.value} → {nuevo_estado.value}"
            )
        self.estado = nuevo_estado


@dataclass
class Comprobante:
    """Documento tributario electrónico emitido al cierre de transacción (02 §1.1)."""
    pedido_id: str
    tipo: TipoComprobante
    monto: Decimal
    emitido_por: str
    estado: EstadoComprobante = EstadoComprobante.PENDIENTE_VALIDACION
    ruc_cliente: Optional[str] = None
    nota_credito_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.monto <= Decimal("0"):
            raise DomainError("monto del comprobante debe ser > 0")

    def aprobar(self) -> None:
        if self.estado != EstadoComprobante.PENDIENTE_VALIDACION:
            raise TransicionEstadoInvalidaError(
                f"Solo se puede aprobar desde PENDIENTE_VALIDACION, estado: {self.estado.value}"
            )
        self.estado = EstadoComprobante.EMITIDO

    def marcar_enviado(self) -> None:
        if self.estado != EstadoComprobante.EMITIDO:
            raise TransicionEstadoInvalidaError(
                f"Solo se puede marcar enviado desde EMITIDO, estado: {self.estado.value}"
            )
        self.estado = EstadoComprobante.ENVIADO_CLIENTE

    def anular(self, nota_credito_id: str) -> None:
        if self.estado not in (EstadoComprobante.EMITIDO, EstadoComprobante.ENVIADO_CLIENTE):
            raise TransicionEstadoInvalidaError(
                f"Solo se puede anular desde EMITIDO o ENVIADO_CLIENTE, estado: {self.estado.value}"
            )
        self.nota_credito_id = nota_credito_id
        self.estado = EstadoComprobante.ANULADO

    def esta_emitido(self) -> bool:
        return self.estado in (EstadoComprobante.EMITIDO, EstadoComprobante.ENVIADO_CLIENTE)


@dataclass
class DeudaActiva:
    """Saldo pendiente por excepción del 80% (02 §2.2)."""
    pedido_id: str
    cliente_id: str
    monto_deuda: Decimal
    plazo_dias: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.monto_deuda <= Decimal("0"):
            raise DomainError("monto_deuda debe ser > 0")
        if self.plazo_dias <= 0:
            raise DomainError("plazo_dias debe ser > 0")

    @property
    def alerta_50_en(self) -> datetime:
        return self.created_at + timedelta(days=self.plazo_dias // 2)

    @property
    def alerta_vencimiento_en(self) -> datetime:
        return self.created_at + timedelta(days=self.plazo_dias - 1)

    @property
    def vence_en(self) -> datetime:
        return self.created_at + timedelta(days=self.plazo_dias)


@dataclass
class ListaReservaProg:
    """Lista de reserva progresiva para CLIENTE_DISTRITO (02 §2.2)."""
    cliente_id: str
    nombre: Optional[str] = None
    estado: EstadoListaReserva = EstadoListaReserva.BORRADOR
    items: list[ListaReservaProg_Item] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ultima_actividad: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def agregar_item(self, item: ListaReservaProg_Item) -> None:
        if self.estado != EstadoListaReserva.BORRADOR:
            raise DomainError("Solo se pueden agregar ítems en estado BORRADOR")
        self.items.append(item)
        self.ultima_actividad = datetime.now(timezone.utc)

    def confirmar(self) -> None:
        if not self.items:
            raise DomainError("No se puede confirmar una lista sin ítems")
        if self.estado != EstadoListaReserva.BORRADOR:
            raise TransicionEstadoInvalidaError(
                f"Solo se puede confirmar desde BORRADOR, estado: {self.estado.value}"
            )
        self.estado = EstadoListaReserva.CONFIRMADA

    def formalizar(self) -> None:
        if self.estado != EstadoListaReserva.CONFIRMADA:
            raise TransicionEstadoInvalidaError(
                f"Solo se puede formalizar desde CONFIRMADA, estado: {self.estado.value}"
            )
        self.estado = EstadoListaReserva.FORMALIZADA


@dataclass
class Pedido:
    """
    Solicitud de repuestos hecha por un cliente (02 §1.1).
    Ciclo de vida con 7 estados (02 §1.3).
    """
    canal_origen: str
    origen_actor: str
    cliente_id: Optional[str] = None
    ot_id: Optional[str] = None
    estado: EstadoPedido = EstadoPedido.BORRADOR
    items: list[PedidoItem] = field(default_factory=list)
    monto_total: Decimal = Decimal("0")
    descuento_aplicado: Optional[Decimal] = None
    precio_ajustado: Optional[Decimal] = None
    motivo_cancelacion: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    _TRANSICIONES_VALIDAS: dict[EstadoPedido, list[EstadoPedido]] = field(
        default_factory=lambda: {
            EstadoPedido.BORRADOR:       [EstadoPedido.CONFIRMADO, EstadoPedido.CANCELADO],
            EstadoPedido.CONFIRMADO:     [EstadoPedido.EN_PREPARACION, EstadoPedido.CANCELADO],
            EstadoPedido.EN_PREPARACION: [EstadoPedido.DESPACHADO, EstadoPedido.CANCELADO],
            EstadoPedido.DESPACHADO:     [EstadoPedido.ENTREGADO, EstadoPedido.INCIDENCIA],
            EstadoPedido.ENTREGADO:      [],
            EstadoPedido.INCIDENCIA:     [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO],
            EstadoPedido.CANCELADO:      [],
        },
        init=False,
    )

    def __post_init__(self) -> None:
        if not self.canal_origen.strip():
            raise DomainError("canal_origen no puede estar vacío")

    def agregar_item(self, item: PedidoItem) -> None:
        if self.estado != EstadoPedido.BORRADOR:
            raise DomainError("Solo se pueden agregar ítems en estado BORRADOR")
        self.items.append(item)
        self._recalcular_total()

    def _recalcular_total(self) -> None:
        self.monto_total = sum(i.subtotal for i in self.items)
        self.updated_at = datetime.now(timezone.utc)

    def avanzar_estado(self, nuevo_estado: EstadoPedido, motivo: Optional[str] = None) -> None:
        permitidos = self._TRANSICIONES_VALIDAS.get(self.estado, [])
        if nuevo_estado not in permitidos:
            raise TransicionEstadoInvalidaError(
                f"Transición inválida: {self.estado.value} → {nuevo_estado.value}"
            )
        if nuevo_estado == EstadoPedido.CANCELADO:
            self.motivo_cancelacion = motivo
        self.estado = nuevo_estado
        self.updated_at = datetime.now(timezone.utc)

    def confirmar(self) -> None:
        self.avanzar_estado(EstadoPedido.CONFIRMADO)

    def cancelar(self, motivo: str) -> None:
        self.avanzar_estado(EstadoPedido.CANCELADO, motivo=motivo)

    def despachar(self) -> None:
        self.avanzar_estado(EstadoPedido.DESPACHADO)

    def entregar(self) -> None:
        self.avanzar_estado(EstadoPedido.ENTREGADO)

    def registrar_incidencia(self) -> None:
        self.avanzar_estado(EstadoPedido.INCIDENCIA)

    def aplicar_descuento(self, descuento: Decimal, precio_final: Decimal) -> None:
        if self.estado != EstadoPedido.BORRADOR:
            raise DomainError("Solo se pueden aplicar descuentos en BORRADOR")
        if descuento < Decimal("0"):
            raise DomainError("descuento no puede ser negativo")
        self.descuento_aplicado = descuento
        self.precio_ajustado = precio_final
        self.updated_at = datetime.now(timezone.utc)

    def monto_efectivo(self) -> Decimal:
        return self.precio_ajustado if self.precio_ajustado is not None else self.monto_total

    def esta_cancelado(self) -> bool:
        return self.estado == EstadoPedido.CANCELADO

    def esta_entregado(self) -> bool:
        return self.estado == EstadoPedido.ENTREGADO

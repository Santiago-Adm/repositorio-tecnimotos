"""
Entidades del dominio taller (02 §1.3, §2.1).
Sin imports de FastAPI, SQLAlchemy ni Redis.
Vocabulario canónico: OrdenTrabajo (NO Ticket/Trabajo/Servicio),
Mecanico (NO Tecnico/Operario). Ver 02 §1.1.
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


class OrdenTrabajoNoEncontradaError(DomainError):
    pass


class TransicionEstadoInvalidaError(DomainError):
    pass


class ListaNoConfirmadaError(DomainError):
    pass


class CobroNoConfirmadoError(DomainError):
    pass


class VehiculoNoEncontradoError(DomainError):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class EstadoOrdenTrabajo(str, Enum):
    ABIERTA         = "ABIERTA"
    LISTA_REPUESTOS = "LISTA_REPUESTOS"
    EN_EJECUCION    = "EN_EJECUCION"
    REVISION_FINAL  = "REVISION_FINAL"
    CERRADA         = "CERRADA"
    CANCELADA       = "CANCELADA"


class ModalidadIntervencion(str, Enum):
    """Modalidad de la intervención sobre el vehículo (02 §1.3)."""
    PREVENTIVO  = "preventivo"
    CORRECTIVO  = "correctivo"
    DIAGNOSTICO = "diagnostico"
    SOLDADURA   = "soldadura"


class NivelUrgencia(str, Enum):
    ALTA   = "alta"
    MEDIA  = "media"
    BAJA   = "baja"


class NivelMecanico(str, Enum):
    MASTER = "MASTER"
    JUNIOR = "JUNIOR"


class EstadoAprobacion(str, Enum):
    PENDIENTE            = "PENDIENTE"
    APROBADO_AUTOMATICO  = "APROBADO_AUTOMATICO"
    APROBADO_TACITO      = "APROBADO_TACITO"
    APROBADO_EXPLICITO   = "APROBADO_EXPLICITO"
    RECHAZADO            = "RECHAZADO"
    PENDIENTE_ADICIONAL  = "PENDIENTE_ADICIONAL"


class TramoAdicional(str, Enum):
    AUTOMATICO = "automatico"
    TACITO     = "tacito"
    MANUAL     = "manual"


class EstadoEntrada(str, Enum):
    ACTIVA  = "ACTIVA"
    CERRADA = "CERRADA"


# ── Umbrales de costo adicional (02 §2.1, HU-INT-03) ─────────────────────────

UMBRAL_APROBACION_AUTOMATICA = Decimal("30.00")
UMBRAL_APROBACION_TACITA     = Decimal("100.00")
MINUTOS_ESPERA_TACITA        = 30


# ── Value Objects ─────────────────────────────────────────────────────────────

@dataclass
class ListaRepuestosOT:
    """Item de repuesto en la lista de una OrdenTrabajo (03 §5.5)."""
    orden_trabajo_id: str
    repuesto_id: str
    codigo: str
    cantidad: int
    precio_unitario: Decimal
    momento_agregado: str  # "inicial" | "en_ejecucion"
    tramo_precio: Optional[TramoAdicional] = None
    aprobacion_cliente: EstadoAprobacion = EstadoAprobacion.PENDIENTE
    aprobado_en: Optional[datetime] = None
    espera_hasta: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise DomainError("cantidad debe ser > 0")
        if self.precio_unitario <= Decimal("0"):
            raise DomainError("precio_unitario debe ser > 0")

    @property
    def subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad

    def determinar_tramo(self) -> TramoAdicional:
        if self.precio_unitario < UMBRAL_APROBACION_AUTOMATICA:
            return TramoAdicional.AUTOMATICO
        if self.precio_unitario <= UMBRAL_APROBACION_TACITA:
            return TramoAdicional.TACITO
        return TramoAdicional.MANUAL

    def aprobar_automaticamente(self) -> None:
        self.tramo_precio = TramoAdicional.AUTOMATICO
        self.aprobacion_cliente = EstadoAprobacion.APROBADO_AUTOMATICO
        self.aprobado_en = datetime.now(timezone.utc)

    def iniciar_espera_tacita(self) -> None:
        self.tramo_precio = TramoAdicional.TACITO
        self.aprobacion_cliente = EstadoAprobacion.PENDIENTE_ADICIONAL
        self.espera_hasta = datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_ESPERA_TACITA)

    def aprobar_tacitamente(self) -> None:
        self.aprobacion_cliente = EstadoAprobacion.APROBADO_TACITO
        self.aprobado_en = datetime.now(timezone.utc)

    def aprobar_explicitamente(self) -> None:
        self.aprobacion_cliente = EstadoAprobacion.APROBADO_EXPLICITO
        self.aprobado_en = datetime.now(timezone.utc)

    def rechazar(self) -> None:
        self.aprobacion_cliente = EstadoAprobacion.RECHAZADO

    def esta_aprobado(self) -> bool:
        return self.aprobacion_cliente in (
            EstadoAprobacion.APROBADO_AUTOMATICO,
            EstadoAprobacion.APROBADO_TACITO,
            EstadoAprobacion.APROBADO_EXPLICITO,
        )

    def espera_expirada(self) -> bool:
        if self.espera_hasta is None:
            return False
        return datetime.now(timezone.utc) >= self.espera_hasta


@dataclass
class CostoAdicionalOT:
    """Registro de un costo adicional por tramo de precio (03 §5.5)."""
    orden_trabajo_id: str
    lista_repuesto_id: str
    tramo: TramoAdicional
    monto_adicional: Decimal
    espera_hasta: Optional[datetime] = None
    resultado: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class HistorialIntervencion:
    """Registro histórico de una intervención cerrada (03 §5.5)."""
    vehiculo_id: str
    orden_trabajo_id: str
    mecanico_master_id: str
    fecha_apertura: datetime
    fecha_cierre: datetime
    monto_final: Decimal
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


# ── Agregados ─────────────────────────────────────────────────────────────────

@dataclass
class Vehiculo:
    """Mototaxi o motolineal registrado en el sistema (02 §1.1)."""
    universo: str
    modelo: str
    año: int
    cliente_id: Optional[str] = None
    placa: Optional[str] = None
    salud_estimada: int = 100
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not (1990 <= self.año <= 2100):
            raise DomainError(f"año debe estar entre 1990 y 2100, recibido: {self.año}")
        if not (0 <= self.salud_estimada <= 100):
            raise DomainError("salud_estimada debe estar entre 0 y 100")


@dataclass
class Mecanico:
    """
    Miembro del equipo técnico del taller (02 §1.1).
    NOTA: 'Mecanico' es el término canónico — NO usar Tecnico ni Operario.
    """
    usuario_id: str
    nivel: NivelMecanico
    supervisor_id: Optional[str] = None
    disponible: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Entrada:
    """Interacción registrada de un cliente con el taller (02 §1.1)."""
    vehiculo_id: str
    orden_trabajo_id: Optional[str] = None
    cliente_id: Optional[str] = None
    estado: EstadoEntrada = EstadoEntrada.ACTIVA
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def cerrar(self) -> None:
        if self.estado != EstadoEntrada.ACTIVA:
            raise DomainError("Solo se puede cerrar una entrada ACTIVA")
        self.estado = EstadoEntrada.CERRADA


@dataclass
class OrdenTrabajo:
    """
    Registro formal de una intervención técnica sobre un vehículo (02 §1.1).
    6 estados: ABIERTA → LISTA_REPUESTOS → EN_EJECUCION → REVISION_FINAL → CERRADA | CANCELADA.
    """
    vehiculo_id: str
    mecanico_master_id: str
    modalidad: ModalidadIntervencion
    urgencia: NivelUrgencia
    mecanico_junior_id: Optional[str] = None
    cliente_id: Optional[str] = None
    estado: EstadoOrdenTrabajo = EstadoOrdenTrabajo.ABIERTA
    lista_repuestos: list[ListaRepuestosOT] = field(default_factory=list)
    cobro_confirmado: bool = False
    visibilidad_precio_cliente: bool = False
    cliente_aprobo_lista: bool = False
    costo_mano_obra: Optional[Decimal] = None
    monto_estimado: Decimal = Decimal("0")
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    _TRANSICIONES_VALIDAS: dict[EstadoOrdenTrabajo, list[EstadoOrdenTrabajo]] = field(
        default_factory=lambda: {
            EstadoOrdenTrabajo.ABIERTA: [
                EstadoOrdenTrabajo.LISTA_REPUESTOS,
                EstadoOrdenTrabajo.CANCELADA,
            ],
            EstadoOrdenTrabajo.LISTA_REPUESTOS: [
                EstadoOrdenTrabajo.EN_EJECUCION,
                EstadoOrdenTrabajo.CANCELADA,
            ],
            EstadoOrdenTrabajo.EN_EJECUCION: [
                EstadoOrdenTrabajo.REVISION_FINAL,
                EstadoOrdenTrabajo.CANCELADA,
            ],
            EstadoOrdenTrabajo.REVISION_FINAL: [
                EstadoOrdenTrabajo.CERRADA,
                EstadoOrdenTrabajo.CANCELADA,
            ],
            EstadoOrdenTrabajo.CERRADA: [],
            EstadoOrdenTrabajo.CANCELADA: [],
        },
        init=False,
    )

    def avanzar_estado(self, nuevo_estado: EstadoOrdenTrabajo) -> None:
        permitidos = self._TRANSICIONES_VALIDAS.get(self.estado, [])
        if nuevo_estado not in permitidos:
            raise TransicionEstadoInvalidaError(
                f"Transición inválida: {self.estado.value} → {nuevo_estado.value}"
            )
        self.estado = nuevo_estado
        self.updated_at = datetime.now(timezone.utc)

    def agregar_repuesto_inicial(self, item: ListaRepuestosOT) -> None:
        if self.estado != EstadoOrdenTrabajo.ABIERTA:
            raise DomainError("Solo se pueden agregar repuestos iniciales en estado ABIERTA")
        self.lista_repuestos.append(item)
        self._recalcular_monto()

    def agregar_repuesto_en_ejecucion(self, item: ListaRepuestosOT) -> None:
        if self.estado != EstadoOrdenTrabajo.EN_EJECUCION:
            raise DomainError("Solo se pueden agregar repuestos durante EN_EJECUCION")
        tramo = item.determinar_tramo()
        if tramo == TramoAdicional.AUTOMATICO:
            item.aprobar_automaticamente()
        elif tramo == TramoAdicional.TACITO:
            item.iniciar_espera_tacita()
        else:
            item.tramo_precio = TramoAdicional.MANUAL
            item.aprobacion_cliente = EstadoAprobacion.PENDIENTE_ADICIONAL
        self.lista_repuestos.append(item)
        self._recalcular_monto()

    def _recalcular_monto(self) -> None:
        self.monto_estimado = sum(i.subtotal for i in self.lista_repuestos)
        self.updated_at = datetime.now(timezone.utc)

    def presentar_lista_al_cliente(self) -> None:
        """Transición ABIERTA → LISTA_REPUESTOS."""
        if not self.lista_repuestos:
            raise DomainError("No se puede presentar lista sin repuestos")
        self.avanzar_estado(EstadoOrdenTrabajo.LISTA_REPUESTOS)

    def aprobar_lista(self) -> None:
        """Cliente aprueba la lista → EN_EJECUCION."""
        if self.estado != EstadoOrdenTrabajo.LISTA_REPUESTOS:
            raise DomainError(
                f"Solo se puede aprobar la lista en LISTA_REPUESTOS, estado: {self.estado.value}"
            )
        for item in self.lista_repuestos:
            if item.momento_agregado == "inicial":
                item.aprobar_automaticamente()
        self.cliente_aprobo_lista = True
        self.avanzar_estado(EstadoOrdenTrabajo.EN_EJECUCION)

    def declarar_revision_final(
        self, costo_mano_obra: Decimal, mecanico_master_id: str
    ) -> None:
        """
        MECANICO_MASTER declara vehículo listo (HU-INT-04).
        Requiere lista verificada y costo de mano de obra declarado.
        """
        if self.estado != EstadoOrdenTrabajo.EN_EJECUCION:
            raise DomainError(
                f"Solo desde EN_EJECUCION, estado: {self.estado.value}"
            )
        items_bloqueantes = [
            i for i in self.lista_repuestos
            if i.aprobacion_cliente == EstadoAprobacion.PENDIENTE_ADICIONAL
            and i.tramo_precio == TramoAdicional.MANUAL
        ]
        if items_bloqueantes:
            raise DomainError(
                f"Hay {len(items_bloqueantes)} ítem(s) con aprobación manual pendiente"
            )
        if costo_mano_obra < Decimal("0"):
            raise DomainError("costo_mano_obra no puede ser negativo")
        self.costo_mano_obra = costo_mano_obra
        self.avanzar_estado(EstadoOrdenTrabajo.REVISION_FINAL)

    def cerrar(self) -> None:
        """Cierre tras cobro confirmado (HU-INT-04)."""
        if not self.cobro_confirmado:
            raise CobroNoConfirmadoError(
                "No se puede cerrar sin cobro_confirmado = True"
            )
        if not self.cliente_aprobo_lista:
            raise ListaNoConfirmadaError(
                "No se puede cerrar sin lista aprobada por el cliente"
            )
        self.avanzar_estado(EstadoOrdenTrabajo.CERRADA)

    def cancelar(self) -> None:
        self.avanzar_estado(EstadoOrdenTrabajo.CANCELADA)

    def confirmar_cobro(self) -> None:
        self.cobro_confirmado = True
        self.updated_at = datetime.now(timezone.utc)

    def autorizar_precio_cliente(self) -> None:
        self.visibilidad_precio_cliente = True
        self.updated_at = datetime.now(timezone.utc)

    def repuestos_aprobados(self) -> list[ListaRepuestosOT]:
        return [i for i in self.lista_repuestos if i.esta_aprobado()]

    def tiene_pendiente_manual(self) -> bool:
        return any(
            i.aprobacion_cliente == EstadoAprobacion.PENDIENTE_ADICIONAL
            and i.tramo_precio == TramoAdicional.MANUAL
            for i in self.lista_repuestos
        )

    def monto_total_con_mano_obra(self) -> Decimal:
        mo = self.costo_mano_obra or Decimal("0")
        return self.monto_estimado + mo

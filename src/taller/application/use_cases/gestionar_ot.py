"""
EP-TAL-01: Abrir orden_trabajo.
EP-TAL-02: Agregar repuesto (inicial en ABIERTA o adicional en EN_EJECUCION).
EP-TAL-03: Aprobar lista → EN_EJECUCION.
EP-TAL-04: Confirmar adicional (cliente confirma tramo MANUAL).
EP-TAL-05: Autorizar visibilidad de precio al cliente.
EP-TAL-06: Declarar revisión final → REVISION_FINAL.
EP-TAL-07: Registrar cobro parcial (excepción 80%).
EP-TAL-08: Cerrar orden_trabajo.
EP-TAL-09: Cancelar orden_trabajo.
EP-TAL-10: Liberar vehículo tras prueba de ruta.
EP-TAL-11: Consultar disponibilidad de mecánicos.
EP-TAL-12: Obtener orden_trabajo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from src.shared.events.envelope import EventEnvelope
from src.taller.domain.models.orden_trabajo import (
    CobroNoConfirmadoError,
    DomainError,
    Entrada,
    EstadoOrdenTrabajo,
    HistorialIntervencion,
    ListaNoConfirmadaError,
    ListaRepuestosOT,
    Mecanico,
    ModalidadIntervencion,
    NivelUrgencia,
    OrdenTrabajo,
    OrdenTrabajoNoEncontradaError,
    TransicionEstadoInvalidaError,
    Vehiculo,
    VehiculoNoEncontradoError,
)
from src.taller.domain.ports.catalogo_taller_port import CatalogoTallerPort
from src.taller.domain.ports.event_publisher import EventPublisher
from src.taller.domain.ports.taller_repository import TallerRepository
from src.taller.domain.services.taller_service import TallerService


# ── Commands ──────────────────────────────────────────────────────────────────

@dataclass
class AbrirOrdenTrabajoCommand:
    vehiculo_id: str
    mecanico_master_id: str
    modalidad: ModalidadIntervencion
    urgencia: NivelUrgencia
    actor_id: str
    mecanico_junior_id: Optional[str] = None
    cliente_id: Optional[str] = None


@dataclass
class AgregarRepuestoCommand:
    ot_id: str
    codigo: str
    cantidad: int
    actor_id: str


@dataclass
class AprobarListaCommand:
    ot_id: str
    actor_id: str


@dataclass
class ConfirmarAdicionalCommand:
    ot_id: str
    item_id: str
    actor_id: str


@dataclass
class AutorizarPrecioCommand:
    ot_id: str
    cliente_id: str
    actor_id: str


@dataclass
class RevisionFinalCommand:
    ot_id: str
    costo_mano_obra: Decimal
    actor_id: str


@dataclass
class CobroParcialCommand:
    ot_id: str
    monto_pagado: Decimal
    plazo_dias: int
    actor_id: str


@dataclass
class CerrarOTCommand:
    ot_id: str
    actor_id: str


@dataclass
class CancelarOTCommand:
    ot_id: str
    motivo: str
    actor_id: str


@dataclass
class LiberarVehiculoCommand:
    ot_id: str
    actor_id: str


# ── Use cases ─────────────────────────────────────────────────────────────────

class AbrirOrdenTrabajoUseCase:
    """EP-TAL-01: POST /v1/ordenes-trabajo"""

    def __init__(self, repo: TallerRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: AbrirOrdenTrabajoCommand) -> OrdenTrabajo:
        vehiculo = await self._repo.obtener_vehiculo(command.vehiculo_id)
        if vehiculo is None:
            raise VehiculoNoEncontradoError(
                f"Vehículo {command.vehiculo_id} no encontrado"
            )
        ot = OrdenTrabajo(
            vehiculo_id=command.vehiculo_id,
            mecanico_master_id=command.mecanico_master_id,
            modalidad=command.modalidad,
            urgencia=command.urgencia,
            mecanico_junior_id=command.mecanico_junior_id,
            cliente_id=command.cliente_id,
        )
        await self._repo.guardar_ot(ot)

        entrada = Entrada(
            vehiculo_id=command.vehiculo_id,
            orden_trabajo_id=ot.id,
            cliente_id=command.cliente_id,
        )
        await self._repo.guardar_entrada(entrada)

        await self._pub.publish(EventEnvelope(
            tipo="orden_trabajo.abierta",
            modulo_origen="taller",
            payload={
                "orden_trabajo_id": ot.id,
                "vehiculo_id": command.vehiculo_id,
                "mecanico_id": command.mecanico_master_id,
                "tipo_intervencion": command.modalidad.value,
            },
        ))
        return ot


class AgregarRepuestoUseCase:
    """EP-TAL-02: POST /v1/ordenes-trabajo/{id}/repuestos"""

    def __init__(
        self,
        repo: TallerRepository,
        catalogo: CatalogoTallerPort,
        event_publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._catalogo = catalogo
        self._pub = event_publisher

    async def execute(self, command: AgregarRepuestoCommand) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(command.ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {command.ot_id} no encontrada")

        info = await self._catalogo.obtener_precio_para_ot(command.codigo)
        if not info.activo:
            raise DomainError(f"Repuesto {command.codigo!r} está dado de baja")

        item = ListaRepuestosOT(
            orden_trabajo_id=ot.id,
            repuesto_id=info.repuesto_id,
            codigo=info.codigo,
            cantidad=command.cantidad,
            precio_unitario=info.precio_venta,
            momento_agregado="en_ejecucion" if ot.estado == EstadoOrdenTrabajo.EN_EJECUCION else "inicial",
        )

        if ot.estado == EstadoOrdenTrabajo.EN_EJECUCION:
            ot.agregar_repuesto_en_ejecucion(item)
            await self._pub.publish(EventEnvelope(
                tipo="orden_trabajo.repuesto_agregado",
                modulo_origen="taller",
                payload={
                    "orden_trabajo_id": ot.id,
                    "repuesto_id": info.repuesto_id,
                    "cantidad": command.cantidad,
                    "precio_vigente": str(info.precio_venta),
                    "monto_actualizado": str(ot.monto_estimado),
                    "tramo": item.tramo_precio.value if item.tramo_precio else "inicial",
                },
            ))
        elif ot.estado == EstadoOrdenTrabajo.ABIERTA:
            ot.agregar_repuesto_inicial(item)
        else:
            raise DomainError(
                f"No se pueden agregar repuestos en estado {ot.estado.value}"
            )

        await self._repo.actualizar_ot(ot)
        return ot


class AprobarListaUseCase:
    """EP-TAL-03: POST /v1/ordenes-trabajo/{id}/aprobar-lista → EN_EJECUCION"""

    def __init__(self, repo: TallerRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: AprobarListaCommand) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(command.ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {command.ot_id} no encontrada")

        # Si viene de ABIERTA, primero presentar la lista al cliente
        if ot.estado == EstadoOrdenTrabajo.ABIERTA:
            ot.presentar_lista_al_cliente()
        ot.aprobar_lista()
        await self._repo.actualizar_ot(ot)

        repuestos_payload = [
            {
                "repuesto_id": i.repuesto_id,
                "cantidad": i.cantidad,
                "precio_unitario": str(i.precio_unitario),
            }
            for i in ot.lista_repuestos
        ]
        await self._pub.publish(EventEnvelope(
            tipo="orden_trabajo.lista_aprobada",
            modulo_origen="taller",
            payload={
                "orden_trabajo_id": ot.id,
                "repuestos": repuestos_payload,
                "monto_estimado": str(ot.monto_estimado),
                "cliente_id": ot.cliente_id or "",
            },
        ))
        return ot


class ConfirmarAdicionalUseCase:
    """EP-TAL-04: POST /v1/ordenes-trabajo/{id}/confirmar-adicional"""

    def __init__(self, repo: TallerRepository) -> None:
        self._repo = repo

    async def execute(self, command: ConfirmarAdicionalCommand) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(command.ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {command.ot_id} no encontrada")

        item = next((i for i in ot.lista_repuestos if i.id == command.item_id), None)
        if item is None:
            raise DomainError(f"Ítem {command.item_id} no encontrado en la OT")

        item.aprobar_explicitamente()
        await self._repo.actualizar_ot(ot)
        return ot


class AutorizarPrecioUseCase:
    """EP-TAL-05: POST /v1/ordenes-trabajo/{id}/autorizar-precio"""

    def __init__(self, repo: TallerRepository) -> None:
        self._repo = repo

    async def execute(self, command: AutorizarPrecioCommand) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(command.ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {command.ot_id} no encontrada")

        ot.autorizar_precio_cliente()
        await self._repo.actualizar_ot(ot)
        return ot


class RevisionFinalUseCase:
    """EP-TAL-06: POST /v1/ordenes-trabajo/{id}/revision-final → REVISION_FINAL"""

    def __init__(self, repo: TallerRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: RevisionFinalCommand) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(command.ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {command.ot_id} no encontrada")

        # Resolver aprobaciones tácitas expiradas antes de declarar revisión
        for item in TallerService.items_con_espera_expirada(ot):
            item.aprobar_tacitamente()

        ot.declarar_revision_final(command.costo_mano_obra, command.actor_id)
        await self._repo.actualizar_ot(ot)

        repuestos_consumidos = [
            {
                "repuesto_id": i.repuesto_id,
                "codigo": i.codigo,
                "cantidad": i.cantidad,
                "precio_unitario": str(i.precio_unitario),
            }
            for i in ot.repuestos_aprobados()
        ]
        await self._pub.publish(EventEnvelope(
            tipo="orden_trabajo.revision_final",
            modulo_origen="taller",
            payload={
                "orden_trabajo_id": ot.id,
                "repuestos_consumidos": repuestos_consumidos,
                "costo_mano_obra": str(command.costo_mano_obra),
                "mecanico_id": command.actor_id,
            },
        ))
        return ot


class CobroParcialUseCase:
    """EP-TAL-07: POST /v1/ordenes-trabajo/{id}/cobro-parcial"""

    def __init__(self, repo: TallerRepository) -> None:
        self._repo = repo

    async def execute(self, command: CobroParcialCommand) -> dict:
        ot = await self._repo.obtener_ot(command.ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {command.ot_id} no encontrada")
        if ot.estado != EstadoOrdenTrabajo.REVISION_FINAL:
            raise DomainError(
                f"Cobro parcial solo en REVISION_FINAL, estado: {ot.estado.value}"
            )
        monto_total = ot.monto_total_con_mano_obra()
        if monto_total <= Decimal("0"):
            raise DomainError("Monto total de la OT debe ser > 0")
        porcentaje = command.monto_pagado / monto_total
        from decimal import Decimal as D
        if porcentaje < D("0.80"):
            raise DomainError(
                f"Pago mínimo 80% requerido sin aprobación conjunta. "
                f"Pagado: {porcentaje:.1%}, requerido: 80%"
            )
        deuda = monto_total - command.monto_pagado
        ot.confirmar_cobro()
        await self._repo.actualizar_ot(ot)
        return {
            "ot_id": ot.id,
            "monto_total": monto_total,
            "monto_pagado": command.monto_pagado,
            "deuda_activa": deuda,
            "plazo_dias": command.plazo_dias,
        }


class CerrarOrdenTrabajoUseCase:
    """EP-TAL-08: POST /v1/ordenes-trabajo/{id}/cerrar"""

    def __init__(self, repo: TallerRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: CerrarOTCommand) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(command.ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {command.ot_id} no encontrada")

        if not TallerService.verificar_consumo_registrado(ot):
            raise ListaNoConfirmadaError(
                "OT no cierra sin lista de consumo confirmada o costo mano de obra"
            )

        ot.cerrar()
        await self._repo.actualizar_ot(ot)

        historial = HistorialIntervencion(
            vehiculo_id=ot.vehiculo_id,
            orden_trabajo_id=ot.id,
            mecanico_master_id=ot.mecanico_master_id,
            fecha_apertura=ot.created_at,
            fecha_cierre=datetime.now(timezone.utc),
            monto_final=ot.monto_total_con_mano_obra(),
        )
        await self._repo.guardar_historial(historial)

        await self._pub.publish(EventEnvelope(
            tipo="orden_trabajo.cerrada",
            modulo_origen="taller",
            payload={
                "orden_trabajo_id": ot.id,
                "vehiculo_id": ot.vehiculo_id,
                "repuestos_consumidos": [
                    {"repuesto_id": i.repuesto_id, "cantidad": i.cantidad}
                    for i in ot.repuestos_aprobados()
                ],
            },
        ))
        return ot


class CancelarOrdenTrabajoUseCase:
    """EP-TAL-09: POST /v1/ordenes-trabajo/{id}/cancelar"""

    def __init__(self, repo: TallerRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: CancelarOTCommand) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(command.ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {command.ot_id} no encontrada")

        ot.cancelar()
        await self._repo.actualizar_ot(ot)

        await self._pub.publish(EventEnvelope(
            tipo="orden_trabajo.cancelada",
            modulo_origen="taller",
            payload={
                "orden_trabajo_id": ot.id,
                "motivo": command.motivo,
            },
        ))
        return ot


class LiberarVehiculoUseCase:
    """EP-TAL-10: POST /v1/ordenes-trabajo/{id}/liberar-vehiculo"""

    def __init__(self, repo: TallerRepository, event_publisher: EventPublisher) -> None:
        self._repo = repo
        self._pub = event_publisher

    async def execute(self, command: LiberarVehiculoCommand) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(command.ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {command.ot_id} no encontrada")
        if ot.estado != EstadoOrdenTrabajo.CERRADA:
            raise DomainError(
                f"Solo se puede liberar vehículo de OT CERRADA, estado: {ot.estado.value}"
            )

        entrada = await self._repo.obtener_entrada_por_ot(command.ot_id)
        if entrada:
            entrada.cerrar()
            await self._repo.actualizar_entrada(entrada)

        await self._pub.publish(EventEnvelope(
            tipo="vehiculo.liberado",
            modulo_origen="taller",
            payload={
                "orden_trabajo_id": ot.id,
                "vehiculo_id": ot.vehiculo_id,
                "cliente_id": ot.cliente_id or "",
            },
        ))
        return ot


class ConsultarDisponibilidadUseCase:
    """EP-TAL-11: GET /v1/taller/disponibilidad"""

    def __init__(self, repo: TallerRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Mecanico]:
        return await self._repo.listar_mecanicos_disponibles()


class ObtenerOrdenTrabajoUseCase:
    """EP-TAL-12: GET /v1/ordenes-trabajo/{id}"""

    def __init__(self, repo: TallerRepository) -> None:
        self._repo = repo

    async def execute(self, ot_id: str) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {ot_id} no encontrada")
        return ot


class AplicarAprobacionesTacitasUseCase:
    """
    Use case interno: aplica aprobaciones tácitas cuando el timer expira.
    Llamado por job o antes de declarar revisión final.
    """

    def __init__(self, repo: TallerRepository) -> None:
        self._repo = repo

    async def execute(self, ot_id: str) -> OrdenTrabajo:
        ot = await self._repo.obtener_ot(ot_id)
        if ot is None:
            raise OrdenTrabajoNoEncontradaError(f"OT {ot_id} no encontrada")

        for item in TallerService.items_con_espera_expirada(ot):
            item.aprobar_tacitamente()

        await self._repo.actualizar_ot(ot)
        return ot

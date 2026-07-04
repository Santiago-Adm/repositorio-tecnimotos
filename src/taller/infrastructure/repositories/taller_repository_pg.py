"""
Repositorio PostgreSQL para Taller — implementa TallerRepository Protocol.
Patrón idéntico a RepuestoRepositoryPG (catalogo).
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.taller.domain.models.orden_trabajo import (
    EstadoAprobacion,
    EstadoEntrada,
    EstadoOrdenTrabajo,
    Entrada,
    HistorialIntervencion,
    ListaRepuestosOT,
    Mecanico,
    ModalidadIntervencion,
    NivelMecanico,
    NivelUrgencia,
    OrdenTrabajo,
    TramoAdicional,
    Vehiculo,
)
from src.taller.infrastructure.repositories.models.taller_models import (
    EntradaModel,
    HistorialCobroMecanicoModel,
    HistorialIntervencionModel,
    ListaRepuestosOTModel,
    MecanicoModel,
    OrdenTrabajoModel,
    RendicionMecanicoModel,
    VehiculoModel,
)


def _dt(value) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value))


class TallerRepositoryPG:
    """Implementación SQLAlchemy del Protocol TallerRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Vehículos ─────────────────────────────────────────────────────────────

    async def guardar_vehiculo(self, v: Vehiculo) -> Vehiculo:
        self._session.add(VehiculoModel(
            id=v.id,
            universo=v.universo,
            modelo=v.modelo,
            año=v.año,
            placa=v.placa,
            cliente_id=v.cliente_id,
            salud_estimada=v.salud_estimada,
        ))
        await self._session.flush()
        return v

    async def obtener_vehiculo(self, v_id: str) -> Optional[Vehiculo]:
        stmt = select(VehiculoModel).where(VehiculoModel.id == v_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._vehiculo_to_domain(model) if model else None

    # ── Mecánicos ─────────────────────────────────────────────────────────────

    async def guardar_mecanico(self, m: Mecanico) -> Mecanico:
        self._session.add(MecanicoModel(
            id=m.id,
            usuario_id=m.usuario_id,
            nivel=m.nivel.value,
            supervisor_id=m.supervisor_id,
            disponible=m.disponible,
        ))
        await self._session.flush()
        return m

    async def obtener_mecanico(self, m_id: str) -> Optional[Mecanico]:
        stmt = select(MecanicoModel).where(MecanicoModel.id == m_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._mecanico_to_domain(model) if model else None

    async def listar_mecanicos_disponibles(self) -> list[Mecanico]:
        stmt = select(MecanicoModel).where(MecanicoModel.disponible == True)  # noqa: E712
        result = await self._session.execute(stmt)
        return [self._mecanico_to_domain(m) for m in result.scalars().all()]

    async def actualizar_mecanico(self, m: Mecanico) -> Mecanico:
        stmt = select(MecanicoModel).where(MecanicoModel.id == m.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Mecanico {m.id} no encontrado")
        model.disponible = m.disponible
        model.supervisor_id = m.supervisor_id
        await self._session.flush()
        return m

    # ── Órdenes de Trabajo ────────────────────────────────────────────────────

    async def guardar_ot(self, ot: OrdenTrabajo) -> OrdenTrabajo:
        self._session.add(OrdenTrabajoModel(
            id=ot.id,
            vehiculo_id=ot.vehiculo_id,
            mecanico_master_id=ot.mecanico_master_id,
            mecanico_junior_id=ot.mecanico_junior_id,
            cliente_id=ot.cliente_id,
            modalidad=ot.modalidad.value,
            urgencia=ot.urgencia.value,
            estado=ot.estado.value,
            cobro_confirmado=ot.cobro_confirmado,
            visibilidad_precio_cliente=ot.visibilidad_precio_cliente,
            cliente_aprobo_lista=ot.cliente_aprobo_lista,
            costo_mano_obra=ot.costo_mano_obra,
            monto_estimado=ot.monto_estimado,
        ))
        await self._session.flush()  # OT debe existir antes de lista_repuestos_ot (FK)
        for item in ot.lista_repuestos:
            self._session.add(self._lista_item_to_model(item))
        if ot.lista_repuestos:
            await self._session.flush()
        return ot

    async def obtener_ot(self, ot_id: str) -> Optional[OrdenTrabajo]:
        stmt = select(OrdenTrabajoModel).where(OrdenTrabajoModel.id == ot_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        lista = await self._obtener_lista_repuestos(ot_id)
        return self._ot_to_domain(model, lista)

    async def actualizar_ot(self, ot: OrdenTrabajo) -> OrdenTrabajo:
        stmt = select(OrdenTrabajoModel).where(OrdenTrabajoModel.id == ot.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"OT {ot.id} no encontrada")

        model.estado = ot.estado.value
        model.cobro_confirmado = ot.cobro_confirmado
        model.visibilidad_precio_cliente = ot.visibilidad_precio_cliente
        model.cliente_aprobo_lista = ot.cliente_aprobo_lista
        model.costo_mano_obra = ot.costo_mano_obra
        model.monto_estimado = ot.monto_estimado
        model.mecanico_junior_id = ot.mecanico_junior_id
        model.updated_at = datetime.now(timezone.utc)

        existentes = {
            r[0] for r in (await self._session.execute(
                select(ListaRepuestosOTModel.id).where(
                    ListaRepuestosOTModel.orden_trabajo_id == ot.id
                )
            )).all()
        }
        for item in ot.lista_repuestos:
            if item.id not in existentes:
                self._session.add(self._lista_item_to_model(item))
            else:
                # Actualizar aprobación y fechas
                item_stmt = select(ListaRepuestosOTModel).where(
                    ListaRepuestosOTModel.id == item.id
                )
                item_result = await self._session.execute(item_stmt)
                item_model = item_result.scalar_one_or_none()
                if item_model:
                    item_model.aprobacion_cliente = item.aprobacion_cliente.value
                    item_model.aprobado_en = item.aprobado_en
                    item_model.espera_hasta = item.espera_hasta

        await self._session.flush()
        return ot

    async def listar_ots(self) -> list[OrdenTrabajo]:
        stmt = select(OrdenTrabajoModel)
        result = await self._session.execute(stmt)
        ots = []
        for model in result.scalars().all():
            lista = await self._obtener_lista_repuestos(model.id)
            ots.append(self._ot_to_domain(model, lista))
        return ots

    # ── Entradas (registro de ingreso de vehículo) ────────────────────────────

    async def guardar_entrada(self, e: Entrada) -> Entrada:
        self._session.add(EntradaModel(
            id=e.id,
            vehiculo_id=e.vehiculo_id,
            orden_trabajo_id=e.orden_trabajo_id,
            cliente_id=e.cliente_id,
            estado=e.estado.value,
        ))
        await self._session.flush()
        return e

    async def obtener_entrada_por_ot(self, ot_id: str) -> Optional[Entrada]:
        stmt = select(EntradaModel).where(EntradaModel.orden_trabajo_id == ot_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Entrada(
            id=model.id,
            vehiculo_id=model.vehiculo_id,
            orden_trabajo_id=model.orden_trabajo_id,
            cliente_id=model.cliente_id,
            estado=EstadoEntrada(model.estado),
            created_at=_dt(model.created_at),
        )

    async def actualizar_entrada(self, e: Entrada) -> Entrada:
        stmt = select(EntradaModel).where(EntradaModel.id == e.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Entrada {e.id} no encontrada")
        model.estado = e.estado.value
        model.orden_trabajo_id = e.orden_trabajo_id
        await self._session.flush()
        return e

    # ── Historial de intervención ─────────────────────────────────────────────

    async def guardar_historial(self, h: HistorialIntervencion) -> HistorialIntervencion:
        self._session.add(HistorialIntervencionModel(
            id=h.id,
            vehiculo_id=h.vehiculo_id,
            orden_trabajo_id=h.orden_trabajo_id,
            mecanico_master_id=h.mecanico_master_id,
            fecha_apertura=h.fecha_apertura,
            fecha_cierre=h.fecha_cierre,
            monto_final=h.monto_final,
        ))
        await self._session.flush()
        return h

    # ── Historial de negocio (ADR-016) ──────────────────────────────────────────

    async def obtener_mecanico_id_por_usuario(self, usuario_id: str) -> Optional[str]:
        stmt = select(MecanicoModel.id).where(MecanicoModel.usuario_id == usuario_id)
        result = await self._session.execute(stmt)
        row = result.first()
        return row[0] if row else None

    async def tiene_actividad_cliente(self, cliente_id: str) -> bool:
        """True si el cliente tiene vehículo/OT/entrada real — bloquea el DELETE
        físico de usuario (ADR-016)."""
        for model, campo in (
            (VehiculoModel, VehiculoModel.cliente_id),
            (OrdenTrabajoModel, OrdenTrabajoModel.cliente_id),
            (EntradaModel, EntradaModel.cliente_id),
        ):
            stmt = select(model.id).where(campo == cliente_id).limit(1)
            result = await self._session.execute(stmt)
            if result.first() is not None:
                return True
        return False

    async def tiene_actividad_mecanico(self, mecanico_id: str) -> bool:
        """True si el mecánico tiene OT/rendición/historial de cobro real, o es
        supervisor de otro mecánico — bloquea el DELETE físico (ADR-016)."""
        stmt = select(OrdenTrabajoModel.id).where(
            (OrdenTrabajoModel.mecanico_master_id == mecanico_id)
            | (OrdenTrabajoModel.mecanico_junior_id == mecanico_id)
        ).limit(1)
        if (await self._session.execute(stmt)).first() is not None:
            return True
        stmt = select(MecanicoModel.id).where(MecanicoModel.supervisor_id == mecanico_id).limit(1)
        if (await self._session.execute(stmt)).first() is not None:
            return True
        stmt = select(RendicionMecanicoModel.id).where(
            RendicionMecanicoModel.mecanico_id == mecanico_id
        ).limit(1)
        if (await self._session.execute(stmt)).first() is not None:
            return True
        stmt = select(HistorialCobroMecanicoModel.id).where(
            HistorialCobroMecanicoModel.mecanico_master_id == mecanico_id
        ).limit(1)
        if (await self._session.execute(stmt)).first() is not None:
            return True
        return False

    # ── Helpers privados ──────────────────────────────────────────────────────

    async def _obtener_lista_repuestos(self, ot_id: str) -> list[ListaRepuestosOT]:
        stmt = select(ListaRepuestosOTModel).where(
            ListaRepuestosOTModel.orden_trabajo_id == ot_id
        )
        result = await self._session.execute(stmt)
        return [self._lista_item_to_domain(m) for m in result.scalars().all()]

    def _ot_to_domain(
        self, model: OrdenTrabajoModel, lista: list[ListaRepuestosOT]
    ) -> OrdenTrabajo:
        ot = object.__new__(OrdenTrabajo)
        ot.id = model.id
        ot.vehiculo_id = model.vehiculo_id
        ot.mecanico_master_id = model.mecanico_master_id
        ot.mecanico_junior_id = model.mecanico_junior_id
        ot.cliente_id = model.cliente_id
        ot.modalidad = ModalidadIntervencion(model.modalidad)
        ot.urgencia = NivelUrgencia(model.urgencia)
        ot.estado = EstadoOrdenTrabajo(model.estado)
        ot.lista_repuestos = lista
        ot.cobro_confirmado = model.cobro_confirmado
        ot.visibilidad_precio_cliente = model.visibilidad_precio_cliente
        ot.cliente_aprobo_lista = model.cliente_aprobo_lista
        ot.costo_mano_obra = (
            Decimal(str(model.costo_mano_obra)) if model.costo_mano_obra else None
        )
        ot.monto_estimado = (
            Decimal(str(model.monto_estimado)) if model.monto_estimado else Decimal("0")
        )
        ot.created_at = _dt(model.created_at)
        ot.updated_at = _dt(model.updated_at)
        # _TRANSICIONES_VALIDAS es un field con default_factory
        from src.taller.domain.models.orden_trabajo import EstadoOrdenTrabajo as EstadoOT
        ot._TRANSICIONES_VALIDAS = {
            EstadoOT.ABIERTA:        [EstadoOT.LISTA_REPUESTOS, EstadoOT.CANCELADA],
            EstadoOT.LISTA_REPUESTOS: [EstadoOT.EN_EJECUCION, EstadoOT.CANCELADA],
            EstadoOT.EN_EJECUCION:   [EstadoOT.REVISION_FINAL, EstadoOT.CANCELADA],
            EstadoOT.REVISION_FINAL: [EstadoOT.CERRADA, EstadoOT.EN_EJECUCION],
            EstadoOT.CERRADA:        [],
            EstadoOT.CANCELADA:      [],
        }
        return ot

    def _lista_item_to_model(self, item: ListaRepuestosOT) -> ListaRepuestosOTModel:
        return ListaRepuestosOTModel(
            id=item.id,
            orden_trabajo_id=item.orden_trabajo_id,
            repuesto_id=item.repuesto_id,
            codigo=item.codigo,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            momento_agregado=item.momento_agregado,
            tramo_precio=item.tramo_precio.value if item.tramo_precio else None,
            aprobacion_cliente=item.aprobacion_cliente.value,
            aprobado_en=item.aprobado_en,
            espera_hasta=item.espera_hasta,
        )

    def _lista_item_to_domain(self, model: ListaRepuestosOTModel) -> ListaRepuestosOT:
        return ListaRepuestosOT(
            id=model.id,
            orden_trabajo_id=model.orden_trabajo_id,
            repuesto_id=model.repuesto_id,
            codigo=model.codigo,
            cantidad=model.cantidad,
            precio_unitario=Decimal(str(model.precio_unitario)),
            momento_agregado=model.momento_agregado,
            tramo_precio=TramoAdicional(model.tramo_precio) if model.tramo_precio else None,
            aprobacion_cliente=EstadoAprobacion(model.aprobacion_cliente),
            aprobado_en=_dt(model.aprobado_en) if model.aprobado_en else None,
            espera_hasta=_dt(model.espera_hasta) if model.espera_hasta else None,
        )

    def _vehiculo_to_domain(self, model: VehiculoModel) -> Vehiculo:
        return Vehiculo(
            id=model.id,
            universo=model.universo,
            modelo=model.modelo,
            año=model.año,
            placa=model.placa,
            cliente_id=model.cliente_id,
            salud_estimada=model.salud_estimada,
            created_at=_dt(model.created_at),
        )

    def _mecanico_to_domain(self, model: MecanicoModel) -> Mecanico:
        return Mecanico(
            id=model.id,
            usuario_id=model.usuario_id,
            nivel=NivelMecanico(model.nivel),
            supervisor_id=model.supervisor_id,
            disponible=model.disponible,
            created_at=_dt(model.created_at),
        )

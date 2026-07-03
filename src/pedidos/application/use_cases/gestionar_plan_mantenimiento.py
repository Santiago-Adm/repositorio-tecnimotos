"""
Use cases para el módulo de plan de mantenimiento preventivo (02 §5.2).
EP-PED-18: Activar plan de mantenimiento.
EP-PED-19: Cancelar plan de mantenimiento.
Job background: ProcesarRecordatoriosMantenimientoUseCase (sin endpoint propio).
"""
from __future__ import annotations

from dataclasses import dataclass

from src.pedidos.domain.models.pedido import (
    DomainError,
    PlanMantenimiento,
    PlanMantenimientoNoEncontradoError,
    PlanYaActivoError,
)
from src.pedidos.domain.ports.pedido_repository import PedidoRepository


@dataclass
class ActivarPlanMantenimientoCommand:
    cliente_id: str
    vehiculo_id: str


@dataclass
class CancelarPlanMantenimientoCommand:
    plan_id: str
    cliente_id: str  # quien solicita — solo el propietario puede cancelar


class ActivarPlanMantenimientoUseCase:
    """EP-PED-18: POST /v1/pedidos/plan-mantenimiento
    Solo CLIENTE_CONDUCTOR y CLIENTE_RURAL (validado en el endpoint).
    Un cliente solo puede tener un plan ACTIVO por vehículo a la vez."""

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: ActivarPlanMantenimientoCommand) -> PlanMantenimiento:
        existente = await self._repo.obtener_plan_activo_por_cliente(
            cmd.cliente_id, cmd.vehiculo_id
        )
        if existente is not None:
            raise PlanYaActivoError(
                f"Ya existe un plan ACTIVO para el vehículo {cmd.vehiculo_id}"
            )

        plan = PlanMantenimiento(
            cliente_id=cmd.cliente_id,
            vehiculo_id=cmd.vehiculo_id,
        )
        return await self._repo.guardar_plan_mantenimiento(plan)


class CancelarPlanMantenimientoUseCase:
    """EP-PED-19: POST /v1/pedidos/plan-mantenimiento/{id}/cancelar
    Solo el propietario del plan puede cancelarlo."""

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self, cmd: CancelarPlanMantenimientoCommand) -> PlanMantenimiento:
        plan = await self._repo.obtener_plan_mantenimiento(cmd.plan_id)
        if plan is None:
            raise PlanMantenimientoNoEncontradoError(
                f"Plan {cmd.plan_id} no encontrado"
            )
        if plan.cliente_id != cmd.cliente_id:
            raise DomainError("No tienes permiso para cancelar este plan")

        plan.cancelar()
        return await self._repo.actualizar_plan_mantenimiento(plan)


class ProcesarRecordatoriosMantenimientoUseCase:
    """
    Job diario (sin endpoint propio).
    Itera todos los planes ACTIVOS; si el ciclo de 30 días se cumplió,
    marca fecha_ultimo_recordatorio y emite notificación (stub en esta versión).
    Retorna la lista de planes que recibieron recordatorio.
    """

    def __init__(self, repo: PedidoRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[PlanMantenimiento]:
        planes = await self._repo.listar_planes_activos()
        procesados: list[PlanMantenimiento] = []
        for plan in planes:
            if plan.necesita_recordatorio():
                plan.registrar_recordatorio()
                await self._repo.actualizar_plan_mantenimiento(plan)
                procesados.append(plan)
        return procesados

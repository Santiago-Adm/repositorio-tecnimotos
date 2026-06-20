"""
Reglas de negocio puras del módulo taller (02 §2.1).
Sin imports de FastAPI, SQLAlchemy ni Redis.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.taller.domain.models.orden_trabajo import (
    DomainError,
    EstadoAprobacion,
    EstadoOrdenTrabajo,
    ListaRepuestosOT,
    OrdenTrabajo,
    TramoAdicional,
    UMBRAL_APROBACION_AUTOMATICA,
    UMBRAL_APROBACION_TACITA,
)


class TallerService:

    @staticmethod
    def clasificar_tramo_adicional(precio_unitario: Decimal) -> TramoAdicional:
        """Clasifica el tramo de un repuesto adicional según su precio (HU-INT-03)."""
        if precio_unitario < UMBRAL_APROBACION_AUTOMATICA:
            return TramoAdicional.AUTOMATICO
        if precio_unitario <= UMBRAL_APROBACION_TACITA:
            return TramoAdicional.TACITO
        return TramoAdicional.MANUAL

    @staticmethod
    def lista_completamente_aprobada(ot: OrdenTrabajo) -> bool:
        """
        Verifica que todos los ítems de la lista tienen aprobación.
        OT no puede cerrar sin lista completa (HU-INT-04).
        """
        if not ot.lista_repuestos:
            return False
        return all(i.esta_aprobado() for i in ot.lista_repuestos)

    @staticmethod
    def calcular_monto_total(ot: OrdenTrabajo) -> Decimal:
        """Suma subtotales de repuestos + mano de obra."""
        repuestos = sum(i.subtotal for i in ot.lista_repuestos if i.esta_aprobado())
        mo = ot.costo_mano_obra or Decimal("0")
        return repuestos + mo

    @staticmethod
    def puede_avanzar_a_revision(ot: OrdenTrabajo) -> tuple[bool, str]:
        """
        Verifica si la OT puede pasar a REVISION_FINAL.
        Retorna (puede_avanzar, motivo_si_no).
        """
        if ot.estado != EstadoOrdenTrabajo.EN_EJECUCION:
            return False, f"Estado debe ser EN_EJECUCION, actual: {ot.estado.value}"
        if ot.tiene_pendiente_manual():
            return False, "Hay repuestos con aprobación manual pendiente del cliente"
        return True, ""

    @staticmethod
    def items_con_espera_expirada(ot: OrdenTrabajo) -> list[ListaRepuestosOT]:
        """Retorna ítems en espera tácita cuyo timer ya expiró."""
        return [
            i for i in ot.lista_repuestos
            if i.tramo_precio == TramoAdicional.TACITO
            and i.aprobacion_cliente == EstadoAprobacion.PENDIENTE_ADICIONAL
            and i.espera_expirada()
        ]

    @staticmethod
    def verificar_consumo_registrado(ot: OrdenTrabajo) -> bool:
        """
        OT no cierra sin lista de consumo confirmada (criterio 09 §3.4).
        Al menos un ítem aprobado es condición mínima.
        """
        return len(ot.repuestos_aprobados()) > 0 or ot.costo_mano_obra is not None

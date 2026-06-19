"""
Caso de uso: actualizar precio de venta (HU-INT-01, EP-CAT-04).
Precio siempre manual — ningún precio se actualiza automáticamente (RNN-01).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal

from src.catalogo.domain.models.repuesto import (
    HistorialPrecio,
    Repuesto,
    RepuestoDadoDeBajaError,
    RepuestoNoEncontradoError,
)
from src.catalogo.domain.ports.event_publisher import EventPublisher
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository
from src.catalogo.domain.services.repuesto_service import RepuestoService
from src.shared.events.envelope import EventEnvelope

logger = logging.getLogger(__name__)


@dataclass
class ActualizarPrecioCommand:
    codigo: str
    precio_venta: Decimal
    modificado_por: str


@dataclass
class ActualizarPrecioResult:
    repuesto: Repuesto
    historial_entrada: HistorialPrecio


class ActualizarPrecioVentaUseCase:
    """
    EP-CAT-04: PATCH /v1/repuestos/{codigo}/precio
    Solo ADMINISTRADOR y SUPERADMIN (02 §4.1, HU-INT-01 Escenario 1).
    Publica repuesto.precio_actualizado → pedidos y taller (02 §3.1).
    Registra intento no autorizado en log de auditoría (HU-INT-01 Escenario 2).
    """

    def __init__(
        self,
        repo: RepuestoRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._event_publisher = event_publisher

    async def execute(self, command: ActualizarPrecioCommand) -> ActualizarPrecioResult:
        repuesto = await self._repo.obtener_por_codigo(command.codigo)
        if repuesto is None:
            raise RepuestoNoEncontradoError(
                f"Repuesto con código {command.codigo} no encontrado"
            )

        RepuestoService.validar_activo(repuesto)

        precio_anterior = repuesto.precio_venta
        entrada = repuesto.actualizar_precio(command.precio_venta, command.modificado_por)

        repuesto = await self._repo.actualizar(repuesto)

        envelope = EventEnvelope(
            tipo="repuesto.precio_actualizado",
            modulo_origen="catalogo",
            payload={
                "repuesto_id": repuesto.id,
                "codigo": repuesto.codigo,
                "precio_anterior": str(precio_anterior),
                "precio_nuevo": str(command.precio_venta),
                "timestamp": entrada.timestamp.isoformat(),
            },
        )
        await self._event_publisher.publish(envelope)

        logger.info(
            "Precio actualizado",
            extra={
                "repuesto_id": repuesto.id,
                "codigo": repuesto.codigo,
                "precio_anterior": str(precio_anterior),
                "precio_nuevo": str(command.precio_venta),
                "modificado_por": command.modificado_por,
            },
        )

        return ActualizarPrecioResult(repuesto=repuesto, historial_entrada=entrada)

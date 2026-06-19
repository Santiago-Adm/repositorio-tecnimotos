"""
Caso de uso: dar de baja un repuesto (EP-CAT-05).
Baja lógica únicamente — NUNCA eliminación física (02 §3.1).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from src.catalogo.domain.models.repuesto import (
    Repuesto,
    RepuestoNoEncontradoError,
)
from src.catalogo.domain.ports.event_publisher import EventPublisher
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository
from src.catalogo.domain.services.repuesto_service import RepuestoService
from src.shared.events.envelope import EventEnvelope

logger = logging.getLogger(__name__)


@dataclass
class DarDeBajaRepuestoCommand:
    codigo: str
    motivo: str
    dado_de_baja_por: str


class DarDeBajaRepuestoUseCase:
    """
    EP-CAT-05: DELETE /v1/repuestos/{codigo}
    Baja lógica — activo=False · eliminado_en registrado.
    Publica repuesto.dado_de_baja → pedidos, stock, taller (02 §3.1).
    """

    def __init__(
        self,
        repo: RepuestoRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._event_publisher = event_publisher

    async def execute(self, command: DarDeBajaRepuestoCommand) -> Repuesto:
        repuesto = await self._repo.obtener_por_codigo(command.codigo)
        if repuesto is None:
            raise RepuestoNoEncontradoError(
                f"Repuesto con código {command.codigo} no encontrado"
            )

        RepuestoService.verificar_puede_dar_de_baja(repuesto)

        repuesto.dar_de_baja(command.motivo)
        repuesto = await self._repo.actualizar(repuesto)

        envelope = EventEnvelope(
            tipo="repuesto.dado_de_baja",
            modulo_origen="catalogo",
            payload={
                "repuesto_id": repuesto.id,
                "codigo": repuesto.codigo,
                "motivo": command.motivo,
            },
        )
        await self._event_publisher.publish(envelope)

        logger.info(
            "Repuesto dado de baja",
            extra={
                "repuesto_id": repuesto.id,
                "codigo": repuesto.codigo,
                "motivo": command.motivo,
                "dado_de_baja_por": command.dado_de_baja_por,
            },
        )

        return repuesto

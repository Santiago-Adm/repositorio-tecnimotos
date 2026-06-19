"""
Caso de uso: crear repuesto (HU-INT-01 parcial, EP-CAT-03).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    UniversoRepuesto,
)
from src.catalogo.domain.ports.event_publisher import EventPublisher
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository
from src.shared.events.envelope import EventEnvelope

logger = logging.getLogger(__name__)


@dataclass
class CrearRepuestoCommand:
    codigo: str
    nombre: str
    universo: UniversoRepuesto
    modelo: str
    año: int
    categoria: CategoriaRepuesto
    precio_venta: Decimal
    descripcion: str = ""
    creado_por: str = ""


class CrearRepuestoUseCase:
    """
    EP-CAT-03: POST /v1/repuestos — solo ADMINISTRADOR y SUPERADMIN.
    Publica repuesto.creado → stock inicializa registro en cero (02 §3.1).
    """

    def __init__(
        self,
        repo: RepuestoRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._repo = repo
        self._event_publisher = event_publisher

    async def execute(self, command: CrearRepuestoCommand) -> Repuesto:
        repuesto = Repuesto(
            codigo=command.codigo,
            nombre=command.nombre,
            universo=command.universo,
            modelo=command.modelo,
            año=command.año,
            categoria=command.categoria,
            precio_venta=command.precio_venta,
            descripcion=command.descripcion,
        )

        repuesto = await self._repo.guardar(repuesto)

        envelope = EventEnvelope(
            tipo="repuesto.creado",
            modulo_origen="catalogo",
            payload={
                "repuesto_id": repuesto.id,
                "codigo": repuesto.codigo,
                "universo": repuesto.universo.value,
                "modelo": repuesto.modelo,
                "año": repuesto.año,
                "categoria": repuesto.categoria.value,
            },
        )
        await self._event_publisher.publish(envelope)

        logger.info(
            "Repuesto creado",
            extra={
                "repuesto_id": repuesto.id,
                "codigo": repuesto.codigo,
                "creado_por": command.creado_por,
            },
        )

        return repuesto

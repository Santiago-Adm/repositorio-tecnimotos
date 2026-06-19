"""
EventBus sobre Redis Streams con garantías at-least-once (03 §7.8).
El worker outbox publica eventos persistidos en outbox_events (03 §11).
"""
from __future__ import annotations

import json
import logging
from typing import Any

from src.shared.events.envelope import EventEnvelope

logger = logging.getLogger(__name__)

CONSUMER_GROUPS = {
    "catalogo-group": "catalogo",
    "pedidos-group": "pedidos",
    "stock-group": "stock",
    "taller-group": "taller",
    "notif-group": "notification-service",
}

TOPICO_SUBSCRIPTIONS: dict[str, list[str]] = {
    "catalogo-group": [
        "stock.agotado",
        "stock.disponible",
        "reabastecimiento.recibido",
        "reabastecimiento.precio_actualizado",
    ],
    "pedidos-group": [
        "stock.disponible",
        "reabastecimiento.recibido",
        "reserva.creada",
        "orden_trabajo.lista_aprobada",
        "orden_trabajo.repuesto_agregado",
        "orden_trabajo.revision_final",
        "orden_trabajo.cancelada",
        "vehiculo.liberado",
    ],
    "stock-group": [
        "reserva.creada",
        "reserva.liberada",
        "reserva.prioridad_taller",
        "pedido.confirmado",
        "pedido.cancelado",
        "orden_trabajo.cerrada",
        "orden_trabajo.cancelada",
        "repuesto.creado",
        "repuesto.dado_de_baja",
    ],
    "taller-group": [
        "cobro.confirmado",
        "stock.consumo_registrado",
    ],
    "notif-group": [
        "margen.alerta",
        "stock.bajo_umbral",
        "comprobante.pendiente_validacion",
    ],
}


class EventBus:
    """Bus de eventos sobre Redis Streams."""

    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client
        self._initialized = False

    async def initialize(self) -> None:
        """Crea los 5 consumer groups en Redis Streams (03 §7.6)."""
        if self._initialized:
            return
        for group, module in CONSUMER_GROUPS.items():
            topicos = TOPICO_SUBSCRIPTIONS.get(group, [])
            for topico in topicos:
                try:
                    await self._redis.xgroup_create(
                        topico, group, id="0", mkstream=True
                    )
                    logger.info(
                        "Consumer group creado",
                        extra={"group": group, "topico": topico},
                    )
                except Exception as exc:
                    if "BUSYGROUP" in str(exc):
                        pass  # ya existe
                    else:
                        logger.warning(
                            "Error creando consumer group",
                            extra={"group": group, "topico": topico, "error": str(exc)},
                        )
        self._initialized = True

    async def publish(self, envelope: EventEnvelope) -> str:
        """Publica un evento en el stream del tópico."""
        data = json.dumps(envelope.to_dict(), default=str)
        msg_id = await self._redis.xadd(envelope.tipo, {"data": data})
        logger.info(
            "Evento publicado",
            extra={"tipo": envelope.tipo, "evento_id": envelope.evento_id, "msg_id": msg_id},
        )
        return msg_id


class InMemoryEventBus:
    """EventBus en memoria para pruebas unitarias."""

    def __init__(self) -> None:
        self._published: list[EventEnvelope] = []

    async def initialize(self) -> None:
        pass

    async def publish(self, envelope: EventEnvelope) -> str:
        self._published.append(envelope)
        return f"inmemory-{len(self._published)}"

    def get_published(self) -> list[EventEnvelope]:
        return list(self._published)

    def clear(self) -> None:
        self._published.clear()

    def fue_publicado(self, tipo: str) -> bool:
        return any(e.tipo == tipo for e in self._published)

    def conteo_publicaciones(self, tipo: str) -> int:
        return sum(1 for e in self._published if e.tipo == tipo)

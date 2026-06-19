"""Puerto para publicación de eventos de dominio del módulo catalogo."""
from typing import Any, Protocol

from src.shared.events.envelope import EventEnvelope


class EventPublisher(Protocol):
    async def publish(self, envelope: EventEnvelope) -> str: ...

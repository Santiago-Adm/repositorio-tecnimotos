"""EventPublisher port — mismo contrato que el bus compartido (04 §4.1)."""
from __future__ import annotations

from typing import Protocol

from src.shared.events.envelope import EventEnvelope


class EventPublisher(Protocol):
    async def publish(self, envelope: EventEnvelope) -> str: ...

"""Envelope obligatorio para todos los eventos (03 §7.1)."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EventEnvelope:
    tipo: str
    modulo_origen: str
    payload: dict[str, Any]
    version: str = "1.0.0"
    evento_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "evento_id": self.evento_id,
            "tipo": self.tipo,
            "timestamp": self.timestamp.isoformat(),
            "modulo_origen": self.modulo_origen,
            "version": self.version,
            "payload": self.payload,
        }

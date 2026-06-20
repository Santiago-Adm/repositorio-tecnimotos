"""
NotificacionPort — adaptador de salida hexagonal (03 §9.1).
Implementado por WhatsAppAdapter (primario) y SMSAdapter (fallback).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ComandoNotificacion:
    destinatario_id: str
    canal: str
    tipo: str
    payload: dict


@dataclass
class ResultadoNotificacion:
    enviado: bool
    canal_usado: str
    mensaje_id: str = ""
    fallback_activado: bool = False


class NotificacionPort(Protocol):
    async def enviar_notificacion(
        self, comando: ComandoNotificacion
    ) -> ResultadoNotificacion: ...

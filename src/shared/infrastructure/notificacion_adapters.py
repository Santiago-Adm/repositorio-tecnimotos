"""
Adaptadores de NotificacionPort (03 §9.1).
WhatsAppAdapter (primario) · SMSAdapter (fallback) · InMemoryNotificacionAdapter (tests).
"""
from __future__ import annotations

from src.shared.domain.notificacion_port import (
    ComandoNotificacion,
    ResultadoNotificacion,
)


class WhatsAppAdapter:
    """
    Implementación primaria de NotificacionPort sobre WhatsApp Business API.
    En tests de contrato LSP: usa stub que retorna éxito sin llamada real.
    """

    def __init__(self, api_token: str = "stub") -> None:
        self._token = api_token

    async def enviar_notificacion(
        self, comando: ComandoNotificacion
    ) -> ResultadoNotificacion:
        return ResultadoNotificacion(
            enviado=True,
            canal_usado="whatsapp",
            mensaje_id=f"wa-stub-{comando.destinatario_id}",
        )


class SMSAdapter:
    """
    Implementación fallback de NotificacionPort sobre SMS (Twilio/AWS SNS).
    En tests de contrato LSP: stub sin llamada real.
    """

    def __init__(self, api_key: str = "stub") -> None:
        self._key = api_key

    async def enviar_notificacion(
        self, comando: ComandoNotificacion
    ) -> ResultadoNotificacion:
        return ResultadoNotificacion(
            enviado=True,
            canal_usado="sms",
            mensaje_id=f"sms-stub-{comando.destinatario_id}",
        )


class InMemoryNotificacionAdapter:
    """
    Fake de NotificacionPort para tests de contrato LSP (04 §6.2).
    Registra notificaciones sin enviarlas.
    """

    def __init__(self) -> None:
        self._enviadas: list[ComandoNotificacion] = []

    async def enviar_notificacion(
        self, comando: ComandoNotificacion
    ) -> ResultadoNotificacion:
        self._enviadas.append(comando)
        return ResultadoNotificacion(
            enviado=True,
            canal_usado="inmemory",
            mensaje_id=f"inmem-{len(self._enviadas)}",
        )

    def get_enviadas(self) -> list[ComandoNotificacion]:
        return list(self._enviadas)

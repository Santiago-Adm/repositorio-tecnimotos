"""
Envío de correo transaccional — Resend HTTP API (ADR-011 MFA por correo).
Railway no ofrece SMTP propio; Resend evita gestionar TLS/25/587 a mano.
Credenciales siempre en variables de entorno (R23) — nunca hardcodeadas.
"""
from __future__ import annotations

import logging

import httpx

from src.shared.infrastructure.settings import get_settings

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    pass


async def enviar_correo(destinatario: str, asunto: str, cuerpo_texto: str) -> None:
    """
    Envía un correo transaccional. Si RESEND_API_KEY no está configurada
    (dev/test sin credenciales), registra un log y no falla — mismo patrón
    de degradación que R2ImagenStorage/InMemoryImagenStorage.
    Nunca loguea el cuerpo del correo (puede contener el código MFA).
    """
    settings = get_settings()
    destinatario_parcial = destinatario[:3] + "***"

    if not settings.resend_api_key:
        # PIEZA D (sesión 2026-07-03): visibilidad del código MFA en desarrollo.
        # Condición estricta == "development" (no "not production") — si
        # ENVIRONMENT tiene cualquier otro valor (incluido vacío, mal escrito,
        # o "production"), esta rama NUNCA loguea el código. Fail-safe: el
        # valor por defecto de settings.environment es "development" (ver
        # settings.py), así que un ENVIRONMENT ausente en un despliegue real
        # sigue siendo un error de configuración a corregir — no una vía para
        # exponer códigos por accidente, porque Railway/producción real deben
        # declarar ENVIRONMENT=production explícitamente en sus variables.
        if settings.environment == "development":
            logger.warning(
                "email_sender: SOLO DESARROLLO — NUNCA EN PRODUCCIÓN — "
                "RESEND_API_KEY no configurada, código MFA visible solo aquí: %s",
                cuerpo_texto,
                extra={"destinatario_parcial": destinatario_parcial, "asunto": asunto},
            )
        else:
            logger.warning(
                "email_sender: RESEND_API_KEY no configurada — correo no enviado",
                extra={"destinatario_parcial": destinatario_parcial, "asunto": asunto},
            )
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.mfa_email_from,
                "to": [destinatario],
                "subject": asunto,
                "text": cuerpo_texto,
            },
        )

    if response.status_code >= 400:
        logger.error(
            "email_sender: fallo al enviar correo",
            extra={
                "destinatario_parcial": destinatario_parcial,
                "status_code": response.status_code,
            },
        )
        raise EmailSendError(f"Resend respondió {response.status_code}: {response.text[:200]}")

    logger.info(
        "email_sender: correo enviado",
        extra={"destinatario_parcial": destinatario_parcial, "asunto": asunto},
    )

"""Registro de auditoría de intentos MFA (R29) — ADR-011."""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def registrar_intento_mfa(
    db: AsyncSession | None, usuario_id: str, resultado: str, ip: str | None
) -> None:
    """
    Inserta una fila de auditoría en mfa_intento si hay sesión de BD disponible.
    Sin BD (tests / InMemory puro): degrada a un log estructurado — nunca
    rompe el flujo de login por un fallo de auditoría.
    """
    if db is None:
        logger.info(
            "mfa_auditoria: sin BD — degradando a log",
            extra={"usuario_id": usuario_id, "resultado": resultado},
        )
        return
    try:
        await db.execute(
            text(
                "INSERT INTO mfa_intento (id, usuario_id, resultado, ip) "
                "VALUES (:id, :usuario_id, :resultado, :ip)"
            ),
            {
                "id": str(uuid.uuid4()),
                "usuario_id": usuario_id,
                "resultado": resultado,
                "ip": ip,
            },
        )
    except Exception:
        logger.exception(
            "mfa_auditoria: fallo al insertar intento — no bloquea el login",
            extra={"usuario_id": usuario_id, "resultado": resultado},
        )

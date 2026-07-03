"""Auditoría de intentos MFA (R29) — ADR-011. Sin FK a usuario: el store de
auth es InMemory hoy (usuario_id no vive en la tabla usuario de PostgreSQL
todavía) — ver ADR-011 sección "Limitación conocida".
usuario_id es String, no UUID: el store InMemory usa literales no-UUID para
cuentas semilla (ej. "user-admin-seed"), no solo uuid4."""
from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class MfaIntentoModel(Base):
    __tablename__ = "mfa_intento"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id: Mapped[str] = mapped_column(String(100), nullable=False)
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    creado_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "resultado IN ('EXITOSO','CODIGO_INCORRECTO','EXPIRADO','BLOQUEADO','TOKEN_INVALIDO')",
            name="chk_mfa_intento_resultado",
        ),
        Index("idx_mfa_intento_usuario", "usuario_id"),
        Index("idx_mfa_intento_creado", "creado_en"),
    )

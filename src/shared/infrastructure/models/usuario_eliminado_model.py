"""Auditoría append-only de eliminaciones físicas de usuario (R29) — ADR-016.
Sin FK a usuario.id: el registro debe sobrevivir al DELETE que audita
(mismo patrón que mfa_intento, ADR-011). eliminado_por sí tiene FK — quien
elimina sigue existiendo."""
from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class UsuarioEliminadoModel(Base):
    __tablename__ = "usuario_eliminado"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id_original: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    eliminado_por: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id"), nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    eliminado_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_usuario_eliminado_original", "usuario_id_original"),
        Index("idx_usuario_eliminado_en", "eliminado_en"),
    )

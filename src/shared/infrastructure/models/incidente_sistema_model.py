"""Modelo SQLAlchemy — incidente_sistema (ADR-019)."""
from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class IncidenteSistemaModel(Base):
    __tablename__ = "incidente_sistema"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ABIERTO")
    reportado_por: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id"), nullable=False)
    resuelto_por: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id"), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resuelto_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("severidad IN ('BAJA','MEDIA','ALTA','CRITICA')", name="chk_incidente_severidad"),
        CheckConstraint("estado IN ('ABIERTO','RESUELTO')", name="chk_incidente_estado"),
        Index("idx_incidente_estado", "estado"),
        Index("idx_incidente_created_at", "created_at"),
    )

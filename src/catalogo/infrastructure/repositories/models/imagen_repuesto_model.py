"""
Modelo SQLAlchemy para imagen_repuesto — galería de imágenes por repuesto.
Formalizada en ADR-012 (revierte ADR-010, campo único imagen_url).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class ImagenRepuestoModel(Base):
    __tablename__ = "imagen_repuesto"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    repuesto_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("repuesto.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    subido_por: Mapped[str] = mapped_column(String(100), nullable=False)
    subido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("repuesto_id", "orden", name="uq_imagen_repuesto_orden"),
        Index("idx_imagen_repuesto_repuesto_id", "repuesto_id"),
    )

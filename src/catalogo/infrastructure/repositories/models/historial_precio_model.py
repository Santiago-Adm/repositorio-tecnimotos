"""
Modelo SQLAlchemy para historial_precio_repuesto (03 §5.2).
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class HistorialPrecioModel(Base):
    __tablename__ = "historial_precio_repuesto"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    repuesto_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("repuesto.id", ondelete="CASCADE"),
        nullable=False,
    )
    precio_anterior: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    precio_nuevo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    modificado_por: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_historial_precio", "repuesto_id", "created_at"),
    )

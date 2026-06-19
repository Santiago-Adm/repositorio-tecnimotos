"""
Modelo SQLAlchemy para la tabla repuesto (03 §5.2).
UUID v4 como PK · TIMESTAMPTZ en created_at/updated_at · snake_case singular.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class RepuestoModel(Base):
    __tablename__ = "repuesto"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    universo: Mapped[str] = mapped_column(String(20), nullable=False)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    año: Mapped[int] = mapped_column(nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    precio_costo: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # cifrado Fernet (03 §5.7)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    eliminado_en: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "universo IN ('mototaxi', 'motolineal')",
            name="chk_repuesto_universo",
        ),
        CheckConstraint(
            "año BETWEEN 1990 AND 2100",
            name="chk_repuesto_año",
        ),
        CheckConstraint(
            "precio_venta > 0",
            name="chk_repuesto_precio_venta",
        ),
        Index("idx_repuesto_busqueda", "universo", "modelo", "año", "codigo"),
        Index("idx_repuesto_activo", "activo", "universo"),
    )

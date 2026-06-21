"""Modelos SQLAlchemy compartidos: parametros_sistema, outbox_events (03 §5.6)."""
from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class ParametrosSistemaModel(Base):
    __tablename__ = "parametros_sistema"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    clave: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    modulo: Mapped[str] = mapped_column(String(30), nullable=False)
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_valor: Mapped[str] = mapped_column(String(20), nullable=False)
    valor_defecto: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False, default="")
    modificable_por: Mapped[str] = mapped_column(String(30), nullable=False, default="ADMINISTRADOR")
    modificado_por: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id"), nullable=True)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "modulo IN ('catalogo','pedidos','stock','taller','shared')",
            name="chk_params_modulo",
        ),
        CheckConstraint(
            "tipo_valor IN ('int','float','str','bool')",
            name="chk_params_tipo_valor",
        ),
        CheckConstraint(
            "modificable_por IN ('ADMINISTRADOR','SUPERADMIN')",
            name="chk_params_modificable_por",
        ),
        Index("idx_params_modulo", "modulo"),
        Index("idx_params_clave", "clave"),
    )


class OutboxEventsModel(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tipo_evento: Mapped[str] = mapped_column(String(100), nullable=False)
    modulo_origen: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ultimo_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "modulo_origen IN ('catalogo','pedidos','stock','taller')",
            name="chk_outbox_modulo",
        ),
        CheckConstraint(
            "estado IN ('PENDIENTE','PROCESADO','FALLIDO')",
            name="chk_outbox_estado",
        ),
        CheckConstraint("intentos >= 0", name="chk_outbox_intentos"),
        Index("idx_outbox_pendiente", "estado", "created_at"),
        Index("idx_outbox_fallido", "estado", "intentos"),
        Index("idx_outbox_tipo", "tipo_evento"),
    )


class EventosProcesadosModel(Base):
    """Tabla de idempotencia para eventos consumidos — una instancia por módulo consumidor (03 §5.8)."""
    __tablename__ = "eventos_procesados"

    evento_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(100), nullable=False)
    modulo_origen: Mapped[str] = mapped_column(String(20), nullable=False)
    modulo_consumidor: Mapped[str] = mapped_column(String(20), nullable=False)
    procesado_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        CheckConstraint("resultado IN ('EXITOSO','IGNORADO')", name="chk_eventos_proc_resultado"),
        Index("idx_eventos_proc_consumidor", "modulo_consumidor", "procesado_en"),
    )

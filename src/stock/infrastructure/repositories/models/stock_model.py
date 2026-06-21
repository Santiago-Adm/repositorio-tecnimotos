"""SQLAlchemy models para el módulo stock (03 §5.3)."""
from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class StockRepuestoModel(Base):
    __tablename__ = "stock_repuesto"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    repuesto_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("repuesto.id"), unique=True, nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad_disponible: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_apartada: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_en_transito: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    umbral_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("cantidad_disponible >= 0", name="chk_disponible_no_negativo"),
        CheckConstraint("cantidad_apartada >= 0", name="chk_apartado_no_negativo"),
        CheckConstraint("cantidad_disponible + cantidad_apartada >= 0", name="chk_stock_coherente"),
        Index("idx_stock_disponible", "repuesto_id", "cantidad_disponible"),
    )


class MovimientoStockModel(Base):
    __tablename__ = "movimiento_stock"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    repuesto_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("stock_repuesto.repuesto_id"), nullable=False)
    tipo_movimiento: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    estado_origen: Mapped[str] = mapped_column(String(50), nullable=False)
    estado_destino: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    referencia_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    timestamp: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="chk_movimiento_cantidad_positiva"),
        CheckConstraint(
            "tipo_movimiento IN ('ENTRADA_REABASTECIMIENTO','SALIDA_VENTA','SALIDA_TALLER',"
            "'AJUSTE_MANUAL','RESERVA','LIBERACION_RESERVA')",
            name="chk_tipo_movimiento",
        ),
        Index("idx_movimiento_repuesto", "repuesto_id"),
        Index("idx_movimiento_referencia", "referencia_id"),
        Index("idx_movimiento_actor", "actor_id"),
    )


class ReabastecimientoModel(Base):
    __tablename__ = "reabastecimiento"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    proveedor: Mapped[str] = mapped_column(String(200), nullable=False)
    solicitado_por: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="SOLICITADO")
    notas: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "estado IN ('SOLICITADO','CONFIRMADO_PROVEEDOR','EN_TRANSITO','RECIBIDO','CANCELADO')",
            name="chk_reabastecimiento_estado",
        ),
        Index("idx_reabastecimiento_estado", "estado", "created_at"),
    )


class ReabastecimientoItemModel(Base):
    __tablename__ = "reabastecimiento_item"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    reabastecimiento_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("reabastecimiento.id", ondelete="CASCADE"), nullable=False)
    repuesto_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("repuesto.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad_solicitada: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_recibida: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    precio_costo_unitario: Mapped[str] = mapped_column(String(500), nullable=False)  # cifrado Fernet (03 §5.7)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("cantidad_solicitada > 0", name="chk_reab_item_cantidad"),
        Index("idx_reab_item_repuesto", "repuesto_id", "created_at"),
    )


class NotificacionStockClienteModel(Base):
    __tablename__ = "notificacion_stock_cliente"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    repuesto_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("repuesto.id"), nullable=False)
    cliente_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDIENTE")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("estado IN ('PENDIENTE','ENVIADA','CANCELADA')", name="chk_notif_stock_estado"),
        Index("idx_notif_stock", "repuesto_id", "estado"),
    )

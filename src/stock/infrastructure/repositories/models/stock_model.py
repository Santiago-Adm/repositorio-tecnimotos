"""SQLAlchemy models para el módulo stock (03 §5.3)."""
from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class StockRepuestoModel(Base):
    __tablename__ = "stock_repuesto"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    repuesto_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad_disponible: Mapped[int] = mapped_column(Integer, default=0)
    cantidad_apartada: Mapped[int] = mapped_column(Integer, default=0)
    cantidad_en_transito: Mapped[int] = mapped_column(Integer, default=0)
    umbral_minimo: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        CheckConstraint("cantidad_disponible >= 0", name="chk_disponible_no_negativo"),
        CheckConstraint("cantidad_apartada >= 0", name="chk_apartado_no_negativo"),
        CheckConstraint(
            "cantidad_disponible + cantidad_apartada >= 0",
            name="chk_stock_coherente",
        ),
        Index("idx_stock_disponible", "repuesto_id", "cantidad_disponible"),
    )


class MovimientoStockModel(Base):
    __tablename__ = "movimiento_stock"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    repuesto_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stock_repuesto.repuesto_id"), nullable=False
    )
    tipo_movimiento: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    estado_origen: Mapped[str] = mapped_column(String(50))
    estado_destino: Mapped[str] = mapped_column(String(50))
    actor_id: Mapped[str] = mapped_column(String(36))
    referencia_id: Mapped[str] = mapped_column(String(100), default="")
    timestamp: Mapped[str] = mapped_column(String(50))

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

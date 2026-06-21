"""Modelos SQLAlchemy para el módulo pedidos (03 §5.4)."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class ClienteModel(Base):
    __tablename__ = "cliente"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False)
    segmento: Mapped[str] = mapped_column(String(30), nullable=False)
    sub_rol: Mapped[str | None] = mapped_column(String(30), nullable=True)
    canal_preferido: Mapped[str] = mapped_column(String(20), nullable=False, default="presencial")
    mecanico_preferido_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    nivel_visibilidad: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("nivel_visibilidad IN (0,1,2)", name="chk_cliente_visibilidad"),
        Index("idx_cliente_usuario", "usuario_id"),
        Index("idx_cliente_segmento", "segmento"),
    )


class PedidoModel(Base):
    __tablename__ = "pedido"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("cliente.id"), nullable=True)
    canal_origen: Mapped[str] = mapped_column(String(50), nullable=False)
    origen_actor: Mapped[str] = mapped_column(String(30), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR")
    monto_total: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    descuento_aplicado: Mapped[str | None] = mapped_column(Text, nullable=True)  # cifrado Fernet (03 §5.7)
    precio_ajustado: Mapped[object | None] = mapped_column(Numeric(12, 2), nullable=True)
    motivo_cancelacion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    orden_trabajo_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "estado IN ('BORRADOR','CONFIRMADO','EN_PREPARACION','DESPACHADO','ENTREGADO','INCIDENCIA','CANCELADO')",
            name="chk_pedido_estado",
        ),
        CheckConstraint("monto_total >= 0", name="chk_pedido_monto"),
        Index("idx_pedido_cliente", "cliente_id"),
        Index("idx_pedido_estado", "estado"),
        Index("idx_pedido_orden_trabajo", "orden_trabajo_id"),
        Index("idx_pedido_origen_actor", "origen_actor"),
    )


class PedidoItemModel(Base):
    __tablename__ = "pedido_item"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    pedido_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False)
    repuesto_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("repuesto.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)
    precio_ajustado_unit: Mapped[object | None] = mapped_column(Numeric(12, 2), nullable=True)

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="chk_pedido_item_cantidad"),
        CheckConstraint("precio_unitario > 0", name="chk_pedido_item_precio"),
        Index("idx_pedido_item_pedido", "pedido_id"),
    )


class ReservaModel(Base):
    __tablename__ = "reserva"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("cliente.id"), nullable=False)
    repuesto_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("repuesto.id"), nullable=False)
    pedido_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("pedido.id"), nullable=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    segmento: Mapped[str] = mapped_column(String(30), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVA")
    expira_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    pago_registrado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notificaciones_enviadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "estado IN ('ACTIVA','CONFIRMADA','EXPIRADA','LIBERADA')",
            name="chk_reserva_estado",
        ),
        CheckConstraint("notificaciones_enviadas >= 0", name="chk_reserva_notif"),
        Index("idx_reserva_cliente", "cliente_id"),
        Index("idx_reserva_repuesto", "repuesto_id"),
        Index("idx_reserva_expiracion", "expira_en", "estado"),
    )


class ListaReservaProgresivaModel(Base):
    __tablename__ = "lista_reserva_progresiva"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    cliente_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("cliente.id"), nullable=False)
    nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR")
    ultima_actividad: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("estado IN ('BORRADOR','CONFIRMADA','FORMALIZADA')", name="chk_lista_reserva_estado"),
        Index("idx_lista_cliente", "cliente_id"),
        Index("idx_lista_actividad", "ultima_actividad"),
    )


class ListaReservaProgresivaItemModel(Base):
    __tablename__ = "lista_reserva_progresiva_item"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    lista_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("lista_reserva_progresiva.id", ondelete="CASCADE"), nullable=False)
    repuesto_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("repuesto.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_referencia: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="chk_lista_item_cantidad"),
        Index("idx_lista_item_lista", "lista_id"),
    )


class ProformaModel(Base):
    __tablename__ = "proforma"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    pedido_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False)
    numero_referencia: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="BORRADOR")
    monto_total: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "estado IN ('BORRADOR','ENVIADA','ACEPTADA','RECHAZADA','VENCIDA')",
            name="chk_proforma_estado",
        ),
        CheckConstraint("monto_total > 0", name="chk_proforma_monto"),
        Index("idx_proforma_pedido", "pedido_id"),
        Index("idx_proforma_numero", "numero_referencia"),
    )


class EnvioModel(Base):
    __tablename__ = "envio"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    pedido_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("pedido.id", ondelete="CASCADE"), unique=True, nullable=False)
    empresa_encomienda: Mapped[str] = mapped_column(String(100), nullable=False)
    direccion_destino: Mapped[str] = mapped_column(Text, nullable=False)  # cifrado Fernet (03 §5.7)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PREPARADO")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "estado IN ('PREPARADO','ENTREGADO_AGENCIA','EN_TRANSITO','ENTREGADO_CLIENTE','INCIDENCIA','RESUELTO')",
            name="chk_envio_estado",
        ),
        Index("idx_envio_pedido", "pedido_id"),
        Index("idx_envio_estado", "estado"),
    )


class ComprobanteModel(Base):
    __tablename__ = "comprobante"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    pedido_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("pedido.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDIENTE_VALIDACION")
    monto: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)
    emitido_por: Mapped[str] = mapped_column(String(100), nullable=False)
    ruc_cliente: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nota_credito_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("comprobante.id"), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("tipo IN ('boleta','factura','ticket')", name="chk_comprobante_tipo"),
        CheckConstraint(
            "estado IN ('PENDIENTE_VALIDACION','EMITIDO','ENVIADO_CLIENTE','ANULADO')",
            name="chk_comprobante_estado",
        ),
        CheckConstraint("monto > 0", name="chk_comprobante_monto"),
        Index("idx_comprobante_pedido", "pedido_id"),
        Index("idx_comprobante_estado", "estado"),
    )


class DeudaActivaModel(Base):
    __tablename__ = "deuda_activa"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    pedido_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("pedido.id"), unique=True, nullable=False)
    cliente_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("cliente.id"), nullable=False)
    monto_deuda: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)
    plazo_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    alerta_50_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    alerta_vencimiento_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    vence_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("monto_deuda > 0", name="chk_deuda_monto"),
        CheckConstraint("plazo_dias > 0", name="chk_deuda_plazo"),
        Index("idx_deuda_cliente", "cliente_id"),
        Index("idx_deuda_alerta_50", "alerta_50_en"),
        Index("idx_deuda_alerta_venc", "alerta_vencimiento_en"),
    )

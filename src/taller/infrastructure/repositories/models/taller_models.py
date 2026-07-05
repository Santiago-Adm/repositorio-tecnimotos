"""Modelos SQLAlchemy para el módulo taller (03 §5.5)."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class VehiculoModel(Base):
    __tablename__ = "vehiculo"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    universo: Mapped[str] = mapped_column(String(20), nullable=False)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    año: Mapped[int] = mapped_column(Integer, nullable=False)
    placa: Mapped[str | None] = mapped_column(Text, nullable=True)            # cifrado Fernet (03 §5.7)
    tarjeta_propiedad: Mapped[str | None] = mapped_column(Text, nullable=True) # cifrado Fernet
    cliente_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("cliente.id"), nullable=True)
    salud_estimada: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("año BETWEEN 1990 AND 2100", name="chk_vehiculo_año"),
        CheckConstraint("salud_estimada BETWEEN 0 AND 100", name="chk_vehiculo_salud"),
        Index("idx_vehiculo_cliente", "cliente_id"),
        Index("idx_vehiculo_modelo", "universo", "modelo", "año"),
    )


class MecanicoModel(Base):
    __tablename__ = "mecanico"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False)
    nivel: Mapped[str] = mapped_column(String(10), nullable=False)
    supervisor_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("mecanico.id"), nullable=True)
    disponible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("nivel IN ('MASTER','JUNIOR')", name="chk_mecanico_nivel"),
        Index("idx_mecanico_disponible", "disponible", "nivel"),
        Index("idx_mecanico_supervisor", "supervisor_id"),
    )


class MecanicoPerfilModel(Base):
    __tablename__ = "mecanico_perfil"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    mecanico_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("mecanico.id", ondelete="CASCADE"), unique=True, nullable=False)
    dni: Mapped[str] = mapped_column(Text, unique=True, nullable=False)    # cifrado Fernet (03 §5.7)
    nombres: Mapped[str] = mapped_column(Text, nullable=False)             # cifrado Fernet
    apellidos: Mapped[str] = mapped_column(Text, nullable=False)           # cifrado Fernet
    telefono: Mapped[str | None] = mapped_column(Text, nullable=True)      # cifrado Fernet
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)     # cifrado Fernet
    fecha_nacimiento: Mapped[str | None] = mapped_column(Text, nullable=True)  # cifrado Fernet
    tipo_contrato: Mapped[str] = mapped_column(String(30), nullable=False, default="tiempo_completo")
    validado_por: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id"), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "tipo_contrato IN ('tiempo_completo','medio_tiempo','eventual','honorarios')",
            name="chk_mecanico_perfil_contrato",
        ),
        Index("idx_mecanico_perfil_dni", "mecanico_id"),
    )


class OrdenTrabajoModel(Base):
    __tablename__ = "orden_trabajo"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehiculo_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vehiculo.id"), nullable=False)
    mecanico_master_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("mecanico.id"), nullable=False)
    mecanico_junior_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("mecanico.id"), nullable=True)
    cliente_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("cliente.id"), nullable=True)
    modalidad: Mapped[str] = mapped_column(String(20), nullable=False)
    urgencia: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ABIERTA")
    cliente_aprobo_lista: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visibilidad_precio_cliente: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cobro_confirmado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    costo_mano_obra: Mapped[object | None] = mapped_column(Numeric(12, 2), nullable=True)
    monto_estimado: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    aceptada_en: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "modalidad IN ('preventivo','correctivo','diagnostico','soldadura')",
            name="chk_ot_modalidad",
        ),
        CheckConstraint(
            "urgencia IN ('alta','media','baja')",
            name="chk_ot_urgencia",
        ),
        CheckConstraint(
            "estado IN ('ABIERTA','LISTA_REPUESTOS','EN_EJECUCION','REVISION_FINAL','CERRADA','CANCELADA')",
            name="chk_ot_estado",
        ),
        Index("idx_ot_vehiculo", "vehiculo_id"),
        Index("idx_ot_mecanico_master", "mecanico_master_id"),
        Index("idx_ot_estado", "estado"),
        Index("idx_ot_cobro", "cobro_confirmado", "estado"),
    )


class ListaRepuestosOTModel(Base):
    __tablename__ = "lista_repuestos_ot"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    orden_trabajo_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("orden_trabajo.id", ondelete="CASCADE"), nullable=False)
    repuesto_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("repuesto.id"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)
    momento_agregado: Mapped[str] = mapped_column(String(20), nullable=False)
    tramo_precio: Mapped[str | None] = mapped_column(String(20), nullable=True)
    aprobacion_cliente: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDIENTE")
    aprobado_en: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    espera_hasta: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="chk_lrot_cantidad"),
        CheckConstraint("momento_agregado IN ('inicial','en_ejecucion')", name="chk_lrot_momento"),
        CheckConstraint(
            "aprobacion_cliente IN ('PENDIENTE','APROBADO_AUTOMATICO','APROBADO_TACITO','APROBADO_EXPLICITO','RECHAZADO','PENDIENTE_ADICIONAL')",
            name="chk_lrot_aprobacion",
        ),
        Index("idx_lrot_orden", "orden_trabajo_id"),
        Index("idx_lrot_aprobacion", "aprobacion_cliente"),
    )


class CostoAdicionalOTModel(Base):
    __tablename__ = "costo_adicional_ot"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    orden_trabajo_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("orden_trabajo.id", ondelete="CASCADE"), nullable=False)
    lista_repuesto_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("lista_repuestos_ot.id"), nullable=False)
    tramo: Mapped[str] = mapped_column(String(20), nullable=False)
    monto_adicional: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)
    espera_hasta: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resultado: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("tramo IN ('automatico','tacito','manual')", name="chk_costo_adic_tramo"),
        Index("idx_costo_adic_ot", "orden_trabajo_id"),
        Index("idx_costo_adic_espera", "espera_hasta"),
    )


class HistorialIntervencionModel(Base):
    __tablename__ = "historial_intervencion"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehiculo_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vehiculo.id"), nullable=False)
    orden_trabajo_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("orden_trabajo.id"), unique=True, nullable=False)
    mecanico_master_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("mecanico.id"), nullable=False)
    fecha_apertura: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_cierre: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    monto_final: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        Index("idx_historial_vehiculo", "vehiculo_id", "fecha_cierre"),
        Index("idx_historial_mecanico", "mecanico_master_id"),
    )


class EntradaModel(Base):
    __tablename__ = "entrada"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehiculo_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("vehiculo.id"), nullable=False)
    orden_trabajo_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("orden_trabajo.id"), nullable=True)
    cliente_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("cliente.id"), nullable=True)
    estado: Mapped[str] = mapped_column(String(10), nullable=False, default="ACTIVA")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("estado IN ('ACTIVA','CERRADA')", name="chk_entrada_estado"),
        Index("idx_entrada_vehiculo", "vehiculo_id"),
        Index("idx_entrada_ot", "orden_trabajo_id"),
        Index("idx_entrada_activa", "estado", "created_at"),
    )


class HistorialCobroMecanicoModel(Base):
    __tablename__ = "historial_cobro_mecanico"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    orden_trabajo_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("orden_trabajo.id"), unique=True, nullable=False)
    mecanico_master_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("mecanico.id"), nullable=False)
    costo_mano_obra: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)
    periodo_mes: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo_año: Mapped[int] = mapped_column(Integer, nullable=False)
    rendicion_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("rendicion_mecanico.id"), nullable=True)

    __table_args__ = (
        CheckConstraint("costo_mano_obra >= 0", name="chk_cobro_mano_obra"),
        Index("idx_cobro_master", "mecanico_master_id"),
        Index("idx_cobro_periodo", "periodo_año", "periodo_mes"),
    )


class RendicionMecanicoModel(Base):
    __tablename__ = "rendicion_mecanico"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    mecanico_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("mecanico.id"), nullable=False)
    periodo_mes: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo_año: Mapped[int] = mapped_column(Integer, nullable=False)
    total_generado: Mapped[object] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("estado IN ('PENDIENTE','APROBADA','PAGADA')", name="chk_rendicion_estado"),
        Index("idx_rendicion_mecanico", "mecanico_id"),
        Index("idx_rendicion_estado", "estado"),
    )


class OrdenTrabajoEventoModel(Base):
    """Auditoría append-only de acciones sobre una OT (R29, FASE 2)."""
    __tablename__ = "orden_trabajo_evento"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    ot_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("orden_trabajo.id"), nullable=False)
    evento: Mapped[str] = mapped_column(String(50), nullable=False)
    estado_anterior: Mapped[str] = mapped_column(String(20), nullable=False)
    estado_nuevo: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_ot_evento_ot", "ot_id"),
        Index("idx_ot_evento_actor", "actor_id"),
    )

"""Modelos SQLAlchemy compartidos: usuario, usuario_perfil, sesion (03 §5.6).
ADR-014: nombre/estado_cuenta/motivo_rechazo/variante_tema/mfa_fallos_consecutivos/
mfa_bloqueado_hasta — campos que antes solo vivían en InMemoryUserStore.UsuarioRecord."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database import Base


class UsuarioModel(Base):
    __tablename__ = "usuario"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Cifrado Fernet real (03 §5.7) desde la verificación profunda 2026-07-05 —
    # antes decía "cifrado Fernet" en el comentario pero se guardaba en texto
    # plano (hallazgo real). Fernet no es determinístico, así que la búsqueda
    # y la unicidad viven en email_hash (índice ciego HMAC-SHA256), no aquí.
    email: Mapped[str] = mapped_column(Text, nullable=False)
    email_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    sub_rol: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mfa_secret: Mapped[str | None] = mapped_column(Text, nullable=True)  # cifrado Fernet
    mfa_habilitado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ultimo_acceso: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    nombre: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estado_cuenta: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVO")
    motivo_rechazo: Mapped[str | None] = mapped_column(Text, nullable=True)
    variante_tema: Mapped[str] = mapped_column(String(30), nullable=False, default="OSCURO_ESTANDAR")
    mfa_fallos_consecutivos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mfa_bloqueado_hasta: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "rol IN ('SUPERADMIN','ADMINISTRADOR','VENDEDOR','MECANICO_MASTER','MECANICO_JUNIOR',"
            "'CLIENTE_CONDUCTOR','CLIENTE_DISTRITO','CLIENTE_RURAL','CLIENTE_FLOTA_DUENO',"
            "'CLIENTE_FLOTA_CONDUCTOR','CLIENTE_MOTOLINEAL')",
            name="chk_usuario_rol",
        ),
        CheckConstraint(
            "estado_cuenta IN ('PENDIENTE_DOCUMENTOS','EN_REVISION','ACTIVO','RECHAZADO')",
            name="chk_usuario_estado_cuenta",
        ),
        CheckConstraint(
            "variante_tema IN ('OSCURO_ESTANDAR','OSCURO_SUAVE','OSCURO_ALTO_CONTRASTE',"
            "'CLARO_ESTANDAR','CLARO_CALIDO','CLARO_ALTO_CONTRASTE')",
            name="chk_usuario_variante_tema",
        ),
        Index("idx_usuario_rol", "rol"),
        Index("idx_usuario_activo", "activo"),
    )


class DocumentoUsuarioModel(Base):
    """Documentos de autorregistro (EP-AUTH-07) — dni_frente/dni_dorso/certificado_tecnico."""
    __tablename__ = "documento_usuario"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    creado_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_documento_usuario_usuario", "usuario_id"),
    )


class MfaSesionModel(Base):
    """Desafío MFA de 2 pasos (EP-AUTH-01/02, ADR-011) — persistido para sobrevivir
    a un reinicio o a múltiples réplicas entre login() y mfa()."""
    __tablename__ = "mfa_sesion"

    token: Mapped[str] = mapped_column(String(36), primary_key=True)
    usuario_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    expira_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requiere_codigo_real: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    codigo_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_mfa_sesion_usuario", "usuario_id"),
    )


class UsuarioPerfilModel(Base):
    __tablename__ = "usuario_perfil"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False)
    nombres: Mapped[str] = mapped_column(Text, nullable=False)           # cifrado Fernet (03 §5.7)
    apellidos: Mapped[str] = mapped_column(Text, nullable=False)         # cifrado Fernet
    dni: Mapped[str | None] = mapped_column(Text, nullable=True)         # cifrado Fernet
    telefono_principal: Mapped[str | None] = mapped_column(Text, nullable=True)   # cifrado Fernet
    telefono_secundario: Mapped[str | None] = mapped_column(Text, nullable=True)  # cifrado Fernet
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)   # cifrado Fernet
    consentimiento_fecha: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    anonimizado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anonimizado_en: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    anonimizado_por: Mapped[str | None] = mapped_column(String(100), nullable=True)
    foto_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    variante_tema: Mapped[str] = mapped_column(
        String(30), nullable=False, default="OSCURO_ESTANDAR"
    )
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "variante_tema IN ('OSCURO_ESTANDAR','OSCURO_SUAVE','OSCURO_ALTO_CONTRASTE',"
            "'CLARO_ESTANDAR','CLARO_CALIDO','CLARO_ALTO_CONTRASTE')",
            name="chk_usuario_perfil_variante_tema",
        ),
        Index("idx_usuario_perfil_usuario", "usuario_id"),
        Index("idx_usuario_perfil_consentimiento", "consentimiento_fecha"),
    )


class SesionModel(Base):
    __tablename__ = "sesion"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    consultas_precio: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mfa_completado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    estado: Mapped[str] = mapped_column(String(10), nullable=False, default="ACTIVA")
    expira_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    # Pieza 6-bis: ventana de inactividad (minutos) que se vuelve a aplicar en
    # cada rotar_refresh exitoso (sesión deslizante) — 15 para roles estándar,
    # 180 (3h) para SUPERADMIN/ADMINISTRADOR, fijado en la creación de la sesión.
    idle_window_minutos: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("consultas_precio >= 0", name="chk_sesion_consultas"),
        CheckConstraint("estado IN ('ACTIVA','REVOCADA')", name="chk_sesion_estado"),
        Index("idx_sesion_usuario", "usuario_id"),
        Index("idx_sesion_jti", "jti"),
        Index("idx_sesion_expiracion", "expira_en"),
    )


class DispositivoConfiableModel(Base):
    """Pieza 6-bis — dispositivo ya verificado por MFA una vez: en logins
    posteriores desde el mismo dispositivo, se salta el paso de MFA (solo
    contraseña). Aplica a los 11 roles; el token vive en localStorage del
    navegador y se identifica aquí solo por su hash SHA-256."""
    __tablename__ = "dispositivo_confiable"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    usuario_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    creado_en: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ultimo_uso: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_dispositivo_confiable_usuario", "usuario_id"),
    )

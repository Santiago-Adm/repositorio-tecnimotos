"""
InMemory auth stores para tests — reemplazados por PostgreSQL + Redis en producción.
Implementa el flujo JWT RS256 + MFA de 07 §2.
Password: PBKDF2-SHA256 en InMemory (producción usa Argon2id+pepper — 07 §2.1).
TOTP: cualquier código 6 dígitos válido en InMemory (producción usa TOTP real).

EstadoCuentaUsuario (sesión 2026-06-28):
  PENDIENTE_DOCUMENTOS → registrado por autorregistro, documentos subidos, sin revisar
  EN_REVISION          → ADMINISTRADOR evaluando activamente
  ACTIVO               → aprobado / creado directamente por admin
  RECHAZADO            → no aprobado, con motivo registrado
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

# ── MFA por correo — solo cuentas internas de alto privilegio (ADR-011) ──────
# SUPERADMIN/ADMINISTRADOR reciben un código real de 6 dígitos por correo.
# El resto de roles mantiene el desafío MFA "de forma" (cualquier 6 dígitos)
# para no romper el contrato de 2 pasos que el frontend ya implementa.
ROLES_MFA_CORREO_REQUERIDO: frozenset[str] = frozenset({"SUPERADMIN", "ADMINISTRADOR"})


# ── Password helpers ──────────────────────────────────────────────────────────

def _hash_password(plaintext: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", plaintext.encode(), salt, 100_000)
    return salt.hex() + ":" + h.hex()


def _verify_password(plaintext: str, stored: str) -> bool:
    try:
        salt_hex, h_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = hashlib.pbkdf2_hmac("sha256", plaintext.encode(), salt, 100_000)
        return hmac.compare_digest(expected, bytes.fromhex(h_hex))
    except Exception:
        return False


# ── MFA por correo: código de 6 dígitos, siempre hasheado (nunca texto plano) ─

def generar_codigo_mfa() -> str:
    """secrets.randbelow — CSPRNG, no random.randint (R23/R29)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_codigo_mfa(codigo: str) -> str:
    return _hash_password(codigo)  # mismo esquema salted PBKDF2 que el password


def _verificar_codigo_mfa(codigo: str, hash_almacenado: str) -> bool:
    return _verify_password(codigo, hash_almacenado)


# ── Datos ─────────────────────────────────────────────────────────────────────

ESTADO_ACTIVO = "ACTIVO"
ESTADO_PENDIENTE = "PENDIENTE_DOCUMENTOS"
ESTADO_EN_REVISION = "EN_REVISION"
ESTADO_RECHAZADO = "RECHAZADO"

# ── Variante de tema (EP-USR-01 / DEP-10-005 resuelto) ───────────────────────

VARIANTE_OSCURO_ESTANDAR = "OSCURO_ESTANDAR"
VARIANTE_OSCURO_SUAVE = "OSCURO_SUAVE"
VARIANTE_OSCURO_ALTO_CONTRASTE = "OSCURO_ALTO_CONTRASTE"
VARIANTE_CLARO_ESTANDAR = "CLARO_ESTANDAR"
VARIANTE_CLARO_CALIDO = "CLARO_CALIDO"
VARIANTE_CLARO_ALTO_CONTRASTE = "CLARO_ALTO_CONTRASTE"

VARIANTES_OSCURAS: frozenset[str] = frozenset({
    VARIANTE_OSCURO_ESTANDAR, VARIANTE_OSCURO_SUAVE, VARIANTE_OSCURO_ALTO_CONTRASTE,
})
VARIANTES_CLARAS: frozenset[str] = frozenset({
    VARIANTE_CLARO_ESTANDAR, VARIANTE_CLARO_CALIDO, VARIANTE_CLARO_ALTO_CONTRASTE,
})
ALL_VARIANTES: frozenset[str] = VARIANTES_OSCURAS | VARIANTES_CLARAS

_ROLES_CLIENTE_TEMA: frozenset[str] = frozenset({
    "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
    "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
})


def _default_variante_tema(rol: str) -> str:
    return VARIANTE_CLARO_ESTANDAR if rol in _ROLES_CLIENTE_TEMA else VARIANTE_OSCURO_ESTANDAR


def variantes_permitidas_para_rol(rol: str) -> frozenset[str]:
    return VARIANTES_CLARAS if rol in _ROLES_CLIENTE_TEMA else VARIANTES_OSCURAS


@dataclass
class DocumentoRecord:
    tipo: str        # "dni_frente" | "dni_dorso" | "certificado_tecnico"
    url: str         # URL pública R2 — en producción se cifra con Fernet (03 §5.7)
    documento_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class UsuarioRecord:
    usuario_id: str
    email: str
    nombre: str
    rol: str
    password_hash: str
    token_version: int = 0
    activo: bool = True
    estado_cuenta: str = ESTADO_ACTIVO
    motivo_rechazo: Optional[str] = None
    documentos: list[DocumentoRecord] = field(default_factory=list)
    variante_tema: str = field(default=VARIANTE_OSCURO_ESTANDAR)


@dataclass
class MfaSessionRecord:
    usuario_id: str
    expires_at: datetime
    intentos_fallidos: int = 0
    usado: bool = False
    requiere_codigo_real: bool = False
    codigo_hash: Optional[str] = None


@dataclass
class SessionRecord:
    session_id: str
    usuario_id: str
    refresh_token_hash: str
    estado: str = "ACTIVA"  # "ACTIVA" | "REVOCADA"
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )


# ── Stores ────────────────────────────────────────────────────────────────────

class InMemoryUserStore:
    """
    Almacén en memoria de usuarios. En producción: tabla `usuario` PostgreSQL.
    Crea un SUPERADMIN de prueba por defecto.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, UsuarioRecord] = {}
        self._by_email: dict[str, str] = {}  # email → usuario_id
        # Usuario de prueba pre-cargado
        self._crear_usuario_interno(
            "user-admin-seed", "admin@tecnimotos.test",
            "Admin Seed", "ADMINISTRADOR", "admin123",
        )

    def _crear_usuario_interno(
        self, uid: str, email: str, nombre: str, rol: str, password: str
    ) -> UsuarioRecord:
        record = UsuarioRecord(
            usuario_id=uid,
            email=email,
            nombre=nombre,
            rol=rol,
            password_hash=_hash_password(password),
            variante_tema=_default_variante_tema(rol),
        )
        self._by_id[uid] = record
        self._by_email[email.lower()] = uid
        return record

    def crear_usuario(
        self, email: str, nombre: str, rol: str, password: str
    ) -> UsuarioRecord:
        if email.lower() in self._by_email:
            raise ValueError(f"Email {email!r} ya registrado")
        uid = str(uuid.uuid4())
        return self._crear_usuario_interno(uid, email, nombre, rol, password)

    def buscar_por_email(self, email: str) -> Optional[UsuarioRecord]:
        uid = self._by_email.get(email.lower())
        return self._by_id.get(uid) if uid else None

    def verificar_credenciales(self, email: str, password: str) -> Optional[UsuarioRecord]:
        """Verifica email + password únicamente. No verifica activo ni estado_cuenta.
        El caller (EP-AUTH-01) decide qué hacer según el estado del usuario."""
        user = self.buscar_por_email(email)
        if user and _verify_password(password, user.password_hash):
            return user
        return None

    def obtener_por_id(self, uid: str) -> Optional[UsuarioRecord]:
        return self._by_id.get(uid)

    def listar(self) -> list[UsuarioRecord]:
        return list(self._by_id.values())

    def existe_superadmin(self) -> bool:
        return any(u.rol == "SUPERADMIN" for u in self._by_id.values())

    def crear_superadmin_bootstrap(
        self, email: str, nombre: str, password: str
    ) -> UsuarioRecord:
        """Crea el primer SUPERADMIN. Solo debe llamarse cuando existe_superadmin() es False."""
        if email.lower() in self._by_email:
            raise ValueError(f"Email {email!r} ya registrado")
        uid = str(uuid.uuid4())
        return self._crear_usuario_interno(uid, email, nombre, "SUPERADMIN", password)

    def incrementar_token_version(self, uid: str) -> None:
        if uid in self._by_id:
            self._by_id[uid].token_version += 1

    def crear_cuenta_pendiente(
        self,
        email: str,
        nombre: str,
        rol: str,
        password: str,
        documentos: list[DocumentoRecord] | None = None,
    ) -> UsuarioRecord:
        """Crea usuario en PENDIENTE_DOCUMENTOS (flujo de autorregistro público)."""
        if email.lower() in self._by_email:
            raise ValueError(f"Email {email!r} ya registrado")
        uid = str(uuid.uuid4())
        record = UsuarioRecord(
            usuario_id=uid,
            email=email,
            nombre=nombre,
            rol=rol,
            password_hash=_hash_password(password),
            estado_cuenta=ESTADO_PENDIENTE,
            documentos=documentos or [],
            variante_tema=_default_variante_tema(rol),
        )
        self._by_id[uid] = record
        self._by_email[email.lower()] = uid
        return record

    def listar_pendientes(self) -> list[UsuarioRecord]:
        return [
            u for u in self._by_id.values()
            if u.estado_cuenta in (ESTADO_PENDIENTE, ESTADO_EN_REVISION)
        ]

    def aprobar_cuenta(self, usuario_id: str) -> Optional[UsuarioRecord]:
        user = self._by_id.get(usuario_id)
        if user:
            user.estado_cuenta = ESTADO_ACTIVO
        return user

    def rechazar_cuenta(self, usuario_id: str, motivo: str) -> Optional[UsuarioRecord]:
        user = self._by_id.get(usuario_id)
        if user:
            user.estado_cuenta = ESTADO_RECHAZADO
            user.motivo_rechazo = motivo
        return user

    def obtener_todos(self) -> list[UsuarioRecord]:
        return list(self._by_id.values())

    def actualizar_variante_tema(self, usuario_id: str, variante: str) -> Optional[UsuarioRecord]:
        user = self._by_id.get(usuario_id)
        if user:
            user.variante_tema = variante
        return user


class InMemorySessionStore:
    """
    Almacén en memoria de sesiones y tokens MFA.
    En producción: tabla `sesion` PostgreSQL + blacklist Redis.
    TOTP: en InMemory acepta cualquier 6 dígitos — producción usa TOTP real (07 §2.2).
    """

    MFA_TTL_MINUTES = 5              # 07 §2.4
    REFRESH_TTL_DAYS = 7             # 07 §2.1
    MAX_MFA_INTENTOS = 5             # 07 §2.5 — intentos máx. dentro de una sesión MFA
    MFA_LOCKOUT_INTENTOS = 5         # fallos consecutivos entre sesiones → bloqueo
    MFA_LOCKOUT_MINUTOS = 15         # duración del bloqueo temporal (ADR-011)

    def __init__(self) -> None:
        self._mfa: dict[str, MfaSessionRecord] = {}   # mfa_token → record
        self._sessions: dict[str, SessionRecord] = {}  # session_id → record
        self._by_refresh_hash: dict[str, str] = {}    # hash → session_id
        self._mfa_fallos_usuario: dict[str, int] = {}      # usuario_id → fallos consecutivos
        self._mfa_bloqueo: dict[str, datetime] = {}         # usuario_id → bloqueado_hasta

    # ── MFA ──

    def usuario_bloqueado_mfa(self, usuario_id: str) -> Optional[datetime]:
        """Retorna bloqueado_hasta si el usuario está en bloqueo temporal, None si no."""
        hasta = self._mfa_bloqueo.get(usuario_id)
        if hasta and datetime.now(timezone.utc) < hasta:
            return hasta
        return None

    def crear_mfa_session(
        self, usuario_id: str, requiere_codigo_real: bool = False
    ) -> tuple[str, Optional[str]]:
        """
        Emite mfa_session_token (UUID simple en InMemory; JWT en producción).
        Si requiere_codigo_real=True (SUPERADMIN/ADMINISTRADOR), genera un código
        real de 6 dígitos, guarda solo su hash, y retorna el código en claro
        para que el caller lo envíe por correo — nunca se persiste en claro.
        Retorna (mfa_session_token, codigo_en_claro_o_None).
        """
        token = str(uuid.uuid4())
        codigo_claro: Optional[str] = None
        codigo_hash: Optional[str] = None
        if requiere_codigo_real:
            codigo_claro = generar_codigo_mfa()
            codigo_hash = _hash_codigo_mfa(codigo_claro)
        self._mfa[token] = MfaSessionRecord(
            usuario_id=usuario_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=self.MFA_TTL_MINUTES),
            requiere_codigo_real=requiere_codigo_real,
            codigo_hash=codigo_hash,
        )
        return token, codigo_claro

    def verificar_mfa(self, mfa_token: str, totp_code: str) -> tuple[str, Optional[str]]:
        """
        Verifica token MFA y código.
        - requiere_codigo_real=True: compara contra el hash del código enviado por correo.
        - requiere_codigo_real=False: acepta cualquier código de 6 dígitos numéricos
          (roles sin MFA real — se mantiene el paso "de forma" por compatibilidad
          con el frontend, ver ADR-011).
        Retorna (resultado, usuario_id) — usuario_id se retorna siempre que el
        token exista (para auditoría, R29), pero el caller solo debe emitir
        tokens de acceso cuando resultado == "EXITOSO".
        resultado ∈ EXITOSO · CODIGO_INCORRECTO · EXPIRADO · BLOQUEADO · TOKEN_INVALIDO.
        """
        record = self._mfa.get(mfa_token)
        if not record:
            return "TOKEN_INVALIDO", None

        bloqueo = self.usuario_bloqueado_mfa(record.usuario_id)
        if bloqueo:
            return "BLOQUEADO", record.usuario_id
        if record.usado:
            return "TOKEN_INVALIDO", record.usuario_id
        if datetime.now(timezone.utc) > record.expires_at:
            return "EXPIRADO", record.usuario_id
        if record.intentos_fallidos >= self.MAX_MFA_INTENTOS:
            return "BLOQUEADO", record.usuario_id

        if record.requiere_codigo_real:
            valido = bool(record.codigo_hash) and _verificar_codigo_mfa(totp_code, record.codigo_hash)
        else:
            valido = len(totp_code) == 6 and totp_code.isdigit()

        if not valido:
            record.intentos_fallidos += 1
            fallos = self._mfa_fallos_usuario.get(record.usuario_id, 0) + 1
            self._mfa_fallos_usuario[record.usuario_id] = fallos
            if fallos >= self.MFA_LOCKOUT_INTENTOS:
                self._mfa_bloqueo[record.usuario_id] = (
                    datetime.now(timezone.utc) + timedelta(minutes=self.MFA_LOCKOUT_MINUTOS)
                )
                return "BLOQUEADO", record.usuario_id
            return "CODIGO_INCORRECTO", record.usuario_id

        record.usado = True
        self._mfa_fallos_usuario.pop(record.usuario_id, None)
        return "EXITOSO", record.usuario_id

    # ── Sesiones ──

    def _hash_refresh(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def crear_sesion(self, usuario_id: str) -> tuple[str, str]:
        """Crea sesión y retorna (session_id, refresh_token_raw)."""
        session_id = str(uuid.uuid4())
        refresh_raw = str(uuid.uuid4())
        refresh_hash = self._hash_refresh(refresh_raw)
        record = SessionRecord(
            session_id=session_id,
            usuario_id=usuario_id,
            refresh_token_hash=refresh_hash,
        )
        self._sessions[session_id] = record
        self._by_refresh_hash[refresh_hash] = session_id
        return session_id, refresh_raw

    def rotar_refresh(self, refresh_raw: str) -> Optional[tuple[str, str, str]]:
        """
        Consume refresh_token y emite uno nuevo.
        Retorna (usuario_id, session_id, nuevo_refresh_raw) o None.
        Replay detection: token ya usado invalida familia completa.
        """
        h = self._hash_refresh(refresh_raw)
        session_id = self._by_refresh_hash.pop(h, None)
        if not session_id:
            return None
        record = self._sessions.get(session_id)
        if not record or record.estado == "REVOCADA":
            return None
        if datetime.now(timezone.utc) > record.expires_at:
            return None
        # Rotar: emitir nuevo refresh_token
        nuevo_raw = str(uuid.uuid4())
        nuevo_hash = self._hash_refresh(nuevo_raw)
        record.refresh_token_hash = nuevo_hash
        self._by_refresh_hash[nuevo_hash] = session_id
        return record.usuario_id, session_id, nuevo_raw

    def revocar_por_refresh(self, refresh_raw: str) -> bool:
        """Revoca la sesión asociada al refresh_token. Retorna True si existía."""
        h = self._hash_refresh(refresh_raw)
        session_id = self._by_refresh_hash.pop(h, None)
        if not session_id:
            return False
        if session_id in self._sessions:
            self._sessions[session_id].estado = "REVOCADA"
            return True
        return False

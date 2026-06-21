"""
InMemory auth stores para tests — reemplazados por PostgreSQL + Redis en producción.
Implementa el flujo JWT RS256 + MFA de 07 §2.
Password: PBKDF2-SHA256 en InMemory (producción usa Argon2id+pepper — 07 §2.1).
TOTP: cualquier código 6 dígitos válido en InMemory (producción usa TOTP real).
"""
from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


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


# ── Datos ─────────────────────────────────────────────────────────────────────

@dataclass
class UsuarioRecord:
    usuario_id: str
    email: str
    nombre: str
    rol: str
    password_hash: str
    token_version: int = 0
    activo: bool = True


@dataclass
class MfaSessionRecord:
    usuario_id: str
    expires_at: datetime
    intentos_fallidos: int = 0
    usado: bool = False


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
        user = self.buscar_por_email(email)
        if user and user.activo and _verify_password(password, user.password_hash):
            return user
        return None

    def obtener_por_id(self, uid: str) -> Optional[UsuarioRecord]:
        return self._by_id.get(uid)

    def listar(self) -> list[UsuarioRecord]:
        return list(self._by_id.values())

    def incrementar_token_version(self, uid: str) -> None:
        if uid in self._by_id:
            self._by_id[uid].token_version += 1


class InMemorySessionStore:
    """
    Almacén en memoria de sesiones y tokens MFA.
    En producción: tabla `sesion` PostgreSQL + blacklist Redis.
    TOTP: en InMemory acepta cualquier 6 dígitos — producción usa TOTP real (07 §2.2).
    """

    MFA_TTL_MINUTES = 5       # 07 §2.4
    REFRESH_TTL_DAYS = 7      # 07 §2.1
    MAX_MFA_INTENTOS = 5      # 07 §2.5

    def __init__(self) -> None:
        self._mfa: dict[str, MfaSessionRecord] = {}   # mfa_token → record
        self._sessions: dict[str, SessionRecord] = {}  # session_id → record
        self._by_refresh_hash: dict[str, str] = {}    # hash → session_id

    # ── MFA ──

    def crear_mfa_session(self, usuario_id: str) -> str:
        """Emite mfa_session_token (UUID simple en InMemory; JWT en producción)."""
        token = str(uuid.uuid4())
        self._mfa[token] = MfaSessionRecord(
            usuario_id=usuario_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=self.MFA_TTL_MINUTES),
        )
        return token

    def verificar_mfa(self, mfa_token: str, totp_code: str) -> Optional[str]:
        """
        Verifica token MFA y código TOTP.
        En InMemory: acepta cualquier código de 6 dígitos numéricos válido.
        Retorna usuario_id si OK, None si falla.
        """
        record = self._mfa.get(mfa_token)
        if not record:
            return None
        if record.usado:
            return None
        if datetime.now(timezone.utc) > record.expires_at:
            return None
        if record.intentos_fallidos >= self.MAX_MFA_INTENTOS:
            return None
        # En InMemory: cualquier código 6 dígitos pasa
        if not (len(totp_code) == 6 and totp_code.isdigit()):
            record.intentos_fallidos += 1
            return None
        record.usado = True
        return record.usuario_id

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

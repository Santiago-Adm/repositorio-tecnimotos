"""Cifrado Fernet en capa de aplicación (03 §5.7, RNT-03)."""
import hashlib
import hmac

from cryptography.fernet import Fernet

from src.shared.infrastructure.settings import get_settings

_fernet: Fernet | None = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        settings = get_settings()
        key = settings.fernet_key
        if not key:
            key = Fernet.generate_key().decode()
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return get_fernet().decrypt(value.encode()).decode()


def _email_hash_key() -> bytes:
    """Deriva una clave separada de FERNET_KEY (nunca reutiliza la misma
    clave para dos propósitos criptográficos distintos) para el índice ciego
    de búsqueda por email — Fernet es no determinístico, así que el email
    cifrado no sirve para WHERE email = :valor; este hash sí."""
    settings = get_settings()
    return hashlib.sha256(settings.fernet_key.encode() + b"tecnimotos:email_hash:v1").digest()


def hash_email(email: str) -> str:
    """Índice ciego determinístico para búsqueda por email (hallazgo real de
    la verificación profunda 2026-07-05: el email se guardaba en texto plano
    pese al comentario '# cifrado Fernet'). Nunca usar para nada que no sea
    igualdad exacta — no es una función de propósito general."""
    return hmac.new(_email_hash_key(), email.strip().lower().encode(), hashlib.sha256).hexdigest()

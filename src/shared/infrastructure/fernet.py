"""Cifrado Fernet en capa de aplicación (03 §5.7, RNT-03)."""
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

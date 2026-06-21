"""Tests unitarios para InMemoryUserStore e InMemorySessionStore (api/auth_stores.py)."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pytest

from api.auth_stores import (
    InMemorySessionStore,
    InMemoryUserStore,
    _verify_password,
    _hash_password,
)


# ── _verify_password ──────────────────────────────────────────────────────────

def test_verify_password_hash_malformado_retorna_false():
    """Líneas 32-33: stored hash en formato inválido → except → False."""
    assert _verify_password("cualquier", "hash-sin-dos-puntos") is False


def test_verify_password_correcto():
    """Roundtrip hash/verify."""
    h = _hash_password("secreto")
    assert _verify_password("secreto", h) is True
    assert _verify_password("otro", h) is False


# ── InMemoryUserStore ─────────────────────────────────────────────────────────

def test_incrementar_token_version_uid_inexistente():
    """Línea 121: uid no existe → noop sin error."""
    store = InMemoryUserStore()
    store.incrementar_token_version("uid-que-no-existe")  # no debe lanzar


def test_incrementar_token_version_uid_existente():
    """Línea 121 rama True: uid existe → token_version aumenta."""
    store = InMemoryUserStore()
    user = store.crear_usuario("a@test.com", "A", "VENDEDOR", "pass12345")
    assert user.token_version == 0
    store.incrementar_token_version(user.usuario_id)
    assert store.obtener_por_id(user.usuario_id).token_version == 1


def test_buscar_por_email_inexistente_retorna_none():
    store = InMemoryUserStore()
    assert store.buscar_por_email("noexiste@test.com") is None


def test_listar_usuarios():
    store = InMemoryUserStore()
    usuarios = store.listar()
    assert len(usuarios) >= 1  # admin seed pre-cargado


# ── InMemorySessionStore — MFA ────────────────────────────────────────────────

def test_mfa_token_ya_usado_retorna_none():
    """Línea 164 (record.usado): token MFA ya consumido → None."""
    store = InMemorySessionStore()
    token = store.crear_mfa_session("u-1")
    # Primer uso OK
    assert store.verificar_mfa(token, "123456") == "u-1"
    # Segundo uso → None
    assert store.verificar_mfa(token, "123456") is None


def test_mfa_token_expirado_retorna_none():
    """Líneas 165-166: MFA TTL expirado → None."""
    store = InMemorySessionStore()
    token = store.crear_mfa_session("u-2")
    # Forzar expiración
    store._mfa[token].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert store.verificar_mfa(token, "123456") is None


def test_mfa_intentos_maximos_retorna_none():
    """Líneas 167-168: MAX_MFA_INTENTOS alcanzado → None."""
    store = InMemorySessionStore()
    token = store.crear_mfa_session("u-3")
    # Agotar intentos con código no numérico (len 3, fuerza incremento)
    for _ in range(store.MAX_MFA_INTENTOS):
        store.verificar_mfa(token, "abc")  # código inválido → incrementa contador
    assert store.verificar_mfa(token, "123456") is None  # intentos agotados


def test_mfa_codigo_invalido_incrementa_intentos():
    """Líneas 170-171: código no 6 dígitos → incrementa intentos_fallidos."""
    store = InMemorySessionStore()
    token = store.crear_mfa_session("u-4")
    resultado = store.verificar_mfa(token, "abc")  # código inválido
    assert resultado is None
    assert store._mfa[token].intentos_fallidos == 1


def test_mfa_token_inexistente_retorna_none():
    """Línea 162: token no registrado → None."""
    store = InMemorySessionStore()
    assert store.verificar_mfa("token-inventado", "123456") is None


# ── InMemorySessionStore — Refresh ────────────────────────────────────────────

def test_rotar_refresh_sesion_revocada_retorna_none():
    """Línea 208: sesión existe pero estado=REVOCADA → None."""
    store = InMemorySessionStore()
    _, refresh = store.crear_sesion("u-5")
    # Revocar la sesión manualmente
    store.revocar_por_refresh(refresh)
    # El refresh ya fue eliminado del índice, así que rotar devuelve None
    assert store.rotar_refresh(refresh) is None


def test_rotar_refresh_expirado_retorna_none():
    """Línea 210: sesión existe pero TTL expirado → None."""
    store = InMemorySessionStore()
    session_id, refresh = store.crear_sesion("u-6")
    # Forzar expiración
    store._sessions[session_id].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert store.rotar_refresh(refresh) is None


def test_revocar_refresh_token_inexistente_retorna_false():
    """Línea 222: refresh token no existe → False."""
    store = InMemorySessionStore()
    assert store.revocar_por_refresh("token-que-no-existe") is False


def test_revocar_refresh_existente_retorna_true():
    """Líneas 223-227: sesión existe → REVOCADA, True."""
    store = InMemorySessionStore()
    _, refresh = store.crear_sesion("u-7")
    assert store.revocar_por_refresh(refresh) is True
    # Segunda revocación → False (token ya no está en índice)
    assert store.revocar_por_refresh(refresh) is False

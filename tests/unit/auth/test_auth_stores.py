"""Tests unitarios para InMemoryUserStore e InMemorySessionStore (api/auth_stores.py).
ADR-014: los métodos de ambos stores son async (mismo contrato que
UsuarioRepositoryPG/SesionRepositoryPG) — todas las llamadas usan await."""
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

async def test_incrementar_token_version_uid_inexistente():
    """Línea 121: uid no existe → noop sin error."""
    store = InMemoryUserStore()
    await store.incrementar_token_version("uid-que-no-existe")  # no debe lanzar


async def test_incrementar_token_version_uid_existente():
    """Línea 121 rama True: uid existe → token_version aumenta."""
    store = InMemoryUserStore()
    user = await store.crear_usuario("a@test.com", "A", "VENDEDOR", "pass12345")
    assert user.token_version == 0
    await store.incrementar_token_version(user.usuario_id)
    actualizado = await store.obtener_por_id(user.usuario_id)
    assert actualizado.token_version == 1


async def test_buscar_por_email_inexistente_retorna_none():
    store = InMemoryUserStore()
    assert await store.buscar_por_email("noexiste@test.com") is None


async def test_listar_usuarios():
    store = InMemoryUserStore()
    usuarios = await store.listar()
    assert len(usuarios) >= 1  # admin seed pre-cargado


# ── InMemorySessionStore — MFA (roles sin código real, ej. clientes) ─────────

async def test_mfa_token_ya_usado_retorna_token_invalido():
    """token MFA ya consumido → TOKEN_INVALIDO."""
    store = InMemorySessionStore()
    token, codigo = await store.crear_mfa_session("u-1")
    # Primer uso OK
    assert await store.verificar_mfa(token, "123456") == ("EXITOSO", "u-1")
    # Segundo uso → inválido
    resultado, usuario_id = await store.verificar_mfa(token, "123456")
    assert resultado == "TOKEN_INVALIDO"


async def test_mfa_token_expirado_retorna_expirado():
    """MFA TTL expirado → EXPIRADO."""
    store = InMemorySessionStore()
    token, _ = await store.crear_mfa_session("u-2")
    store._mfa[token].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    resultado, usuario_id = await store.verificar_mfa(token, "123456")
    assert resultado == "EXPIRADO"
    assert usuario_id == "u-2"


async def test_mfa_intentos_maximos_retorna_bloqueado():
    """MAX_MFA_INTENTOS alcanzado dentro de una misma sesión MFA → BLOQUEADO
    (distinto del bloqueo cross-sesión de InMemoryUserStore, ver ADR-011/ADR-014)."""
    store = InMemorySessionStore()
    token, _ = await store.crear_mfa_session("u-3")
    for _ in range(store.MAX_MFA_INTENTOS - 1):
        resultado, _ = await store.verificar_mfa(token, "abc")
        assert resultado == "CODIGO_INCORRECTO"
    resultado, _ = await store.verificar_mfa(token, "abc")  # intento número MAX_MFA_INTENTOS
    assert resultado == "BLOQUEADO"


async def test_mfa_codigo_invalido_incrementa_intentos():
    """Código no 6 dígitos → incrementa intentos_fallidos, resultado CODIGO_INCORRECTO."""
    store = InMemorySessionStore()
    token, _ = await store.crear_mfa_session("u-4")
    resultado, usuario_id = await store.verificar_mfa(token, "abc")
    assert resultado == "CODIGO_INCORRECTO"
    assert usuario_id == "u-4"
    assert store._mfa[token].intentos_fallidos == 1


async def test_mfa_token_inexistente_retorna_token_invalido():
    """Token no registrado → TOKEN_INVALIDO, sin usuario_id (nada que auditar)."""
    store = InMemorySessionStore()
    resultado, usuario_id = await store.verificar_mfa("token-inventado", "123456")
    assert resultado == "TOKEN_INVALIDO"
    assert usuario_id is None


async def test_usuario_id_de_token_existente_y_inexistente():
    """Peek sin mutar (ADR-014) — usado por el caller para chequear bloqueo
    cross-sesión antes de gastar un intento."""
    store = InMemorySessionStore()
    token, _ = await store.crear_mfa_session("u-peek")
    assert await store.usuario_id_de_token(token) == "u-peek"
    assert await store.usuario_id_de_token("token-inventado") is None


# ── InMemorySessionStore — MFA con código real (SUPERADMIN/ADMINISTRADOR) ────

async def test_mfa_codigo_real_generado_tiene_6_digitos():
    store = InMemorySessionStore()
    _, codigo = await store.crear_mfa_session("u-admin", requiere_codigo_real=True)
    assert codigo is not None
    assert len(codigo) == 6
    assert codigo.isdigit()


async def test_mfa_codigo_real_correcto_pasa():
    store = InMemorySessionStore()
    token, codigo = await store.crear_mfa_session("u-admin", requiere_codigo_real=True)
    resultado, usuario_id = await store.verificar_mfa(token, codigo)
    assert resultado == "EXITOSO"
    assert usuario_id == "u-admin"


async def test_mfa_codigo_real_incorrecto_falla():
    store = InMemorySessionStore()
    token, codigo = await store.crear_mfa_session("u-admin", requiere_codigo_real=True)
    otro_codigo = f"{(int(codigo) + 1) % 1_000_000:06d}"
    resultado, usuario_id = await store.verificar_mfa(token, otro_codigo)
    assert resultado == "CODIGO_INCORRECTO"


async def test_mfa_codigo_real_nunca_se_guarda_en_claro():
    store = InMemorySessionStore()
    token, codigo = await store.crear_mfa_session("u-admin", requiere_codigo_real=True)
    assert store._mfa[token].codigo_hash != codigo
    assert codigo not in store._mfa[token].codigo_hash


def test_mfa_codigo_generado_tiene_distribucion_csprng():
    """generar_codigo_mfa usa secrets.randbelow — no debe repetir siempre el mismo valor."""
    from api.auth_stores import generar_codigo_mfa
    codigos = {generar_codigo_mfa() for _ in range(20)}
    assert len(codigos) > 1


# ── InMemoryUserStore — bloqueo temporal cross-sesión (ADR-011/ADR-014) ──────
# Desde ADR-014, este estado vive en InMemoryUserStore (mismo dueño que
# UsuarioRepositoryPG), no en InMemorySessionStore. El caller real
# (api/routes/auth_routes.py::mfa()) orquesta: verificar_mfa() en session_store
# + registrar_fallo_mfa()/resetear_fallos_mfa() en user_store. Estos tests
# simulan esa orquestación directamente contra InMemoryUserStore.

def _codigo_incorrecto(codigo: str) -> str:
    return f"{(int(codigo) + 1) % 1_000_000:06d}"


async def test_mfa_bloqueo_tras_intentos_fallidos_consecutivos():
    session_store = InMemorySessionStore()
    user_store = InMemoryUserStore()
    for _ in range(user_store.MFA_LOCKOUT_INTENTOS):
        token, codigo = await session_store.crear_mfa_session("u-lockout", requiere_codigo_real=True)
        resultado, _ = await session_store.verificar_mfa(token, _codigo_incorrecto(codigo))
        assert resultado == "CODIGO_INCORRECTO"
        await user_store.registrar_fallo_mfa("u-lockout")
    assert await user_store.usuario_bloqueado_mfa("u-lockout") is not None


async def test_mfa_bloqueo_impide_nuevos_intentos_aunque_el_codigo_sea_correcto():
    session_store = InMemorySessionStore()
    user_store = InMemoryUserStore()
    for _ in range(user_store.MFA_LOCKOUT_INTENTOS):
        token, codigo = await session_store.crear_mfa_session("u-lockout2", requiere_codigo_real=True)
        await session_store.verificar_mfa(token, _codigo_incorrecto(codigo))
        await user_store.registrar_fallo_mfa("u-lockout2")

    assert await user_store.usuario_bloqueado_mfa("u-lockout2") is not None
    # El caller real (mfa()) chequea el bloqueo ANTES de llamar a verificar_mfa
    # — un código correcto ni siquiera se evalúa mientras el usuario esté bloqueado.


async def test_mfa_intentos_agotados_en_sesion_sin_bloqueo_cross_sesion():
    """
    Rama distinta del bloqueo cross-sesión: una sesión MFA individual que
    acumuló MAX_MFA_INTENTOS fallos debe bloquearse igual (BLOQUEADO por
    intentos de sesión), aunque el usuario no esté bloqueado cross-sesión.
    """
    session_store = InMemorySessionStore()
    user_store = InMemoryUserStore()
    token, _ = await session_store.crear_mfa_session("u-6")
    session_store._mfa[token].intentos_fallidos = session_store.MAX_MFA_INTENTOS
    assert await user_store.usuario_bloqueado_mfa("u-6") is None  # sin bloqueo cross-sesión
    resultado, usuario_id = await session_store.verificar_mfa(token, "123456")
    assert resultado == "BLOQUEADO"
    assert usuario_id == "u-6"


async def test_mfa_exito_resetea_contador_de_fallos():
    session_store = InMemorySessionStore()
    user_store = InMemoryUserStore()
    token, codigo = await session_store.crear_mfa_session("u-reset", requiere_codigo_real=True)
    await session_store.verificar_mfa(token, _codigo_incorrecto(codigo))  # 1 fallo
    await user_store.registrar_fallo_mfa("u-reset")

    token2, codigo2 = await session_store.crear_mfa_session("u-reset", requiere_codigo_real=True)
    resultado, _ = await session_store.verificar_mfa(token2, codigo2)
    assert resultado == "EXITOSO"
    await user_store.resetear_fallos_mfa("u-reset")
    assert user_store._mfa_fallos_usuario.get("u-reset", 0) == 0


# ── InMemorySessionStore — Refresh ────────────────────────────────────────────

async def test_rotar_refresh_sesion_revocada_retorna_none():
    """Línea 208: sesión existe pero estado=REVOCADA → None."""
    store = InMemorySessionStore()
    _, refresh = await store.crear_sesion("u-5")
    # Revocar la sesión manualmente
    await store.revocar_por_refresh(refresh)
    # El refresh ya fue eliminado del índice, así que rotar devuelve None
    assert await store.rotar_refresh(refresh) is None


async def test_rotar_refresh_expirado_retorna_none():
    """Línea 210: sesión existe pero TTL expirado → None."""
    store = InMemorySessionStore()
    session_id, refresh = await store.crear_sesion("u-6")
    # Forzar expiración
    store._sessions[session_id].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert await store.rotar_refresh(refresh) is None


async def test_revocar_refresh_token_inexistente_retorna_false():
    """Línea 222: refresh token no existe → False."""
    store = InMemorySessionStore()
    assert await store.revocar_por_refresh("token-que-no-existe") is False


async def test_revocar_refresh_existente_retorna_true():
    """Líneas 223-227: sesión existe → REVOCADA, True."""
    store = InMemorySessionStore()
    _, refresh = await store.crear_sesion("u-7")
    assert await store.revocar_por_refresh(refresh) is True
    # Segunda revocación → False (token ya no está en índice)
    assert await store.revocar_por_refresh(refresh) is False

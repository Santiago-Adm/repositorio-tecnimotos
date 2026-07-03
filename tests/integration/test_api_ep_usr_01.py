"""
Tests EP-USR-01 — PATCH /v1/usuarios/me/tema (preferencia de tema del usuario autenticado).

Escenarios cubiertos:
  - Cambio exitoso dentro de superficie interna (OSCURO_*)
  - Cambio exitoso dentro de superficie CLIENTE (CLARO_*)
  - Rechazo al cruzar superficie: interno intenta variante CLARO_*
  - Rechazo al cruzar superficie: CLIENTE intenta variante OSCURO_*
  - Rechazo con variante desconocida (422)
  - Default OSCURO_ESTANDAR para rol interno creado vía EP-ADM-05
  - Default CLARO_ESTANDAR para rol CLIENTE creado vía EP-ADM-05
  - Default CLARO_ESTANDAR para rol CLIENTE creado vía EP-AUTH-07 (autorregistro)
  - Default OSCURO_ESTANDAR para rol MECANICO creado vía EP-AUTH-07 (autorregistro)
  - variante_tema presente en response real de EP-AUTH-02 (MFA) tras login — interno
  - variante_tema presente en response real de EP-AUTH-02 (MFA) tras login — CLIENTE
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from api.auth_stores import (
    VARIANTE_CLARO_ALTO_CONTRASTE,
    VARIANTE_CLARO_CALIDO,
    VARIANTE_CLARO_ESTANDAR,
    VARIANTE_OSCURO_ALTO_CONTRASTE,
    VARIANTE_OSCURO_ESTANDAR,
    VARIANTE_OSCURO_SUAVE,
)
from tests.integration.conftest import make_test_token

_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16


def _auth_header(private_pem: str, rol: str, sub: str = "test-user") -> dict:
    token = make_test_token(private_pem, rol, sub)
    return {"Authorization": f"Bearer {token}"}


# ── EP-USR-01: Cambio exitoso ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cambio_tema_exitoso_interno(app_client):
    """Rol interno puede cambiar a variante OSCURO_SUAVE."""
    pem = app_client._test_private_pem
    headers = _auth_header(pem, "ADMINISTRADOR", sub="user-admin-seed")
    r = await app_client.patch(
        "/v1/usuarios/me/tema",
        json={"variante_tema": VARIANTE_OSCURO_SUAVE},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["variante_tema"] == VARIANTE_OSCURO_SUAVE


@pytest.mark.asyncio
async def test_cambio_tema_exitoso_cliente(app_client):
    """Rol CLIENTE_CONDUCTOR puede cambiar a variante CLARO_CALIDO."""
    user_store = app_client.app.state.user_store
    user = await user_store.crear_usuario(
        email="conductor@tema.test",
        nombre="Conductor Tema",
        rol="CLIENTE_CONDUCTOR",
        password="pass12345",
    )
    pem = app_client._test_private_pem
    headers = _auth_header(pem, "CLIENTE_CONDUCTOR", sub=user.usuario_id)
    r = await app_client.patch(
        "/v1/usuarios/me/tema",
        json={"variante_tema": VARIANTE_CLARO_CALIDO},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["variante_tema"] == VARIANTE_CLARO_CALIDO


@pytest.mark.asyncio
async def test_cambio_tema_exitoso_alto_contraste_interno(app_client):
    """Rol interno puede cambiar a variante OSCURO_ALTO_CONTRASTE."""
    pem = app_client._test_private_pem
    headers = _auth_header(pem, "SUPERADMIN", sub="user-admin-seed")
    r = await app_client.patch(
        "/v1/usuarios/me/tema",
        json={"variante_tema": VARIANTE_OSCURO_ALTO_CONTRASTE},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["variante_tema"] == VARIANTE_OSCURO_ALTO_CONTRASTE


@pytest.mark.asyncio
async def test_cambio_tema_exitoso_alto_contraste_cliente(app_client):
    """Rol CLIENTE_RURAL puede cambiar a variante CLARO_ALTO_CONTRASTE."""
    user_store = app_client.app.state.user_store
    user = await user_store.crear_usuario(
        email="rural@tema.test",
        nombre="Rural Tema",
        rol="CLIENTE_RURAL",
        password="pass12345",
    )
    pem = app_client._test_private_pem
    headers = _auth_header(pem, "CLIENTE_RURAL", sub=user.usuario_id)
    r = await app_client.patch(
        "/v1/usuarios/me/tema",
        json={"variante_tema": VARIANTE_CLARO_ALTO_CONTRASTE},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["variante_tema"] == VARIANTE_CLARO_ALTO_CONTRASTE


# ── EP-USR-01: Rechazo cruce de superficie ────────────────────────────────────

@pytest.mark.asyncio
async def test_rechazo_cruce_superficie_interno_a_claro(app_client):
    """Rol interno intenta variante CLARO_* — debe ser rechazado con VALIDACION_FALLIDA 422."""
    pem = app_client._test_private_pem
    headers = _auth_header(pem, "VENDEDOR", sub="user-admin-seed")
    r = await app_client.patch(
        "/v1/usuarios/me/tema",
        json={"variante_tema": VARIANTE_CLARO_ESTANDAR},
        headers=headers,
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["error"]["code"] == "VALIDACION_FALLIDA"


@pytest.mark.asyncio
async def test_rechazo_cruce_superficie_cliente_a_oscuro(app_client):
    """Rol CLIENTE_DISTRITO intenta variante OSCURO_* — debe ser rechazado con VALIDACION_FALLIDA 422."""
    user_store = app_client.app.state.user_store
    user = await user_store.crear_usuario(
        email="distrito@tema.test",
        nombre="Distrito Tema",
        rol="CLIENTE_DISTRITO",
        password="pass12345",
    )
    pem = app_client._test_private_pem
    headers = _auth_header(pem, "CLIENTE_DISTRITO", sub=user.usuario_id)
    r = await app_client.patch(
        "/v1/usuarios/me/tema",
        json={"variante_tema": VARIANTE_OSCURO_SUAVE},
        headers=headers,
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["error"]["code"] == "VALIDACION_FALLIDA"


@pytest.mark.asyncio
async def test_rechazo_variante_desconocida(app_client):
    """Variante inventada → VALIDACION_FALLIDA 422."""
    pem = app_client._test_private_pem
    headers = _auth_header(pem, "ADMINISTRADOR", sub="user-admin-seed")
    r = await app_client.patch(
        "/v1/usuarios/me/tema",
        json={"variante_tema": "MODO_ARCOIRIS"},
        headers=headers,
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["error"]["code"] == "VALIDACION_FALLIDA"


# ── Default por rol — EP-ADM-05 ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_default_variante_tema_rol_interno_adm05(app_client):
    """Usuario creado por EP-ADM-05 con rol interno recibe OSCURO_ESTANDAR."""
    pem = app_client._test_private_pem
    headers = _auth_header(pem, "SUPERADMIN")
    r = await app_client.post(
        "/v1/admin/usuarios",
        json={
            "email": "vendedor_default@test.com",
            "nombre": "Vendedor Default",
            "rol": "VENDEDOR",
            "password": "pass12345",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["data"]["variante_tema"] == VARIANTE_OSCURO_ESTANDAR


@pytest.mark.asyncio
async def test_default_variante_tema_rol_cliente_adm05(app_client):
    """Usuario creado por EP-ADM-05 con rol CLIENTE recibe CLARO_ESTANDAR."""
    pem = app_client._test_private_pem
    headers = _auth_header(pem, "ADMINISTRADOR")
    r = await app_client.post(
        "/v1/admin/usuarios",
        json={
            "email": "cliente_default@test.com",
            "nombre": "Cliente Default",
            "rol": "CLIENTE_CONDUCTOR",
            "password": "pass12345",
            "consentimiento_privacidad": True,
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["data"]["variante_tema"] == VARIANTE_CLARO_ESTANDAR


# ── Default por rol — EP-AUTH-07 (autorregistro) ─────────────────────────────

@pytest.mark.asyncio
async def test_default_variante_tema_autorregistro_cliente(app_client):
    """Usuario creado por EP-AUTH-07 (autorregistro CLIENTE_CONDUCTOR) recibe CLARO_ESTANDAR."""
    r = await app_client.post(
        "/v1/auth/registro",
        data={
            "email": "auto@tema.test",
            "nombre": "Auto Registro",
            "password": "pass12345",
            "rol": "CLIENTE_CONDUCTOR",
            "consentimiento_privacidad": "true",
        },
        files={
            "dni_frente": ("frente.jpg", _JPEG, "image/jpeg"),
            "dni_dorso":  ("dorso.jpg",  _JPEG, "image/jpeg"),
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["variante_tema"] == VARIANTE_CLARO_ESTANDAR


@pytest.mark.asyncio
async def test_default_variante_tema_autorregistro_mecanico(app_client):
    """Usuario creado por EP-AUTH-07 (autorregistro MECANICO_JUNIOR) recibe OSCURO_ESTANDAR."""
    _cert = b"\xff\xd8\xff\xe0" + b"\x00" * 16
    r = await app_client.post(
        "/v1/auth/registro",
        data={
            "email": "mecanico_auto@tema.test",
            "nombre": "Mecánico Auto",
            "password": "pass12345",
            "rol": "MECANICO_JUNIOR",
            "consentimiento_privacidad": "true",
        },
        files={
            "dni_frente":          ("frente.jpg", _JPEG, "image/jpeg"),
            "dni_dorso":           ("dorso.jpg",  _JPEG, "image/jpeg"),
            "certificado_tecnico": ("cert.jpg",   _cert, "image/jpeg"),
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["variante_tema"] == VARIANTE_OSCURO_ESTANDAR


# ── variante_tema en response MFA (EP-AUTH-02) ───────────────────────────────

@pytest.mark.asyncio
async def test_variante_tema_en_response_mfa_login_completo(app_client):
    """
    Flujo real de login (EP-AUTH-01 → EP-AUTH-02):
    variante_tema debe estar presente en el response de MFA, no solo en el modelo.
    """
    r1 = await app_client.post(
        "/v1/auth/login",
        json={"email": "admin@tecnimotos.test", "password": "admin123"},
    )
    assert r1.status_code == 200, r1.text
    mfa_token = r1.json()["data"]["mfa_session_token"]

    r2 = await app_client.post(
        "/v1/auth/mfa",
        json={"mfa_session_token": mfa_token, "totp_code": "123456"},
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()["data"]

    assert "variante_tema" in data, "variante_tema debe aparecer en el response de MFA"
    assert data["variante_tema"] == VARIANTE_OSCURO_ESTANDAR  # ADMINISTRADOR → rol interno
    assert "access_token" in data


@pytest.mark.asyncio
async def test_variante_tema_en_response_mfa_cliente(app_client):
    """
    Flujo login para CLIENTE_CONDUCTOR: variante_tema debe ser CLARO_ESTANDAR.
    Crea usuario activo via user_store (ACTIVO para poder hacer login sin aprobación).
    """
    user_store = app_client.app.state.user_store
    await user_store.crear_usuario(
        email="cliente_login@tema.test",
        nombre="Cliente Login",
        rol="CLIENTE_CONDUCTOR",
        password="pass12345",
    )

    r1 = await app_client.post(
        "/v1/auth/login",
        json={"email": "cliente_login@tema.test", "password": "pass12345"},
    )
    assert r1.status_code == 200, r1.text
    mfa_token = r1.json()["data"]["mfa_session_token"]

    r2 = await app_client.post(
        "/v1/auth/mfa",
        json={"mfa_session_token": mfa_token, "totp_code": "654321"},
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()["data"]

    assert data["variante_tema"] == VARIANTE_CLARO_ESTANDAR

"""
Tests de integración — MFA por correo (ADR-011).
SUPERADMIN/ADMINISTRADOR: código real, hasheado, enviado por correo.
Resto de roles: paso MFA "de forma" (cualquier 6 dígitos), sin romper el
contrato de 2 pasos que el frontend ya implementa.
"""
from __future__ import annotations

import re
from unittest.mock import AsyncMock, patch

import pytest

from src.shared.infrastructure.email_sender import EmailSendError


async def _crear_usuario(app_client, rol: str, email: str, password: str = "clave12345"):
    user_store = app_client.app.state.user_store
    return await user_store.crear_usuario(email, f"Usuario {rol}", rol, password)


async def _login_capturando_codigo(client, email: str, password: str) -> tuple[str, str | None]:
    with patch("api.routes.auth_routes.enviar_correo", new=AsyncMock()) as mock_enviar:
        r = await client.post("/v1/auth/login", json={"email": email, "password": password})
    mfa_token = r.json()["data"]["mfa_session_token"]
    codigo = None
    if mock_enviar.await_args:
        cuerpo = mock_enviar.await_args.args[2]
        codigo = re.search(r"\b(\d{6})\b", cuerpo).group(1)
    return mfa_token, codigo


class TestMfaSoloParaRolesInternosAltoPrivilegio:
    async def test_superadmin_recibe_codigo_real_por_correo(self, app_client):
        await _crear_usuario(app_client, "SUPERADMIN", "super@tecnimotos.test")
        with patch("api.routes.auth_routes.enviar_correo", new=AsyncMock()) as mock_enviar:
            await app_client.post(
                "/v1/auth/login",
                json={"email": "super@tecnimotos.test", "password": "clave12345"},
            )
        mock_enviar.assert_awaited_once()
        destinatario = mock_enviar.await_args.args[0]
        assert destinatario == "super@tecnimotos.test"

    async def test_administrador_recibe_codigo_real_por_correo(self, app_client):
        await _crear_usuario(app_client, "ADMINISTRADOR", "adm2@tecnimotos.test")
        with patch("api.routes.auth_routes.enviar_correo", new=AsyncMock()) as mock_enviar:
            await app_client.post(
                "/v1/auth/login",
                json={"email": "adm2@tecnimotos.test", "password": "clave12345"},
            )
        mock_enviar.assert_awaited_once()

    async def test_vendedor_no_recibe_correo_mfa(self, app_client):
        await _crear_usuario(app_client, "VENDEDOR", "vendedor@tecnimotos.test")
        with patch("api.routes.auth_routes.enviar_correo", new=AsyncMock()) as mock_enviar:
            await app_client.post(
                "/v1/auth/login",
                json={"email": "vendedor@tecnimotos.test", "password": "clave12345"},
            )
        mock_enviar.assert_not_called()

    async def test_vendedor_pasa_mfa_con_cualquier_codigo_6_digitos(self, app_client):
        await _crear_usuario(app_client, "VENDEDOR", "vendedor2@tecnimotos.test")
        login_r = await app_client.post(
            "/v1/auth/login",
            json={"email": "vendedor2@tecnimotos.test", "password": "clave12345"},
        )
        mfa_token = login_r.json()["data"]["mfa_session_token"]
        r = await app_client.post(
            "/v1/auth/mfa", json={"mfa_session_token": mfa_token, "totp_code": "777777"}
        )
        assert r.status_code == 200

    async def test_superadmin_codigo_incorrecto_falla(self, app_client):
        await _crear_usuario(app_client, "SUPERADMIN", "super3@tecnimotos.test")
        mfa_token, codigo = await _login_capturando_codigo(
            app_client, "super3@tecnimotos.test", "clave12345"
        )
        codigo_malo = "000001" if codigo != "000001" else "000002"
        r = await app_client.post(
            "/v1/auth/mfa", json={"mfa_session_token": mfa_token, "totp_code": codigo_malo}
        )
        assert r.status_code == 401

    async def test_login_no_falla_si_el_envio_de_correo_falla(self, app_client):
        """Fallo transitorio del proveedor de correo no debe bloquear el login
        (el admin puede reintentar y recibir un código nuevo)."""
        await _crear_usuario(app_client, "SUPERADMIN", "super5@tecnimotos.test")
        with patch(
            "api.routes.auth_routes.enviar_correo",
            new=AsyncMock(side_effect=EmailSendError("Resend caído")),
        ):
            r = await app_client.post(
                "/v1/auth/login",
                json={"email": "super5@tecnimotos.test", "password": "clave12345"},
            )
        assert r.status_code == 200
        assert "mfa_session_token" in r.json()["data"]

    async def test_superadmin_codigo_correcto_pasa(self, app_client):
        await _crear_usuario(app_client, "SUPERADMIN", "super4@tecnimotos.test")
        mfa_token, codigo = await _login_capturando_codigo(
            app_client, "super4@tecnimotos.test", "clave12345"
        )
        r = await app_client.post(
            "/v1/auth/mfa", json={"mfa_session_token": mfa_token, "totp_code": codigo}
        )
        assert r.status_code == 200
        assert "access_token" in r.json()["data"]


class TestBloqueoTemporal:
    async def test_bloqueo_tras_intentos_fallidos_consecutivos(self, app_client):
        user_store = app_client.app.state.user_store
        await _crear_usuario(app_client, "ADMINISTRADOR", "bloqueo@tecnimotos.test")

        for _ in range(user_store.MFA_LOCKOUT_INTENTOS):
            mfa_token, codigo = await _login_capturando_codigo(
                app_client, "bloqueo@tecnimotos.test", "clave12345"
            )
            malo = "000001" if codigo != "000001" else "000002"
            await app_client.post(
                "/v1/auth/mfa", json={"mfa_session_token": mfa_token, "totp_code": malo}
            )

        r = await app_client.post(
            "/v1/auth/login",
            json={"email": "bloqueo@tecnimotos.test", "password": "clave12345"},
        )
        assert r.status_code == 403
        assert r.json()["detail"]["error"]["code"] == "CUENTA_BLOQUEADA_TEMPORAL"


class TestAuditoriaMfa:
    async def test_intento_exitoso_se_audita(self, app_client):
        await _crear_usuario(app_client, "ADMINISTRADOR", "audit1@tecnimotos.test")
        mfa_token, codigo = await _login_capturando_codigo(
            app_client, "audit1@tecnimotos.test", "clave12345"
        )
        with patch(
            "api.routes.auth_routes.registrar_intento_mfa", new=AsyncMock()
        ) as mock_auditoria:
            await app_client.post(
                "/v1/auth/mfa", json={"mfa_session_token": mfa_token, "totp_code": codigo}
            )
        mock_auditoria.assert_awaited_once()
        args = mock_auditoria.await_args.args
        assert args[2] == "EXITOSO"

    async def test_intento_fallido_se_audita(self, app_client):
        await _crear_usuario(app_client, "ADMINISTRADOR", "audit2@tecnimotos.test")
        mfa_token, codigo = await _login_capturando_codigo(
            app_client, "audit2@tecnimotos.test", "clave12345"
        )
        malo = "000001" if codigo != "000001" else "000002"
        with patch(
            "api.routes.auth_routes.registrar_intento_mfa", new=AsyncMock()
        ) as mock_auditoria:
            await app_client.post(
                "/v1/auth/mfa", json={"mfa_session_token": mfa_token, "totp_code": malo}
            )
        mock_auditoria.assert_awaited_once()
        args = mock_auditoria.await_args.args
        assert args[2] == "CODIGO_INCORRECTO"

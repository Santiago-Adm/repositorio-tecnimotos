"""
Tests de integración — cuentas sembradas con `pendiente_habilitacion=True`
(S3/S5: CLIENTE_FLOTA_DUENO, CLIENTE_FLOTA_CONDUCTOR, CLIENTE_MOTOLINEAL).

Estos 3 roles no están activos en el MVP (01 §Segmentos, WON'T documentado
en 01-contexto-proyecto.md) pero el backend ya los acepta en CLIENTE_ROLES
con usuarios seed reales. Requisito real: el login debe reconocer las
credenciales como válidas pero bloquear el acceso con el mismo patrón ya
usado para "Cuentas Pendientes" (EN_REVISION) — la habilitación real debe
requerir una acción CRUD explícita de ADMINISTRADOR/SUPERADMIN (EP-ADM-07),
nunca un cambio de código.
"""
from __future__ import annotations

import pytest

from api.auth_stores import ESTADO_ACTIVO, ESTADO_EN_REVISION
from tests.integration.conftest import make_test_token


@pytest.fixture
async def cuenta_flota(app_client):
    user_store = app_client.app.state.user_store
    user = await user_store.crear_cuenta_pendiente(
        email="flota.dueno@test.com", nombre="Flota Dueno Seed",
        rol="CLIENTE_FLOTA_DUENO", password="flotadueno123",
        estado_inicial=ESTADO_EN_REVISION,
    )
    return app_client, user


class TestCuentaPendienteHabilitacion:
    async def test_se_crea_en_revision_no_activo(self, cuenta_flota):
        _client, user = cuenta_flota
        assert user.estado_cuenta == ESTADO_EN_REVISION

    async def test_login_reconoce_credenciales_pero_bloquea_acceso(self, cuenta_flota):
        client, _user = cuenta_flota
        response = await client.post(
            "/v1/auth/login",
            json={"email": "flota.dueno@test.com", "password": "flotadueno123"},
        )
        # Credenciales válidas reconocidas (no es 401 "credenciales inválidas")
        # pero el acceso queda bloqueado — mismo código que Cuentas Pendientes.
        assert response.status_code == 403
        assert response.json()["detail"]["error"]["code"] == "CUENTA_EN_REVISION"

    async def test_login_con_password_incorrecta_sigue_dando_401_generico(self, cuenta_flota):
        client, _user = cuenta_flota
        response = await client.post(
            "/v1/auth/login",
            json={"email": "flota.dueno@test.com", "password": "password-incorrecta"},
        )
        assert response.status_code == 401

    async def test_aparece_en_cuentas_pendientes_para_admin(self, cuenta_flota):
        client, user = cuenta_flota
        response = await client.get("/v1/admin/usuarios/pendientes")
        assert response.status_code == 200
        emails = [u["email"] for u in response.json()["data"]["usuarios"]]
        assert user.email in emails

    async def test_aprobar_cuenta_habilita_login_real(self, cuenta_flota):
        client, user = cuenta_flota
        aprobar = await client.post(f"/v1/admin/usuarios/{user.usuario_id}/aprobar")
        assert aprobar.status_code == 200
        assert aprobar.json()["data"]["estado_cuenta"] == ESTADO_ACTIVO

        response = await client.post(
            "/v1/auth/login",
            json={"email": "flota.dueno@test.com", "password": "flotadueno123"},
        )
        # Ya no bloquea por estado de cuenta — avanza al paso de MFA real.
        assert response.status_code == 200
        assert "mfa_session_token" in response.json()["data"]

    async def test_rol_no_interno_no_puede_aprobar(self, cuenta_flota):
        client, user = cuenta_flota
        token = make_test_token(client._test_private_pem, "VENDEDOR")
        response = await client.post(
            f"/v1/admin/usuarios/{user.usuario_id}/aprobar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

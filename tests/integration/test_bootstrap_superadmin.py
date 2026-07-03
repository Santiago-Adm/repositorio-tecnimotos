"""
Tests de integración — EP-AUTH-06 bootstrap-superadmin.

Casos cubiertos:
  - Éxito primera vez (sin SUPERADMIN previo, clave correcta)
  - Rechazo con clave de bootstrap incorrecta
  - Rechazo si ya existe un SUPERADMIN (endpoint permanentemente deshabilitado)
  - Tras crear el SUPERADMIN via bootstrap, el login normal (EP-AUTH-01) funciona
"""
import pytest
from httpx import AsyncClient, ASGITransport

from api.main import create_app
from tests.integration.conftest import _generate_test_keypair


_BOOTSTRAP_KEY = "clave-bootstrap-de-prueba-xK9m"
_BODY_VALIDO = {
    "email": "superadmin@tecnimotos.test",
    "nombre": "Super Admin",
    "password": "sa_password_segura",
    "bootstrap_key": _BOOTSTRAP_KEY,
}


@pytest.fixture
async def bootstrap_client():
    """
    App limpia con superadmin_bootstrap_key inyectada en app.state.
    El InMemoryUserStore arranca sin SUPERADMIN (solo hay un ADMINISTRADOR de seed).
    """
    private_pem, public_pem = _generate_test_keypair()
    app = create_app()
    app.state.jwt_public_key = public_pem
    app.state.jwt_private_key = private_pem
    app.state.superadmin_bootstrap_key = _BOOTSTRAP_KEY

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        client.app = app
        yield client


@pytest.mark.asyncio
async def test_bootstrap_exito_primera_vez(bootstrap_client):
    """EP-AUTH-06: primer SUPERADMIN creado correctamente."""
    response = await bootstrap_client.post(
        "/v1/auth/bootstrap-superadmin",
        json=_BODY_VALIDO,
    )
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    assert data["rol"] == "SUPERADMIN"
    assert data["email"] == _BODY_VALIDO["email"]
    assert "usuario_id" in data


@pytest.mark.asyncio
async def test_bootstrap_rechaza_clave_incorrecta(bootstrap_client):
    """EP-AUTH-06: clave de bootstrap incorrecta → 401."""
    body = {**_BODY_VALIDO, "bootstrap_key": "clave-incorrecta"}
    response = await bootstrap_client.post(
        "/v1/auth/bootstrap-superadmin",
        json=body,
    )
    assert response.status_code == 401
    error = response.json()["detail"]["error"]
    assert error["code"] == "AUTENTICACION_REQUERIDA"


@pytest.mark.asyncio
async def test_bootstrap_rechaza_si_ya_existe_superadmin(bootstrap_client):
    """EP-AUTH-06: si ya existe un SUPERADMIN, el endpoint se rechaza permanentemente."""
    # Primera llamada exitosa
    r1 = await bootstrap_client.post("/v1/auth/bootstrap-superadmin", json=_BODY_VALIDO)
    assert r1.status_code == 201

    # Segunda llamada — aunque la clave es correcta, debe rechazarse
    body_segundo = {
        "email": "otro_superadmin@tecnimotos.test",
        "nombre": "Otro SA",
        "password": "otro_pass_seguro",
        "bootstrap_key": _BOOTSTRAP_KEY,
    }
    r2 = await bootstrap_client.post("/v1/auth/bootstrap-superadmin", json=body_segundo)
    assert r2.status_code == 409
    error = r2.json()["detail"]["error"]
    assert error["code"] == "VALIDACION_FALLIDA"
    assert "permanentemente deshabilitado" in error["message"]


@pytest.mark.asyncio
async def test_bootstrap_superadmin_puede_loguearse(bootstrap_client):
    """Tras crear el SUPERADMIN via bootstrap, el login normal funciona (EP-AUTH-01)."""
    await bootstrap_client.post("/v1/auth/bootstrap-superadmin", json=_BODY_VALIDO)

    response = await bootstrap_client.post(
        "/v1/auth/login",
        json={"email": _BODY_VALIDO["email"], "password": _BODY_VALIDO["password"]},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "mfa_session_token" in data

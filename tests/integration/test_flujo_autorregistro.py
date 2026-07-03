"""
Tests de integración — Flujo de cuentas pendientes de documentos (EP-AUTH-07,
EP-AUTH-01 modificado, EP-ADM-05 sin regresión, EP-ADM-06/07/08).

Escenarios cubiertos:
  - Autorregistro exitoso por cada tipo de rol con sus documentos requeridos
  - Rechazo de autorregistro sin documento requerido (mecánico sin certificado)
  - Rechazo de rol no permitido en autorregistro (ADMINISTRADOR)
  - Login rechazado con mensaje específico mientras PENDIENTE_DOCUMENTOS
  - Login rechazado con mensaje específico mientras EN_REVISION
  - Login rechazado con mensaje específico mientras RECHAZADO
  - Aprobación → login posterior exitoso
  - Rechazo con motivo → login sigue bloqueado
  - EP-ADM-05 (creación directa por admin) sin regresión — sigue sin revisión
  - Evento usuario.registro_pendiente se publica al autorregistrarse
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from api.auth_stores import ESTADO_ACTIVO, ESTADO_PENDIENTE, ESTADO_RECHAZADO
from tests.integration.conftest import make_test_token

_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16
_DNI_FILES = {
    "dni_frente": ("dni_frente.jpg", _JPEG, "image/jpeg"),
    "dni_dorso":  ("dni_dorso.jpg",  _JPEG, "image/jpeg"),
}
_CERTIFICADO = ("certificado.jpg", _JPEG, "image/jpeg")


def _form_data_registro(**extra):
    return {
        "email": extra.pop("email", "nuevo@test.com"),
        "nombre": extra.pop("nombre", "Nuevo Usuario"),
        "password": extra.pop("password", "pass12345"),
        "rol": extra.pop("rol", "CLIENTE_CONDUCTOR"),
        "consentimiento_privacidad": extra.pop("consentimiento_privacidad", "true"),
        **extra,
    }


async def _registrar(client: AsyncClient, **kwargs) -> dict:
    rol = kwargs.get("rol", "CLIENTE_CONDUCTOR")
    data = _form_data_registro(**kwargs)
    files = dict(_DNI_FILES)
    if rol in ("MECANICO_MASTER", "MECANICO_JUNIOR"):
        files["certificado_tecnico"] = _CERTIFICADO
    return await client.post("/v1/auth/registro", data=data, files=files)


# ── EP-AUTH-07 — Autorregistro ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_autorregistro_cliente_exitoso(app_client):
    r = await _registrar(app_client, email="cliente@test.com", rol="CLIENTE_CONDUCTOR")
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["estado_cuenta"] == ESTADO_PENDIENTE
    assert "dni_frente" in data["documentos_recibidos"]
    assert "dni_dorso" in data["documentos_recibidos"]


@pytest.mark.asyncio
async def test_autorregistro_vendedor_exitoso(app_client):
    r = await _registrar(app_client, email="vendedor@test.com", rol="VENDEDOR")
    assert r.status_code == 201, r.text
    assert r.json()["data"]["estado_cuenta"] == ESTADO_PENDIENTE


@pytest.mark.asyncio
async def test_autorregistro_mecanico_master_con_certificado(app_client):
    r = await _registrar(app_client, email="mecanico@test.com", rol="MECANICO_MASTER")
    assert r.status_code == 201, r.text
    recibidos = r.json()["data"]["documentos_recibidos"]
    assert "certificado_tecnico" in recibidos


@pytest.mark.asyncio
async def test_autorregistro_mecanico_junior_con_certificado(app_client):
    r = await _registrar(app_client, email="junior@test.com", rol="MECANICO_JUNIOR")
    assert r.status_code == 201, r.text
    assert "certificado_tecnico" in r.json()["data"]["documentos_recibidos"]


@pytest.mark.asyncio
async def test_autorregistro_mecanico_sin_certificado_rechaza(app_client):
    """Mecánico sin certificado_tecnico → 422."""
    r = await app_client.post(
        "/v1/auth/registro",
        data=_form_data_registro(email="mec@test.com", rol="MECANICO_MASTER"),
        files=dict(_DNI_FILES),  # sin certificado_tecnico
    )
    assert r.status_code == 422, r.text
    assert "certificado_tecnico" in r.json()["detail"]["error"]["message"]


@pytest.mark.asyncio
async def test_autorregistro_administrador_rechazado(app_client):
    """ADMINISTRADOR no puede autorregistrarse → 422."""
    r = await _registrar(app_client, email="adm@test.com", rol="ADMINISTRADOR")
    assert r.status_code == 422, r.text
    assert "no permitido en autorregistro" in r.json()["detail"]["error"]["message"]


@pytest.mark.asyncio
async def test_autorregistro_superadmin_rechazado(app_client):
    r = await _registrar(app_client, email="super@test.com", rol="SUPERADMIN")
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_autorregistro_sin_consentimiento_rechazado(app_client):
    r = await app_client.post(
        "/v1/auth/registro",
        data=_form_data_registro(email="sin@test.com", consentimiento_privacidad="false"),
        files=dict(_DNI_FILES),
    )
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_evento_registro_pendiente_se_publica(app_client):
    from src.shared.events.event_bus import InMemoryEventBus
    bus: InMemoryEventBus = app_client.app.state.event_bus
    antes = bus.conteo_publicaciones("usuario.registro_pendiente")
    await _registrar(app_client, email="evento@test.com", rol="VENDEDOR")
    assert bus.conteo_publicaciones("usuario.registro_pendiente") == antes + 1


# ── EP-AUTH-01 modificado — bloqueo mientras no ACTIVO ───────────────────────

@pytest.fixture
async def usuario_pendiente(app_client):
    """Crea usuario en PENDIENTE_DOCUMENTOS y retorna (client, email, password)."""
    await _registrar(app_client, email="pendiente@test.com", password="clave1234", rol="VENDEDOR")
    return app_client, "pendiente@test.com", "clave1234"


@pytest.mark.asyncio
async def test_login_rechazado_mientras_pendiente_con_mensaje_especifico(usuario_pendiente):
    client, email, password = usuario_pendiente
    r = await client.post("/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 403, r.text
    error = r.json()["detail"]["error"]
    assert error["code"] == "CUENTA_EN_REVISION"
    assert "revisión" in error["message"]
    # NO debe usar el código genérico de credenciales
    assert error["code"] != "AUTENTICACION_REQUERIDA"


@pytest.mark.asyncio
async def test_login_rechazado_mientras_en_revision(app_client):
    await _registrar(app_client, email="enrev@test.com", password="clave1234", rol="VENDEDOR")
    user_store = app_client.app.state.user_store
    user = user_store.buscar_por_email("enrev@test.com")
    user.estado_cuenta = "EN_REVISION"

    r = await app_client.post("/v1/auth/login", json={"email": "enrev@test.com", "password": "clave1234"})
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "CUENTA_EN_REVISION"


@pytest.mark.asyncio
async def test_login_rechazado_tras_rechazo_admin(app_client):
    await _registrar(app_client, email="rechazado@test.com", password="clave1234", rol="VENDEDOR")
    user_store = app_client.app.state.user_store
    user = user_store.buscar_por_email("rechazado@test.com")
    user_store.rechazar_cuenta(user.usuario_id, "Documentos ilegibles, no se puede verificar identidad.")

    r = await app_client.post("/v1/auth/login", json={"email": "rechazado@test.com", "password": "clave1234"})
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "CUENTA_EN_REVISION"


# ── EP-ADM-06/07/08 — Aprobar y rechazar cuentas ────────────────────────────

@pytest.fixture
async def flujo_completo(app_client):
    """Registra usuario pendiente y retorna (client, usuario_id)."""
    r = await _registrar(app_client, email="flujo@test.com", password="clave1234", rol="CLIENTE_CONDUCTOR")
    uid = r.json()["data"]["usuario_id"]
    return app_client, uid


@pytest.mark.asyncio
async def test_listar_pendientes_muestra_nuevo_registro(flujo_completo):
    client, uid = flujo_completo
    r = await client.get("/v1/admin/usuarios/pendientes")
    assert r.status_code == 200, r.text
    ids = [u["usuario_id"] for u in r.json()["data"]["usuarios"]]
    assert uid in ids


@pytest.mark.asyncio
async def test_aprobar_cuenta_y_login_exitoso(flujo_completo):
    client, uid = flujo_completo

    r_aprobar = await client.post(f"/v1/admin/usuarios/{uid}/aprobar")
    assert r_aprobar.status_code == 200, r_aprobar.text
    assert r_aprobar.json()["data"]["estado_cuenta"] == ESTADO_ACTIVO

    # Ahora puede hacer login
    r_login = await client.post("/v1/auth/login", json={"email": "flujo@test.com", "password": "clave1234"})
    assert r_login.status_code == 200, r_login.text
    assert "mfa_session_token" in r_login.json()["data"]


@pytest.mark.asyncio
async def test_rechazar_cuenta_con_motivo(flujo_completo):
    client, uid = flujo_completo

    r = await client.post(
        f"/v1/admin/usuarios/{uid}/rechazar",
        json={"motivo_rechazo": "El DNI enviado está borroso y no permite verificar identidad."},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["estado_cuenta"] == ESTADO_RECHAZADO
    assert "motivo_rechazo" in data


@pytest.mark.asyncio
async def test_login_sigue_bloqueado_tras_rechazo(flujo_completo):
    client, uid = flujo_completo
    await client.post(
        f"/v1/admin/usuarios/{uid}/rechazar",
        json={"motivo_rechazo": "Documentos no coinciden con los requeridos para el rol."},
    )

    r = await client.post("/v1/auth/login", json={"email": "flujo@test.com", "password": "clave1234"})
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "CUENTA_EN_REVISION"


@pytest.mark.asyncio
async def test_pendientes_no_aparece_en_lista_tras_aprobar(flujo_completo):
    client, uid = flujo_completo
    await client.post(f"/v1/admin/usuarios/{uid}/aprobar")

    r = await client.get("/v1/admin/usuarios/pendientes")
    ids = [u["usuario_id"] for u in r.json()["data"]["usuarios"]]
    assert uid not in ids


# ── EP-ADM-05 sin regresión ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_crea_usuario_directo_sin_revision(app_client):
    """EP-ADM-05: usuario creado por admin queda ACTIVO de inmediato (sin revisión)."""
    r = await app_client.post(
        "/v1/admin/usuarios",
        json={
            "email": "directo@test.com",
            "nombre": "Usuario Directo",
            "rol": "VENDEDOR",
            "password": "clave12345",
            "consentimiento_privacidad": False,
        },
    )
    assert r.status_code == 201, r.text
    uid = r.json()["data"]["usuario_id"]

    # Confirmar que está ACTIVO en el store
    user_store = app_client.app.state.user_store
    user = user_store.obtener_por_id(uid)
    assert user is not None
    assert user.estado_cuenta == ESTADO_ACTIVO

    # Puede hacer login de inmediato
    r_login = await app_client.post(
        "/v1/auth/login",
        json={"email": "directo@test.com", "password": "clave12345"},
    )
    assert r_login.status_code == 200, r_login.text


@pytest.mark.asyncio
async def test_aprobar_usuario_inexistente_retorna_404(app_client):
    r = await app_client.post("/v1/admin/usuarios/uid-no-existe/aprobar")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_rechazar_usuario_inexistente_retorna_404(app_client):
    r = await app_client.post(
        "/v1/admin/usuarios/uid-no-existe/rechazar",
        json={"motivo_rechazo": "Motivo de prueba suficientemente largo."},
    )
    assert r.status_code == 404

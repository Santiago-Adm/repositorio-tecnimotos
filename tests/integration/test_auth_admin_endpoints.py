"""
Tests de integración EP-AUTH-01 a EP-AUTH-04 y EP-ADM-01 a EP-ADM-05 (03 §6.6).
Todos pasan con la misma infraestructura InMemory + test keypair del conftest.
"""
from __future__ import annotations

import re
from unittest.mock import AsyncMock, patch

import pytest
from tests.integration.conftest import make_test_token


async def _login_y_obtener_codigo_mfa(
    client, email: str = "admin@tecnimotos.test", password: str = "admin123"
) -> tuple[str, str]:
    """
    Login capturando el código MFA real enviado por correo (ADR-011:
    ADMINISTRADOR/SUPERADMIN requieren código real — se mockea enviar_correo
    para extraer el código sin depender de un proveedor de email real).
    Retorna (mfa_session_token, codigo).
    """
    with patch("api.routes.auth_routes.enviar_correo", new=AsyncMock()) as mock_enviar:
        login_r = await client.post(
            "/v1/auth/login", json={"email": email, "password": password}
        )
    mfa_token = login_r.json()["data"]["mfa_session_token"]
    if mock_enviar.await_args:
        cuerpo = mock_enviar.await_args.args[2]
        codigo = re.search(r"\b(\d{6})\b", cuerpo).group(1)
    else:
        codigo = "123456"  # rol sin MFA real — cualquier código de 6 dígitos pasa
    return mfa_token, codigo


# ══════════════════════════════════════════════════════════════════════
# EP-AUTH-01 — Login (POST /v1/auth/login)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_auth01_login_correcto_retorna_mfa_token(app_client):
    """EP-AUTH-01: credenciales válidas → mfa_session_token."""
    r = await app_client.post("/v1/auth/login", json={
        "email": "admin@tecnimotos.test",
        "password": "admin123",
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert "mfa_session_token" in data
    assert len(data["mfa_session_token"]) > 10


@pytest.mark.asyncio
async def test_auth01_credenciales_incorrectas_retorna_401(app_client):
    """EP-AUTH-01: password incorrecto → 401 mensaje idéntico (07 §2.5 anti-enumeración)."""
    r = await app_client.post("/v1/auth/login", json={
        "email": "admin@tecnimotos.test",
        "password": "wrong_password",
    })
    assert r.status_code == 401
    assert r.json()["detail"]["error"]["code"] == "AUTENTICACION_REQUERIDA"


@pytest.mark.asyncio
async def test_auth01_email_inexistente_retorna_401_igual(app_client):
    """EP-AUTH-01: email inexistente → mismo 401 (no revela si el email existe)."""
    r = await app_client.post("/v1/auth/login", json={
        "email": "noexiste@test.com",
        "password": "cualquier_cosa",
    })
    assert r.status_code == 401
    assert r.json()["detail"]["error"]["code"] == "AUTENTICACION_REQUERIDA"


# ══════════════════════════════════════════════════════════════════════
# EP-AUTH-02 — MFA (POST /v1/auth/mfa)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_auth02_mfa_correcto_retorna_access_token_y_cookie(app_client):
    """EP-AUTH-02: mfa_session_token válido + código correcto → access_token + refresh_cookie."""
    mfa_token, codigo = await _login_y_obtener_codigo_mfa(app_client)

    r = await app_client.post("/v1/auth/mfa", json={
        "mfa_session_token": mfa_token, "totp_code": codigo,
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in r.cookies


@pytest.mark.asyncio
async def test_auth02_mfa_token_invalido_retorna_401(app_client):
    """EP-AUTH-02: mfa_session_token inválido → 401."""
    r = await app_client.post("/v1/auth/mfa", json={
        "mfa_session_token": "token-inventado-invalido", "totp_code": "123456",
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth02_mfa_token_ya_usado_retorna_401(app_client):
    """EP-AUTH-02: mfa_session_token ya consumido → 401 (replay)."""
    mfa_token, codigo = await _login_y_obtener_codigo_mfa(app_client)
    # Primer uso — OK
    await app_client.post("/v1/auth/mfa", json={
        "mfa_session_token": mfa_token, "totp_code": codigo,
    })
    # Segundo uso — debe fallar
    r = await app_client.post("/v1/auth/mfa", json={
        "mfa_session_token": mfa_token, "totp_code": codigo,
    })
    assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════
# EP-AUTH-03 — Refresh (POST /v1/auth/refresh)
# ══════════════════════════════════════════════════════════════════════

async def _obtener_refresh_cookie(client) -> str:
    """Helper: login + mfa completo → refresh_token cookie."""
    mfa_token, codigo = await _login_y_obtener_codigo_mfa(client)
    await client.post("/v1/auth/mfa", json={
        "mfa_session_token": mfa_token, "totp_code": codigo,
    })
    return client.cookies.get("refresh_token", "")


@pytest.mark.asyncio
async def test_auth03_refresh_valido_retorna_nuevo_access_token(app_client):
    """EP-AUTH-03: refresh_token válido → nuevo access_token + nuevo refresh_token."""
    refresh = await _obtener_refresh_cookie(app_client)
    assert refresh, "No se obtuvo refresh_token en el setup"

    r = await app_client.post("/v1/auth/refresh", cookies={"refresh_token": refresh})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "access_token" in data
    nuevo_refresh = r.cookies.get("refresh_token")
    assert nuevo_refresh is not None
    assert nuevo_refresh != refresh  # token rotado


@pytest.mark.asyncio
async def test_auth03_refresh_replay_retorna_401(app_client):
    """EP-AUTH-03: replay del mismo refresh_token → 401 (07 §2.3 Escenario 2)."""
    refresh = await _obtener_refresh_cookie(app_client)
    await app_client.post("/v1/auth/refresh", cookies={"refresh_token": refresh})
    # Segundo uso del token original → replay detectado
    r = await app_client.post("/v1/auth/refresh", cookies={"refresh_token": refresh})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth03_sin_cookie_retorna_401(app_client):
    """EP-AUTH-03: sin cookie refresh_token → 401."""
    r = await app_client.post("/v1/auth/refresh")
    assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════
# EP-AUTH-04 — Logout (POST /v1/auth/logout)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_auth04_logout_revoca_sesion(app_client):
    """EP-AUTH-04: logout revoca sesión y elimina cookie."""
    refresh = await _obtener_refresh_cookie(app_client)
    r = await app_client.post(
        "/v1/auth/logout",
        cookies={"refresh_token": refresh},
    )
    assert r.status_code == 200
    assert r.json()["data"]["mensaje"] == "Sesión cerrada correctamente"


@pytest.mark.asyncio
async def test_auth04_logout_sin_token_retorna_401(app_client):
    """EP-AUTH-04: sin Authorization Bearer → 401 (Todos autenticados)."""
    # Usamos headers= para reemplazar el Authorization del cliente por defecto
    r = await app_client.post(
        "/v1/auth/logout",
        headers={"Authorization": "Bearer token-invalido-para-forzar-401"},
    )
    assert r.status_code == 401


# ══════════════════════════════════════════════════════════════════════
# EP-ADM-01 — Listar parámetros (GET /v1/admin/parametros)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_adm01_lista_parametros(app_client):
    """EP-ADM-01: ADMINISTRADOR puede listar parámetros del sistema."""
    r = await app_client.get("/v1/admin/parametros")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "parametros" in data
    assert data["total"] > 0
    claves = [p["clave"] for p in data["parametros"]]
    assert "max_consultas_precio_sesion" in claves


@pytest.mark.asyncio
async def test_adm01_vendedor_no_autorizado(app_client):
    """EP-ADM-01: VENDEDOR → 403 (solo SUPERADMIN · ADMINISTRADOR)."""
    token = make_test_token(app_client._test_private_pem, "VENDEDOR")
    r = await app_client.get(
        "/v1/admin/parametros",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════════
# EP-ADM-02 — Actualizar parámetro (PATCH /v1/admin/parametros/{clave})
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_adm02_actualiza_parametro_existente(app_client):
    """EP-ADM-02: ADMINISTRADOR actualiza un parámetro existente."""
    r = await app_client.patch(
        "/v1/admin/parametros/max_consultas_precio_sesion",
        json={"valor": 5},
    )
    assert r.status_code == 200
    assert r.json()["data"]["valor"] == 5
    assert r.json()["data"]["cache_invalidado"] is True


@pytest.mark.asyncio
async def test_adm02_parametro_inexistente_retorna_404(app_client):
    """EP-ADM-02: clave no existente → 404."""
    r = await app_client.patch(
        "/v1/admin/parametros/parametro_que_no_existe",
        json={"valor": 99},
    )
    assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════
# EP-ADM-03 — Crear vehículo (POST /v1/admin/vehiculos)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_adm03_crea_vehiculo(app_client):
    """EP-ADM-03: ADMINISTRADOR crea vehículo → 201 con vehiculo_id."""
    r = await app_client.post("/v1/admin/vehiculos", json={
        "universo": "mototaxi", "modelo": "Bajaj RE", "año": 2021,
    })
    assert r.status_code == 201
    data = r.json()["data"]
    assert "vehiculo_id" in data
    assert data["universo"] == "mototaxi"
    assert data["modelo"] == "Bajaj RE"


@pytest.mark.asyncio
async def test_adm03_vendedor_puede_crear_vehiculo(app_client):
    """EP-ADM-03: VENDEDOR también puede crear vehículo (03 §6.6)."""
    token = make_test_token(app_client._test_private_pem, "VENDEDOR")
    r = await app_client.post(
        "/v1/admin/vehiculos",
        headers={"Authorization": f"Bearer {token}"},
        json={"universo": "motolineal", "modelo": "TVS Apache", "año": 2022},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_adm03_mecanico_no_autorizado(app_client):
    """EP-ADM-03: MECANICO_MASTER → 403 (no está en los roles autorizados)."""
    token = make_test_token(app_client._test_private_pem, "MECANICO_MASTER")
    r = await app_client.post(
        "/v1/admin/vehiculos",
        headers={"Authorization": f"Bearer {token}"},
        json={"universo": "mototaxi", "modelo": "Test", "año": 2020},
    )
    assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════════
# EP-ADM-04 — Crear mecánico (POST /v1/admin/mecanicos)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_adm04_crea_mecanico_master(app_client):
    """EP-ADM-04: ADMINISTRADOR crea mecánico MASTER → 201."""
    r = await app_client.post("/v1/admin/mecanicos", json={
        "usuario_id": "user-mec-001", "nivel": "MASTER",
    })
    assert r.status_code == 201
    data = r.json()["data"]
    assert "mecanico_id" in data
    assert data["nivel"] == "MASTER"
    assert data["disponible"] is True


@pytest.mark.asyncio
async def test_adm04_crea_mecanico_junior_con_supervisor(app_client):
    """EP-ADM-04: mecánico JUNIOR con supervisor_id opcional → 201."""
    r = await app_client.post("/v1/admin/mecanicos", json={
        "usuario_id": "user-mec-002", "nivel": "JUNIOR", "supervisor_id": "user-mec-001",
    })
    assert r.status_code == 201
    assert r.json()["data"]["supervisor_id"] == "user-mec-001"


@pytest.mark.asyncio
async def test_adm12_lista_mecanicos_disponibles_con_nombre(app_client):
    """EP-ADM-12: GET /v1/admin/mecanicos hace join real con usuario.nombre."""
    r = await app_client.post("/v1/admin/mecanicos", json={
        "usuario_id": "user-admin-seed", "nivel": "MASTER",
    })
    assert r.status_code == 201

    r = await app_client.get("/v1/admin/mecanicos")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total"] >= 1
    encontrado = next(m for m in data["mecanicos"] if m["usuario_id"] == "user-admin-seed")
    assert encontrado["nombre"] != "user-admin-seed"  # el seed sí existe → nombre real, no fallback
    assert encontrado["nivel"] == "MASTER"
    assert encontrado["disponible"] is True


@pytest.mark.asyncio
async def test_adm12_usuario_inexistente_hace_fallback_a_usuario_id(app_client):
    """EP-ADM-12: si el usuario_id no existe en el store, el nombre cae a usuario_id."""
    r = await app_client.post("/v1/admin/mecanicos", json={
        "usuario_id": "user-fantasma-999", "nivel": "JUNIOR",
    })
    assert r.status_code == 201

    r = await app_client.get("/v1/admin/mecanicos")
    encontrado = next(m for m in r.json()["data"]["mecanicos"] if m["usuario_id"] == "user-fantasma-999")
    assert encontrado["nombre"] == "user-fantasma-999"


@pytest.mark.asyncio
async def test_adm12_rbac_vendedor_bloqueado(app_client):
    """EP-ADM-12: VENDEDOR no puede listar mecánicos."""
    token = make_test_token(app_client._test_private_pem, "VENDEDOR")
    r = await app_client.get("/v1/admin/mecanicos", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_adm04_vendedor_no_autorizado(app_client):
    """EP-ADM-04: VENDEDOR → 403 (solo SUPERADMIN · ADMINISTRADOR)."""
    token = make_test_token(app_client._test_private_pem, "VENDEDOR")
    r = await app_client.post(
        "/v1/admin/mecanicos",
        headers={"Authorization": f"Bearer {token}"},
        json={"usuario_id": "u-x", "nivel": "JUNIOR"},
    )
    assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════════
# EP-ADM-05 — Crear usuario (POST /v1/admin/usuarios)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_adm05_crea_usuario_vendedor(app_client):
    """EP-ADM-05: ADMINISTRADOR crea usuario con rol VENDEDOR → 201."""
    r = await app_client.post("/v1/admin/usuarios", json={
        "email": "nueva_vendedor@test.com",
        "nombre": "María Vendedora",
        "rol": "VENDEDOR",
        "password": "pass_segura_123",
    })
    assert r.status_code == 201
    data = r.json()["data"]
    assert "usuario_id" in data
    assert data["rol"] == "VENDEDOR"
    assert "password" not in data  # nunca en respuesta


@pytest.mark.asyncio
async def test_adm05_no_puede_crear_superadmin(app_client):
    """EP-ADM-05: no puede crear SUPERADMIN (03 §6.6 regla explícita)."""
    r = await app_client.post("/v1/admin/usuarios", json={
        "email": "super@test.com",
        "nombre": "Intento Superadmin",
        "rol": "SUPERADMIN",
        "password": "pass_segura_123",
    })
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "VALIDACION_FALLIDA"


@pytest.mark.asyncio
async def test_adm05_email_duplicado_retorna_409(app_client):
    """EP-ADM-05: email ya registrado → 409."""
    r = await app_client.post("/v1/admin/usuarios", json={
        "email": "admin@tecnimotos.test",  # ya existe en InMemoryUserStore
        "nombre": "Duplicado",
        "rol": "VENDEDOR",
        "password": "pass_segura_123",
    })
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_adm05_cliente_no_puede_crear_usuarios(app_client):
    """EP-ADM-05: CLIENTE_* → 403."""
    token = make_test_token(app_client._test_private_pem, "CLIENTE_CONDUCTOR")
    r = await app_client.post(
        "/v1/admin/usuarios",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": "x@test.com", "nombre": "X", "rol": "VENDEDOR", "password": "pass123456"},
    )
    assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════════
# EP-ADM-12 — Impersonación (POST /v1/admin/impersonate)
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_impersonate_superadmin_exito(app_client):
    """EP-ADM-12: SUPERADMIN suplanta a cliente activo → 200 y token de impersonación."""
    # Crear usuario destino
    target_user = await app_client.app.state.user_store.crear_usuario(
        email="conductor_target@test.com",
        nombre="Conductor Target",
        rol="CLIENTE_CONDUCTOR",
        password="password123",
    )

    token_superadmin = make_test_token(app_client._test_private_pem, "SUPERADMIN", sub="admin-super")
    r = await app_client.post(
        "/v1/admin/impersonate",
        headers={"Authorization": f"Bearer {token_superadmin}"},
        json={"user_id": target_user.usuario_id},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["usuario_id"] == target_user.usuario_id
    assert data["user"]["rol"] == "CLIENTE_CONDUCTOR"

    # Verificar claims del token generado
    from api.auth import verify_token
    payload = verify_token(data["access_token"], app_client.app.state.jwt_public_key)
    assert payload["sub"] == target_user.usuario_id
    assert payload["rol"] == "CLIENTE_CONDUCTOR"
    assert payload["is_impersonated"] is True
    assert payload["auditor_id"] == "admin-super"


@pytest.mark.asyncio
async def test_impersonate_no_superadmin_forbidden(app_client):
    """EP-ADM-12: Rol distinto de SUPERADMIN (ej: ADMINISTRADOR) → 403."""
    target_user = await app_client.app.state.user_store.crear_usuario(
        email="conductor_forbidden@test.com",
        nombre="Conductor Forbidden",
        rol="CLIENTE_CONDUCTOR",
        password="password123",
    )

    # El token por defecto del app_client es ADMINISTRADOR
    r = await app_client.post(
        "/v1/admin/impersonate",
        json={"user_id": target_user.usuario_id},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_impersonate_usuario_inexistente_retorna_404(app_client):
    """EP-ADM-12: Usuario inexistente → 404."""
    token_superadmin = make_test_token(app_client._test_private_pem, "SUPERADMIN", sub="admin-super")
    r = await app_client.post(
        "/v1/admin/impersonate",
        headers={"Authorization": f"Bearer {token_superadmin}"},
        json={"user_id": "id-inexistente-123"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_impersonate_target_superadmin_prohibido(app_client):
    """EP-ADM-12: Intentar suplantar a otro SUPERADMIN → 403."""
    # Crear otro superadmin
    target_super = await app_client.app.state.user_store.crear_usuario(
        email="otro_super@test.com",
        nombre="Otro Super",
        rol="SUPERADMIN",
        password="password123",
    )

    token_superadmin = make_test_token(app_client._test_private_pem, "SUPERADMIN", sub="admin-super")
    r = await app_client.post(
        "/v1/admin/impersonate",
        headers={"Authorization": f"Bearer {token_superadmin}"},
        json={"user_id": target_super.usuario_id},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_impersonate_target_no_activo_prohibido(app_client):
    """EP-ADM-12: Intentar suplantar usuario con cuenta no activa → 403."""
    target_user = await app_client.app.state.user_store.crear_usuario(
        email="conductor_inactivo@test.com",
        nombre="Conductor Inactivo",
        rol="CLIENTE_CONDUCTOR",
        password="password123",
    )
    # Marcar no activo / pendiente
    target_user.estado_cuenta = "PENDIENTE_DOCUMENTOS"

    token_superadmin = make_test_token(app_client._test_private_pem, "SUPERADMIN", sub="admin-super")
    r = await app_client.post(
        "/v1/admin/impersonate",
        headers={"Authorization": f"Bearer {token_superadmin}"},
        json={"user_id": target_user.usuario_id},
    )
    assert r.status_code == 403

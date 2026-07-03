"""
Suite de tests de autenticación y RBAC (07 §2, §3.2).
Verifica: 401 sin token · 401 token inválido · 403 rol incorrecto · 200 rol correcto.
"""
from __future__ import annotations

import datetime
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import AsyncClient, ASGITransport
from jose import jwt as jose_jwt

from api.main import create_app


# ── Utilidades ────────────────────────────────────────────────────────────────

def _keypair() -> tuple[str, str]:
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv_pem, pub_pem


def _token(priv_pem: str, rol: str, *, expired: bool = False) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = datetime.timedelta(minutes=-5) if expired else datetime.timedelta(minutes=15)
    return jose_jwt.encode(
        {"sub": "u-test", "rol": rol, "iat": now, "exp": now + delta},
        priv_pem, algorithm="RS256",
    )


@pytest.fixture
async def auth_client():
    """Cliente con keypair de test — sin token por defecto (para tests de auth)."""
    priv_pem, pub_pem = _keypair()
    app = create_app()
    app.state.jwt_public_key = pub_pem
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.app = app
        client._priv = priv_pem
        yield client


_CREAR_BODY = {
    "codigo": "AUTH-001", "nombre": "Repuesto Auth",
    "universo": "mototaxi_3r", "modelo": "Bajaj RE",
    "año": 2021, "categoria": "motor", "precio_venta": "45.00",
}


# ── 07 §2 — JWT RS256 ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sin_token_retorna_401(auth_client):
    """07 §3.2: endpoint protegido sin token → 401 AUTENTICACION_REQUERIDA."""
    r = await auth_client.post("/v1/repuestos", json=_CREAR_BODY)
    assert r.status_code == 401
    assert r.json()["detail"]["error"]["code"] == "AUTENTICACION_REQUERIDA"


@pytest.mark.asyncio
async def test_token_malformado_retorna_401(auth_client):
    """07 §2: Bearer con string no-JWT → 401 TOKEN_INVALIDO."""
    r = await auth_client.post(
        "/v1/repuestos",
        headers={"Authorization": "Bearer not.a.jwt"},
        json=_CREAR_BODY,
    )
    assert r.status_code == 401
    assert r.json()["detail"]["error"]["code"] == "TOKEN_INVALIDO"


@pytest.mark.asyncio
async def test_token_expirado_retorna_401(auth_client):
    """07 §2.1: token expirado → 401 TOKEN_INVALIDO."""
    token = _token(auth_client._priv, "ADMINISTRADOR", expired=True)
    r = await auth_client.post(
        "/v1/repuestos",
        headers={"Authorization": f"Bearer {token}"},
        json=_CREAR_BODY,
    )
    assert r.status_code == 401
    assert r.json()["detail"]["error"]["code"] == "TOKEN_INVALIDO"


@pytest.mark.asyncio
async def test_firma_incorrecta_retorna_401(auth_client):
    """07 §2.5: token firmado con clave distinta → 401 (firma RS256 inválida)."""
    other_priv, _ = _keypair()  # clave privada diferente
    token = _token(other_priv, "ADMINISTRADOR")
    r = await auth_client.post(
        "/v1/repuestos",
        headers={"Authorization": f"Bearer {token}"},
        json=_CREAR_BODY,
    )
    assert r.status_code == 401
    assert r.json()["detail"]["error"]["code"] == "TOKEN_INVALIDO"


# ── 07 §3.2 — RBAC ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_vendedor_no_puede_crear_repuesto(auth_client):
    """07 §3.2: VENDEDOR intentando operación de ADMINISTRADOR → 403 ACCESO_DENEGADO."""
    token = _token(auth_client._priv, "VENDEDOR")
    r = await auth_client.post(
        "/v1/repuestos",
        headers={"Authorization": f"Bearer {token}"},
        json=_CREAR_BODY,
    )
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "ACCESO_DENEGADO"


@pytest.mark.asyncio
async def test_mecanico_master_no_puede_crear_repuesto(auth_client):
    """07 §3.2: MECANICO_MASTER no tiene acceso a gestión de catálogo → 403."""
    token = _token(auth_client._priv, "MECANICO_MASTER")
    r = await auth_client.post(
        "/v1/repuestos",
        headers={"Authorization": f"Bearer {token}"},
        json=_CREAR_BODY,
    )
    assert r.status_code == 403
    assert r.json()["detail"]["error"]["code"] == "ACCESO_DENEGADO"


@pytest.mark.asyncio
async def test_administrador_puede_crear_repuesto(auth_client):
    """07 §3.2: ADMINISTRADOR con token válido → 201."""
    token = _token(auth_client._priv, "ADMINISTRADOR")
    r = await auth_client.post(
        "/v1/repuestos",
        headers={"Authorization": f"Bearer {token}"},
        json={"codigo": "ADM-001", "nombre": "Bujía", "universo": "mototaxi_3r",
              "modelo": "Bajaj RE", "año": 2021, "categoria": "motor", "precio_venta": "18.00"},
    )
    assert r.status_code == 201
    assert r.json()["data"]["codigo"] == "ADM-001"


@pytest.mark.asyncio
async def test_superadmin_puede_crear_repuesto(auth_client):
    """07 §3.2: SUPERADMIN tiene acceso a todas las operaciones de ADMINISTRADOR."""
    token = _token(auth_client._priv, "SUPERADMIN")
    r = await auth_client.post(
        "/v1/repuestos",
        headers={"Authorization": f"Bearer {token}"},
        json={"codigo": "SA-001", "nombre": "Filtro", "universo": "motolineal",
              "modelo": "TVS Apache", "año": 2022, "categoria": "motor", "precio_venta": "35.00"},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_endpoint_publico_sin_token_funciona(auth_client):
    """Endpoints sin require_roles (GET catálogo) son accesibles sin token."""
    r = await auth_client.get("/v1/repuestos", params={"universo": "mototaxi_3r"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_vendedor_puede_ver_catalogo(auth_client):
    """VENDEDOR puede acceder a endpoints de lectura pública."""
    token = _token(auth_client._priv, "VENDEDOR")
    r = await auth_client.get(
        "/v1/repuestos",
        headers={"Authorization": f"Bearer {token}"},
        params={"universo": "mototaxi_3r"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_mecanico_master_puede_cerrar_ot(auth_client):
    """07 §3.2: MECANICO_MASTER puede cerrar OT."""
    from src.taller.domain.models.orden_trabajo import (
        EstadoOrdenTrabajo, ListaRepuestosOT, Mecanico,
        ModalidadIntervencion, NivelMecanico, NivelUrgencia, OrdenTrabajo, Vehiculo,
    )
    import decimal
    token = _token(auth_client._priv, "MECANICO_MASTER")
    repo = auth_client.app.state.taller_repo
    m = Mecanico(usuario_id="u-m", nivel=NivelMecanico.MASTER)
    await repo.guardar_mecanico(m)
    v = Vehiculo(universo="mototaxi", modelo="Bajaj RE", año=2021)
    await repo.guardar_vehiculo(v)
    ot = OrdenTrabajo(vehiculo_id=v.id, mecanico_master_id=m.id,
                      modalidad=ModalidadIntervencion.PREVENTIVO, urgencia=NivelUrgencia.BAJA)
    item = ListaRepuestosOT(orden_trabajo_id=ot.id, repuesto_id="rp-x", codigo="X",
                            cantidad=1, precio_unitario=decimal.Decimal("10.00"),
                            momento_agregado="inicial")
    ot.agregar_repuesto_inicial(item)
    ot.presentar_lista_al_cliente()  # ABIERTA → LISTA_REPUESTOS
    ot.aprobar_lista()               # LISTA_REPUESTOS → EN_EJECUCION
    ot.declarar_revision_final(decimal.Decimal("50.00"), m.id)
    ot.confirmar_cobro()
    await repo.guardar_ot(ot)
    r = await auth_client.post(
        f"/v1/ordenes-trabajo/{ot.id}/cerrar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200

"""Fixtures compartidos para todos los tests de integración."""
from __future__ import annotations

import datetime
import decimal
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import AsyncClient, ASGITransport
from jose import jwt as jose_jwt

from api.main import create_app
from src.pedidos.domain.ports.catalogo_pedidos_port import RepuestoInfo
from src.taller.domain.models.orden_trabajo import Mecanico, NivelMecanico, Vehiculo
from src.taller.domain.ports.catalogo_taller_port import RepuestoInfoTaller


def _generate_test_keypair() -> tuple[str, str]:
    """Genera par RS256 en memoria para tests — no persiste en disco."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem


def make_test_token(private_pem: str, rol: str, sub: str = "test-user") -> str:
    """Genera JWT RS256 válido con rol y sub dados."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return jose_jwt.encode(
        {
            "sub": sub,
            "rol": rol,
            "iat": now,
            "exp": now + datetime.timedelta(minutes=15),
        },
        private_pem,
        algorithm="RS256",
    )


@pytest.fixture
async def app_client():
    """
    AsyncClient contra la app FastAPI con repositorios en memoria.
    Inyecta por defecto un token ADMINISTRADOR válido (07 §3.2).
    Para tests de roles distintos usar app_client._test_private_pem con make_test_token.
    """
    private_pem, public_pem = _generate_test_keypair()
    app = create_app()
    app.state.jwt_public_key = public_pem
    app.state.jwt_private_key = private_pem
    admin_token = make_test_token(private_pem, "ADMINISTRADOR")
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        client.app = app
        client.headers.update({"Authorization": f"Bearer {admin_token}"})
        client._test_private_pem = private_pem
        yield client


@pytest.fixture
async def pedidos_client(app_client):
    """Cliente con datos precargados para tests de pedidos."""
    catalogo_adapter = app_client.app.state.catalogo_adapter
    stock_adapter = app_client.app.state.stock_adapter

    catalogo_adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id="rp-001", codigo="REP-001", precio_venta=decimal.Decimal("45.00"),
        nombre="Filtro aceite", categoria="motor", universo="mototaxi_3r", activo=True,
    ))
    catalogo_adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id="rp-002", codigo="REP-002", precio_venta=decimal.Decimal("30.00"),
        nombre="Cadena", categoria="transmision", universo="motolineal", activo=True,
    ))
    catalogo_adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id="rp-baja", codigo="REP-BAJA", precio_venta=decimal.Decimal("20.00"),
        nombre="Repuesto baja", categoria="otro", universo="mototaxi_3r", activo=False,
    ))
    stock_adapter.establecer_stock("rp-001", 20)
    stock_adapter.establecer_stock("rp-002", 10)
    return app_client


@pytest.fixture
async def taller_client(app_client):
    """Cliente con vehículo y mecánico precargados."""
    repo = app_client.app.state.taller_repo
    catalogo = app_client.app.state.catalogo_taller_adapter

    v = Vehiculo(universo="mototaxi", modelo="Bajaj RE", año=2021)
    await repo.guardar_vehiculo(v)
    m = Mecanico(usuario_id="u-master", nivel=NivelMecanico.MASTER)
    await repo.guardar_mecanico(m)

    catalogo.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-001", codigo="REP-001",
        precio_venta=decimal.Decimal("25.00"), nombre="Bujía", activo=True,
    ))
    catalogo.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-medio", codigo="REP-MEDIO",
        precio_venta=decimal.Decimal("65.00"), nombre="Rodamiento", activo=True,
    ))
    catalogo.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-caro", codigo="REP-CARO",
        precio_venta=decimal.Decimal("150.00"), nombre="Sensor ABS", activo=True,
    ))

    app_client._vehiculo_id = v.id
    app_client._mecanico_id = m.id
    return app_client

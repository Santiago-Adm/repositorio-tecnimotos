"""
Fixtures E2E — extiende el patrón de tests/integration/conftest.py
con datos más completos para flujos de usuario de extremo a extremo (04 §7).
"""
from __future__ import annotations

import datetime
import decimal

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt as jose_jwt

from api.main import create_app
from src.pedidos.domain.ports.catalogo_pedidos_port import RepuestoInfo
from src.taller.domain.models.orden_trabajo import Mecanico, NivelMecanico, Vehiculo
from src.taller.domain.ports.catalogo_taller_port import RepuestoInfoTaller


def _generate_keypair() -> tuple[str, str]:
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


def make_token(private_pem: str, rol: str, sub: str = "e2e-user") -> str:
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
async def e2e_app():
    """
    App FastAPI con estado completo precargado para los 3 flujos E2E (04 §7.1).
    Repositorios en memoria — sin BD real.
    """
    private_pem, public_pem = _generate_keypair()
    app = create_app()
    app.state.jwt_public_key = public_pem
    app.state.jwt_private_key = private_pem

    # ── Datos catálogo ────────────────────────────────────────────────────────
    from src.catalogo.domain.models.repuesto import (
        CategoriaRepuesto,
        Repuesto,
        UniversoRepuesto,
    )

    catalogo_repo = app.state.catalogo_repo
    rep_filtro = Repuesto(
        codigo="REP-001",
        nombre="Filtro aceite",
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=decimal.Decimal("45.00"),
        universo=UniversoRepuesto.MOTOTAXI,
        modelo="Universal",
        año=2020,
    )
    rep_cadena = Repuesto(
        codigo="REP-002",
        nombre="Cadena transmisión",
        categoria=CategoriaRepuesto.TRANSMISION,
        precio_venta=decimal.Decimal("80.00"),
        universo=UniversoRepuesto.MOTOLINEAL,
        modelo="Universal",
        año=2020,
    )
    await catalogo_repo.guardar(rep_filtro)
    await catalogo_repo.guardar(rep_cadena)

    # ── Datos stock ───────────────────────────────────────────────────────────
    from src.stock.domain.models.stock import StockRepuesto

    stock_repo = app.state.stock_repo
    st_filtro = StockRepuesto(
        repuesto_id=rep_filtro.id,
        codigo="REP-001",
        cantidad_disponible=50,
        umbral_minimo=5,
    )
    st_cadena = StockRepuesto(
        repuesto_id=rep_cadena.id,
        codigo="REP-002",
        cantidad_disponible=20,
        umbral_minimo=3,
    )
    await stock_repo.guardar(st_filtro)
    await stock_repo.guardar(st_cadena)

    # Adapters de pedidos y taller usan RepuestoInfo/RepuestoInfoTaller
    catalogo_adapter = app.state.catalogo_adapter
    catalogo_adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id=rep_filtro.id,
        codigo="REP-001",
        precio_venta=decimal.Decimal("45.00"),
        nombre="Filtro aceite",
        categoria="motor",
        universo="mototaxi",
        activo=True,
    ))
    catalogo_adapter.agregar_repuesto(RepuestoInfo(
        repuesto_id=rep_cadena.id,
        codigo="REP-002",
        precio_venta=decimal.Decimal("80.00"),
        nombre="Cadena transmisión",
        categoria="transmision",
        universo="motolineal",
        activo=True,
    ))

    stock_adapter = app.state.stock_adapter
    stock_adapter.establecer_stock(rep_filtro.id, 50)
    stock_adapter.establecer_stock(rep_cadena.id, 20)

    # ── Datos taller ──────────────────────────────────────────────────────────
    taller_repo = app.state.taller_repo
    vehiculo = Vehiculo(universo="mototaxi", modelo="Bajaj RE 205", año=2022)
    mecanico = Mecanico(usuario_id="u-master-e2e", nivel=NivelMecanico.MASTER)
    await taller_repo.guardar_vehiculo(vehiculo)
    await taller_repo.guardar_mecanico(mecanico)

    catalogo_taller = app.state.catalogo_taller_adapter
    # Taller adapter usa precio < S/30 para flujo automático sin espera tácita
    catalogo_taller.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id=rep_filtro.id,
        codigo="REP-001",
        precio_venta=decimal.Decimal("25.00"),
        nombre="Filtro aceite",
        activo=True,
    ))
    catalogo_taller.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id=rep_cadena.id,
        codigo="REP-002",
        precio_venta=decimal.Decimal("25.00"),
        nombre="Cadena transmisión",
        activo=True,
    ))

    app._e2e_private_pem = private_pem
    app._e2e_vehiculo_id = vehiculo.id
    app._e2e_mecanico_id = mecanico.id
    app._e2e_rep_filtro_id = rep_filtro.id
    app._e2e_rep_cadena_id = rep_cadena.id

    return app


@pytest.fixture
async def client_conductor(e2e_app):
    """Cliente HTTP con rol CLIENTE_CONDUCTOR."""
    token = make_token(e2e_app._e2e_private_pem, "CLIENTE_CONDUCTOR", "u-cliente-e2e")
    async with AsyncClient(
        transport=ASGITransport(app=e2e_app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        c.app = e2e_app
        yield c


@pytest.fixture
async def client_vendedor(e2e_app):
    """Cliente HTTP con rol VENDEDOR."""
    token = make_token(e2e_app._e2e_private_pem, "VENDEDOR", "u-vendedor-e2e")
    async with AsyncClient(
        transport=ASGITransport(app=e2e_app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        c.app = e2e_app
        yield c


@pytest.fixture
async def client_mecanico(e2e_app):
    """Cliente HTTP con rol MECANICO_MASTER."""
    token = make_token(e2e_app._e2e_private_pem, "MECANICO_MASTER", "u-mecanico-e2e")
    async with AsyncClient(
        transport=ASGITransport(app=e2e_app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        c.app = e2e_app
        yield c


@pytest.fixture
async def client_distrito(e2e_app):
    """Cliente HTTP con rol CLIENTE_DISTRITO."""
    token = make_token(e2e_app._e2e_private_pem, "CLIENTE_DISTRITO", "u-distrito-e2e")
    async with AsyncClient(
        transport=ASGITransport(app=e2e_app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        c.app = e2e_app
        yield c


@pytest.fixture
async def client_admin(e2e_app):
    """Cliente HTTP con rol ADMINISTRADOR."""
    token = make_token(e2e_app._e2e_private_pem, "ADMINISTRADOR", "u-admin-e2e")
    async with AsyncClient(
        transport=ASGITransport(app=e2e_app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as c:
        c.app = e2e_app
        yield c

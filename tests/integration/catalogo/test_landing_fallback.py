"""
Tests de integración — fallback aleatorio de EP-CAT-01 y EP-CAT-17 (modelos),
Pieza A/B sesión 2026-07-03.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.catalogo.domain.models.repuesto import Repuesto, UniversoRepuesto


@pytest.fixture
async def repuestos_mixtos(app_client):
    repo = app_client.app.state.catalogo_repo
    destacado = Repuesto(
        codigo="FALLBACK-DEST-001", nombre="Destacado real", universo=UniversoRepuesto.MOTOLINEAL,
        modelo="Modelo A", año=2022, categoria="motor",
        precio_venta=Decimal("50.00"), destacado=True,
    )
    normales = [
        Repuesto(
            codigo=f"FALLBACK-NORM-{i:03d}", nombre=f"Normal {i}", universo=UniversoRepuesto.MOTOLINEAL,
            modelo="Modelo B", año=2022, categoria="motor", precio_venta=Decimal("30.00"),
        )
        for i in range(5)
    ]
    await repo.guardar(destacado)
    for r in normales:
        await repo.guardar(r)
    return destacado, normales


class TestFallbackAleatorio:
    async def test_sin_completar_aleatorio_devuelve_solo_destacados(self, app_client, repuestos_mixtos):
        r = await app_client.get("/v1/repuestos?universo=motolineal&destacado=true&limit=12")
        codigos = [x["codigo"] for x in r.json()["data"]["repuestos"]]
        assert codigos == ["FALLBACK-DEST-001"]

    async def test_completar_aleatorio_rellena_hasta_limit(self, app_client, repuestos_mixtos):
        r = await app_client.get(
            "/v1/repuestos?universo=motolineal&destacado=true&limit=4&completar_aleatorio=true"
        )
        data = r.json()["data"]["repuestos"]
        assert len(data) == 4
        codigos = [x["codigo"] for x in data]
        assert "FALLBACK-DEST-001" in codigos
        # el resto son de relleno, sin duplicados
        assert len(set(codigos)) == 4

    async def test_completar_aleatorio_nunca_excede_catalogo_disponible(self, app_client, repuestos_mixtos):
        r = await app_client.get(
            "/v1/repuestos?universo=motolineal&destacado=true&limit=100&completar_aleatorio=true"
        )
        data = r.json()["data"]["repuestos"]
        assert len(data) == 6  # 1 destacado + 5 normales, total real del universo


class TestListarModelos:
    async def test_lista_modelos_distintos(self, app_client, repuestos_mixtos):
        r = await app_client.get("/v1/repuestos/modelos?universo=motolineal")
        assert r.status_code == 200
        modelos = r.json()["data"]["modelos"]
        assert "Modelo A" in modelos
        assert "Modelo B" in modelos
        assert len(modelos) == len(set(modelos))

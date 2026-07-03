"""
Tests de integración — campo `destacado` (PIEZA D, sesión 2026-07-03).
Selección editorial manual para la landing pública: EP-CAT-01 filtra por
destacado=true/false, EP-CAT-10 permite marcarlo/desmarcarlo.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    UniversoRepuesto,
)


@pytest.fixture
async def repo_con_destacados(app_client):
    repo = app_client.app.state.catalogo_repo
    destacado = Repuesto(
        codigo="DEST-001", nombre="Repuesto destacado", universo=UniversoRepuesto.MOTOLINEAL,
        modelo="TVS Apache", año=2022, categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("50.00"), destacado=True,
    )
    normal = Repuesto(
        codigo="DEST-002", nombre="Repuesto normal", universo=UniversoRepuesto.MOTOLINEAL,
        modelo="TVS Apache", año=2022, categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("50.00"), destacado=False,
    )
    await repo.guardar(destacado)
    await repo.guardar(normal)
    return repo


class TestDestacadoDominio:

    def test_repuesto_nace_no_destacado_por_defecto(self):
        r = Repuesto(
            codigo="X", nombre="X", universo=UniversoRepuesto.MOTOLINEAL,
            modelo="X", año=2020, categoria=CategoriaRepuesto.MOTOR,
            precio_venta=Decimal("10.00"),
        )
        assert r.destacado is False

    def test_marcar_destacado_actualiza_flag_y_timestamp(self):
        r = Repuesto(
            codigo="X", nombre="X", universo=UniversoRepuesto.MOTOLINEAL,
            modelo="X", año=2020, categoria=CategoriaRepuesto.MOTOR,
            precio_venta=Decimal("10.00"),
        )
        antes = r.updated_at
        r.marcar_destacado(True)
        assert r.destacado is True
        assert r.updated_at >= antes


class TestDestacadoEP_CAT_01:

    async def test_filtra_solo_destacados(self, app_client, repo_con_destacados):
        r = await app_client.get("/v1/repuestos?universo=motolineal&destacado=true")
        codigos = [x["codigo"] for x in r.json()["data"]["repuestos"]]
        assert "DEST-001" in codigos
        assert "DEST-002" not in codigos

    async def test_sin_filtro_devuelve_todos(self, app_client, repo_con_destacados):
        r = await app_client.get("/v1/repuestos?universo=motolineal")
        codigos = [x["codigo"] for x in r.json()["data"]["repuestos"]]
        assert "DEST-001" in codigos
        assert "DEST-002" in codigos

    async def test_response_incluye_campo_destacado(self, app_client, repo_con_destacados):
        r = await app_client.get("/v1/repuestos?universo=motolineal&destacado=true")
        item = r.json()["data"]["repuestos"][0]
        assert item["destacado"] is True


class TestDestacadoEP_CAT_10:

    async def test_admin_marca_destacado_via_patch(self, app_client, repo_con_destacados):
        """app_client ya trae token ADMINISTRADOR por defecto (ver tests/integration/conftest.py)."""
        r = await app_client.patch("/v1/repuestos/DEST-002", json={"destacado": True})
        assert r.status_code == 200
        assert r.json()["data"]["destacado"] is True

        detalle = await app_client.get("/v1/repuestos/DEST-002")
        assert detalle.json()["data"]["destacado"] is True

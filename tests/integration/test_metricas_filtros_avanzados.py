"""
Tests de integración — filtros avanzados reales de EP-ADM-10 (Pieza 1, panel BI):
categoria/universo acotan repuestos_bajo_umbral, mecanico_id acota ots_activas.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.catalogo.domain.models.repuesto import Repuesto, UniversoRepuesto
from src.stock.domain.models.stock import StockRepuesto
from src.taller.domain.models.orden_trabajo import ModalidadIntervencion, NivelUrgencia, OrdenTrabajo


@pytest.fixture
async def datos_filtro_categoria(app_client):
    catalogo_repo = app_client.app.state.catalogo_repo
    stock_repo = app_client.app.state.stock_repo

    rep_motor = Repuesto(
        codigo="FILTRO-MOTOR-001", nombre="X", universo=UniversoRepuesto.MOTOLINEAL,
        modelo="X", año=2020, categoria="motor", precio_venta=Decimal("10.00"),
    )
    rep_frenos = Repuesto(
        codigo="FILTRO-FRENOS-001", nombre="Y", universo=UniversoRepuesto.MOTOLINEAL,
        modelo="X", año=2020, categoria="frenos", precio_venta=Decimal("10.00"),
    )
    await catalogo_repo.guardar(rep_motor)
    await catalogo_repo.guardar(rep_frenos)

    for rep in (rep_motor, rep_frenos):
        s = StockRepuesto(repuesto_id=rep.id, codigo=rep.codigo)
        s.ajustar_umbral(10)
        s.cantidad_disponible = 1  # bajo umbral en ambos
        await stock_repo.guardar(s)

    return rep_motor, rep_frenos


class TestFiltroCategoriaUniverso:
    async def test_sin_filtro_cuenta_ambos(self, app_client, datos_filtro_categoria):
        r = await app_client.get("/v1/admin/metricas-negocio")
        assert r.json()["data"]["repuestos_bajo_umbral"] >= 2

    async def test_filtro_categoria_motor_excluye_frenos(self, app_client, datos_filtro_categoria):
        r = await app_client.get("/v1/admin/metricas-negocio?categoria=motor")
        data = r.json()["data"]
        assert data["repuestos_bajo_umbral"] == 1

    async def test_filtro_universo_motolineal_incluye_ambos(self, app_client, datos_filtro_categoria):
        r = await app_client.get("/v1/admin/metricas-negocio?universo=motolineal")
        assert r.json()["data"]["repuestos_bajo_umbral"] >= 2

    async def test_filtro_universo_mototaxi_excluye_motolineal(self, app_client, datos_filtro_categoria):
        r = await app_client.get("/v1/admin/metricas-negocio?universo=mototaxi_3r")
        # los repuestos del fixture son motolineal — no deben contar aquí
        assert r.json()["data"]["repuestos_bajo_umbral"] == 0


class TestFiltroMecanico:
    async def test_filtro_mecanico_acota_ots_activas(self, app_client):
        repo = app_client.app.state.taller_repo
        ot_mec1 = OrdenTrabajo(
            vehiculo_id="v-1", mecanico_master_id="mec-filtro-1",
            modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
        )
        ot_mec2 = OrdenTrabajo(
            vehiculo_id="v-2", mecanico_master_id="mec-filtro-2",
            modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
        )
        await repo.guardar_ot(ot_mec1)
        await repo.guardar_ot(ot_mec2)

        r = await app_client.get("/v1/admin/metricas-negocio?mecanico_id=mec-filtro-1")
        assert r.json()["data"]["ots_activas"] == 1

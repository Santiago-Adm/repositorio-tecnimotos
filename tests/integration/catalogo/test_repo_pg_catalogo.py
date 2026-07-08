"""
Tests de integración — RepuestoRepositoryPG contra PostgreSQL real.
Se salta automáticamente si PostgreSQL no está disponible.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    UniversoRepuesto,
)
from src.catalogo.infrastructure.repositories.repuesto_repository_pg import RepuestoRepositoryPG
from tests.integration.conftest_pg import pg_session


@pytest.fixture
async def repo(pg_session):
    return RepuestoRepositoryPG(pg_session)


def _make_repuesto(suffix: str = "") -> Repuesto:
    return Repuesto(
        codigo=f"PG-CAT-{uuid.uuid4().hex[:8].upper()}{suffix}",
        nombre=f"Repuesto PG {uuid.uuid4().hex[:4]}",
        universo=UniversoRepuesto.MOTOTAXI_3R,
        modelo="Bajaj RE",
        año=2022,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("45.00"),
    )


class TestRepuestoRepositoryPG:

    async def test_guardar_y_obtener_por_codigo(self, repo, pg_session):
        rep = _make_repuesto()
        saved = await repo.guardar(rep)
        assert saved.id == rep.id

        obtenido = await repo.obtener_por_codigo(rep.codigo)
        assert obtenido is not None
        assert obtenido.nombre == rep.nombre
        assert obtenido.precio_venta == Decimal("45.00")

    async def test_obtener_por_id(self, repo, pg_session):
        rep = _make_repuesto()
        await repo.guardar(rep)

        obtenido = await repo.obtener_por_id(rep.id)
        assert obtenido is not None
        assert obtenido.codigo == rep.codigo

    async def test_buscar_por_universo(self, repo, pg_session):
        rep = _make_repuesto()
        await repo.guardar(rep)

        resultados = await repo.buscar(universo=UniversoRepuesto.MOTOTAXI_3R)
        codigos = [r.codigo for r in resultados]
        assert rep.codigo in codigos

    async def test_actualizar_precio(self, repo, pg_session):
        rep = _make_repuesto()
        await repo.guardar(rep)

        rep.actualizar_precio(Decimal("60.00"), modificado_por="test-actor")
        await repo.actualizar(rep)

        actualizado = await repo.obtener_por_id(rep.id)
        assert actualizado.precio_venta == Decimal("60.00")
        # historial_precio no se carga en obtener_por_id — usar obtener_historial_precio
        historial = await repo.obtener_historial_precio(rep.id)
        assert len(historial) == 1
        assert historial[0].precio_nuevo == Decimal("60.00")

    async def test_buscar_por_lista_codigos(self, repo, pg_session):
        rep1 = _make_repuesto("A")
        rep2 = _make_repuesto("B")
        await repo.guardar(rep1)
        await repo.guardar(rep2)

        resultados = await repo.buscar_por_lista_codigos([rep1.codigo, rep2.codigo])
        codigos = {r.codigo for r in resultados}
        assert rep1.codigo in codigos
        assert rep2.codigo in codigos

    async def test_buscar_por_q_matchea_nombre_o_codigo(self, repo, pg_session):
        rep = _make_repuesto()
        await repo.guardar(rep)

        por_nombre = await repo.buscar(universo=UniversoRepuesto.MOTOTAXI_3R, q=rep.nombre[:8])
        assert rep.codigo in [r.codigo for r in por_nombre]

        por_codigo = await repo.buscar(universo=UniversoRepuesto.MOTOTAXI_3R, q=rep.codigo[-6:].lower())
        assert rep.codigo in [r.codigo for r in por_codigo]

        sin_match = await repo.buscar(universo=UniversoRepuesto.MOTOTAXI_3R, q="zzz-no-existe-zzz")
        assert rep.codigo not in [r.codigo for r in sin_match]

    async def test_repuesto_inactivo_no_en_busqueda(self, repo, pg_session):
        rep = _make_repuesto()
        await repo.guardar(rep)

        rep.activo = False
        await repo.actualizar(rep)

        resultados = await repo.buscar(universo=UniversoRepuesto.MOTOTAXI_3R, solo_disponibles=True)
        codigos = [r.codigo for r in resultados]
        assert rep.codigo not in codigos

"""
Tests de integración — CatalogoTallerAdapterPG contra PostgreSQL real.
Se salta automáticamente si PostgreSQL no está disponible.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel
from src.taller.domain.models.orden_trabajo import DomainError
from src.taller.infrastructure.adapters.catalogo_taller_adapter_pg import CatalogoTallerAdapterPG
from tests.integration.conftest_pg import pg_session


class TestCatalogoTallerAdapterPG:

    async def test_obtener_precio_para_ot_encontrado(self, pg_session):
        codigo = f"TEST-TALPG-{uuid.uuid4().hex[:8]}"
        modelo = RepuestoModel(
            id=str(uuid.uuid4()), codigo=codigo, nombre="Repuesto test taller PG",
            universo="mototaxi_3r", modelo="Universal", categoria="motor",
            precio_venta=Decimal("40.00"), activo=True,
        )
        pg_session.add(modelo)
        await pg_session.flush()

        adapter = CatalogoTallerAdapterPG(pg_session)
        info = await adapter.obtener_precio_para_ot(codigo)
        assert info.codigo == codigo
        assert info.precio_venta == Decimal("40.00")
        assert info.repuesto_id == modelo.id

    async def test_obtener_precio_para_ot_no_encontrado_lanza_domain_error(self, pg_session):
        adapter = CatalogoTallerAdapterPG(pg_session)
        with pytest.raises(DomainError):
            await adapter.obtener_precio_para_ot("CODIGO-QUE-NO-EXISTE-XYZ")

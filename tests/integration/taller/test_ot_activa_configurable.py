"""
Tests de integración — ADR-015: "OT activa" configurable (estado + días) y
GET /v1/ordenes-trabajo (listado, antes inexistente).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.taller.domain.models.orden_trabajo import (
    EstadoOrdenTrabajo, ModalidadIntervencion, NivelUrgencia, OrdenTrabajo,
)
from tests.integration.conftest import make_test_token


@pytest.fixture
async def ots_variadas(app_client):
    repo = app_client.app.state.taller_repo
    ahora = datetime.now(timezone.utc)

    reciente_abierta = OrdenTrabajo(
        vehiculo_id="v-1", mecanico_master_id="mec-1",
        modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
        created_at=ahora,
    )
    vieja_abierta = OrdenTrabajo(
        vehiculo_id="v-2", mecanico_master_id="mec-2",
        modalidad=ModalidadIntervencion.PREVENTIVO, urgencia=NivelUrgencia.BAJA,
        created_at=ahora - timedelta(days=30),
    )
    cerrada = OrdenTrabajo(
        vehiculo_id="v-3", mecanico_master_id="mec-1",
        modalidad=ModalidadIntervencion.DIAGNOSTICO, urgencia=NivelUrgencia.MEDIA,
        created_at=ahora, estado=EstadoOrdenTrabajo.CERRADA,
    )
    for ot in (reciente_abierta, vieja_abierta, cerrada):
        await repo.guardar_ot(ot)
    return reciente_abierta, vieja_abierta, cerrada


class TestListarOrdenesTrabajo:
    async def test_lista_todas_sin_filtro(self, app_client, ots_variadas):
        token = make_test_token(app_client._test_private_pem, "MECANICO_MASTER")
        r = await app_client.get(
            "/v1/ordenes-trabajo", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 200
        assert r.json()["data"]["total"] == 3

    async def test_filtra_por_estado(self, app_client, ots_variadas):
        token = make_test_token(app_client._test_private_pem, "MECANICO_MASTER")
        r = await app_client.get(
            "/v1/ordenes-trabajo?estado=CERRADA", headers={"Authorization": f"Bearer {token}"}
        )
        data = r.json()["data"]
        assert data["total"] == 1
        assert data["ordenes_trabajo"][0]["estado"] == "CERRADA"

    async def test_filtra_por_mecanico(self, app_client, ots_variadas):
        token = make_test_token(app_client._test_private_pem, "MECANICO_MASTER")
        r = await app_client.get(
            "/v1/ordenes-trabajo?mecanico_id=mec-1", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.json()["data"]["total"] == 2

    async def test_filtra_por_activa_usa_regla_configurable(self, app_client, ots_variadas):
        """Default: ABIERTA cuenta como activa solo si <= 7 días abierta (ADR-015)."""
        token = make_test_token(app_client._test_private_pem, "MECANICO_MASTER")
        r = await app_client.get(
            "/v1/ordenes-trabajo?activa=true", headers={"Authorization": f"Bearer {token}"}
        )
        data = r.json()["data"]
        assert data["total"] == 1  # solo la reciente — la vieja (30 días) y la cerrada quedan fuera

    async def test_cambiar_dias_maximo_cambia_resultado_activa(self, app_client, ots_variadas):
        """Cambiar el parámetro configurable cambia el resultado sin tocar código (ADR-015)."""
        token = make_test_token(app_client._test_private_pem, "SUPERADMIN")
        await app_client.patch(
            "/v1/admin/parametros/taller.ot_activa.dias_maximo",
            json={"valor": 60},
            headers={"Authorization": f"Bearer {token}"},
        )
        r = await app_client.get(
            "/v1/ordenes-trabajo?activa=true", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.json()["data"]["total"] == 2  # ahora la de 30 días también cuenta

    async def test_cliente_no_puede_listar(self, app_client):
        """INTERNO_ROLES incluye VENDEDOR/MECANICO_*/ADMIN_ROLES por diseño
        (api/auth.py) — el rol bloqueado real es un CLIENTE_*, no VENDEDOR."""
        token = make_test_token(app_client._test_private_pem, "CLIENTE_CONDUCTOR")
        r = await app_client.get(
            "/v1/ordenes-trabajo", headers={"Authorization": f"Bearer {token}"}
        )
        assert r.status_code == 403


class TestMetricasNegocioConRangoLibre:
    async def test_metricas_acepta_rango_de_fechas_libre(self, app_client):
        from decimal import Decimal
        from src.pedidos.domain.models.pedido import Comprobante, TipoComprobante

        repo = app_client.app.state.pedidos_repo
        comp_viejo = Comprobante(
            pedido_id="p-old", monto=Decimal("999.00"),
            tipo=TipoComprobante.BOLETA, emitido_por="user-admin-seed",
        )
        comp_viejo.aprobar()
        comp_viejo.created_at = datetime(2020, 1, 15, tzinfo=timezone.utc)
        await repo.guardar_comprobante(comp_viejo)

        r = await app_client.get(
            "/v1/admin/metricas-negocio?desde=2020-01-01&hasta=2020-01-31"
        )
        assert r.status_code == 200
        assert r.json()["data"]["comprobantes_emitidos_periodo"] == 999.0
        assert r.json()["data"]["periodo_comprobantes"]["desde"] == "2020-01-01"

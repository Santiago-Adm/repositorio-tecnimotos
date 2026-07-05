"""
Tests de integración — API de taller (EP-TAL-01 a EP-TAL-12).
"""
import pytest
from decimal import Decimal

from tests.integration.conftest import make_test_token


class TestEPTAL01AbrirOT:
    async def test_abrir_ot(self, taller_client):
        response = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["estado"] == "ABIERTA"
        assert "ot_id" in data

    async def test_abrir_ot_vehiculo_inexistente(self, taller_client):
        response = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": "v-99999",
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "baja",
            },
        )
        assert response.status_code == 404

    async def test_evento_abierta_publicado(self, taller_client):
        await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "media",
            },
        )
        bus = taller_client.app.state.event_bus
        assert bus.fue_publicado("orden_trabajo.abierta")


class TestEPTAL02AgregarRepuesto:
    @pytest.fixture
    async def ot_id(self, taller_client) -> str:
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        return r.json()["data"]["ot_id"]

    async def test_agregar_repuesto_en_abierta(self, taller_client, ot_id):
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_id}/repuestos",
            json={"codigo": "REP-001", "cantidad": 2},
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert len(data["lista_repuestos"]) == 1

    async def test_agregar_repuesto_ot_inexistente(self, taller_client):
        response = await taller_client.post(
            "/v1/ordenes-trabajo/id-99999/repuestos",
            json={"codigo": "REP-001", "cantidad": 1},
        )
        assert response.status_code == 404


class TestEPTAL03AprobarLista:
    @pytest.fixture
    async def ot_con_repuesto(self, taller_client) -> str:
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_id}/repuestos",
            json={"codigo": "REP-001", "cantidad": 1},
        )
        return ot_id

    async def test_aprobar_lista(self, taller_client, ot_con_repuesto):
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_con_repuesto}/aprobar-lista"
        )
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "EN_EJECUCION"

    async def test_aprobar_lista_sin_repuestos_falla(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "baja",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        response = await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
        assert response.status_code == 422

    async def test_aprobar_lista_ot_inexistente(self, taller_client):
        response = await taller_client.post("/v1/ordenes-trabajo/id-99999/aprobar-lista")
        assert response.status_code == 404

    async def test_evento_lista_aprobada_publicado(self, taller_client, ot_con_repuesto):
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_con_repuesto}/aprobar-lista")
        bus = taller_client.app.state.event_bus
        assert bus.fue_publicado("orden_trabajo.lista_aprobada")


class TestEPTAL04ConfirmarAdicional:
    async def test_confirmar_adicional(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/repuestos", json={"codigo": "REP-001", "cantidad": 1})
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
        agregar = await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/repuestos", json={"codigo": "REP-CARO", "cantidad": 1})
        ot_data = agregar.json()["data"]
        item_id = next(i["item_id"] for i in ot_data["lista_repuestos"] if i["codigo"] == "REP-CARO")

        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_id}/confirmar-adicional",
            json={"item_id": item_id},
        )
        assert response.status_code == 200

    async def test_confirmar_adicional_ot_inexistente(self, taller_client):
        response = await taller_client.post(
            "/v1/ordenes-trabajo/id-99999/confirmar-adicional",
            json={"item_id": "item-1"},
        )
        assert response.status_code == 404


class TestEPTAL05AutorizarPrecio:
    async def test_autorizar_precio(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "baja",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_id}/autorizar-precio",
            json={"cliente_id": "cli-001"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["visibilidad_precio_cliente"] is True

    async def test_autorizar_precio_ot_inexistente(self, taller_client):
        response = await taller_client.post(
            "/v1/ordenes-trabajo/id-99999/autorizar-precio",
            json={"cliente_id": "cli-001"},
        )
        assert response.status_code == 404


class TestEPTAL06RevisionFinal:
    @pytest.fixture
    async def ot_en_ejecucion(self, taller_client) -> str:
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/repuestos", json={"codigo": "REP-001", "cantidad": 1})
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
        return ot_id

    async def test_revision_final(self, taller_client, ot_en_ejecucion):
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_en_ejecucion}/revision-final",
            json={"costo_mano_obra": "80.00"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "REVISION_FINAL"

    async def test_revision_final_ot_inexistente(self, taller_client):
        response = await taller_client.post(
            "/v1/ordenes-trabajo/id-99999/revision-final",
            json={"costo_mano_obra": "50.00"},
        )
        assert response.status_code == 404

    async def test_revision_final_bloqueada_por_manual(self, taller_client, ot_en_ejecucion):
        await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_en_ejecucion}/repuestos",
            json={"codigo": "REP-CARO", "cantidad": 1},
        )
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_en_ejecucion}/revision-final",
            json={"costo_mano_obra": "80.00"},
        )
        assert response.status_code == 422

    async def test_evento_revision_final_publicado(self, taller_client, ot_en_ejecucion):
        await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_en_ejecucion}/revision-final",
            json={"costo_mano_obra": "80.00"},
        )
        bus = taller_client.app.state.event_bus
        assert bus.fue_publicado("orden_trabajo.revision_final")


class TestEPTAL07CobroParcial:
    @pytest.fixture
    async def ot_revision_final(self, taller_client) -> str:
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/repuestos", json={"codigo": "REP-001", "cantidad": 1})
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/revision-final", json={"costo_mano_obra": "80.00"})
        return ot_id

    async def test_cobro_parcial_80_porcentaje(self, taller_client, ot_revision_final):
        # monto total = 25 (repuesto) + 80 (mano obra) = 105
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_revision_final}/cobro-parcial",
            json={"monto_pagado": "90.00", "plazo_dias": 7},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "deuda_activa" in data

    async def test_cobro_parcial_bajo_80_falla(self, taller_client, ot_revision_final):
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_revision_final}/cobro-parcial",
            json={"monto_pagado": "50.00", "plazo_dias": 7},
        )
        assert response.status_code == 409

    async def test_cobro_parcial_ot_inexistente(self, taller_client):
        response = await taller_client.post(
            "/v1/ordenes-trabajo/id-99999/cobro-parcial",
            json={"monto_pagado": "100.00", "plazo_dias": 7},
        )
        assert response.status_code == 404


class TestEPTAL08CerrarOT:
    @pytest.fixture
    async def ot_lista_para_cerrar(self, taller_client) -> str:
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/repuestos", json={"codigo": "REP-001", "cantidad": 1})
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/revision-final", json={"costo_mano_obra": "80.00"})
        # Confirmar cobro via cobro-parcial completo (105 = 25+80)
        await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_id}/cobro-parcial",
            json={"monto_pagado": "105.00", "plazo_dias": 1},
        )
        return ot_id

    async def test_cerrar_ot(self, taller_client, ot_lista_para_cerrar):
        response = await taller_client.post(f"/v1/ordenes-trabajo/{ot_lista_para_cerrar}/cerrar")
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "CERRADA"

    async def test_cerrar_ot_sin_cobro_falla(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "baja",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/repuestos", json={"codigo": "REP-001", "cantidad": 1})
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/revision-final", json={"costo_mano_obra": "50.00"})
        response = await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/cerrar")
        assert response.status_code == 409

    async def test_cerrar_ot_inexistente(self, taller_client):
        response = await taller_client.post("/v1/ordenes-trabajo/id-99999/cerrar")
        assert response.status_code == 404

    async def test_evento_cerrada_publicado(self, taller_client, ot_lista_para_cerrar):
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_lista_para_cerrar}/cerrar")
        bus = taller_client.app.state.event_bus
        assert bus.fue_publicado("orden_trabajo.cerrada")


class TestEPTAL09CancelarOT:
    async def test_cancelar_ot(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "baja",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_id}/cancelar",
            json={"motivo": "cliente retiró vehículo"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "CANCELADA"

    async def test_cancelar_ot_inexistente(self, taller_client):
        response = await taller_client.post(
            "/v1/ordenes-trabajo/id-99999/cancelar",
            json={"motivo": "test"},
        )
        assert response.status_code == 404

    async def test_evento_cancelada_publicado(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/cancelar", json={"motivo": "prueba"})
        bus = taller_client.app.state.event_bus
        assert bus.fue_publicado("orden_trabajo.cancelada")


class TestEPTAL10LiberarVehiculo:
    async def test_liberar_vehiculo(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/repuestos", json={"codigo": "REP-001", "cantidad": 1})
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/revision-final", json={"costo_mano_obra": "80.00"})
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/cobro-parcial", json={"monto_pagado": "105.00", "plazo_dias": 1})
        await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/cerrar")

        response = await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/liberar-vehiculo")
        assert response.status_code == 200
        bus = taller_client.app.state.event_bus
        assert bus.fue_publicado("vehiculo.liberado")

    async def test_liberar_vehiculo_sin_cerrar_falla(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "baja",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        response = await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/liberar-vehiculo")
        assert response.status_code == 422

    async def test_liberar_vehiculo_inexistente(self, taller_client):
        response = await taller_client.post("/v1/ordenes-trabajo/id-99999/liberar-vehiculo")
        assert response.status_code == 404


class TestEPTAL11Disponibilidad:
    async def test_consultar_disponibilidad(self, taller_client):
        response = await taller_client.get("/v1/taller/disponibilidad")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 1
        assert data["mecanicos_disponibles"][0]["nivel"] == "MASTER"


class TestEPTAL12ObtenerOT:
    async def test_obtener_ot_existente(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "baja",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        response = await taller_client.get(f"/v1/ordenes-trabajo/{ot_id}")
        assert response.status_code == 200
        assert response.json()["data"]["ot_id"] == ot_id

    async def test_obtener_ot_inexistente(self, taller_client):
        response = await taller_client.get("/v1/ordenes-trabajo/id-99999")
        assert response.status_code == 404

    async def test_respuesta_incluye_request_id(self, taller_client):
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "baja",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        response = await taller_client.get(f"/v1/ordenes-trabajo/{ot_id}")
        assert "request_id" in response.json()["meta"]


class TestEPTAL17AceptarOT:
    """Pieza E (sesión catálogo/UI, 2026-07-05) — el mecánico master asignado
    reconoce una OT ya creada. `aceptada_en` es auditoría, no un estado."""

    @pytest.fixture
    async def ot_id(self, taller_client) -> str:
        r = await taller_client.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": taller_client._vehiculo_id,
                "mecanico_master_id": taller_client._mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        return r.json()["data"]["ot_id"]

    def _token_mecanico_asignado(self, taller_client) -> str:
        # El fixture taller_client registra al mecánico con usuario_id="u-master".
        return make_test_token(taller_client._test_private_pem, "MECANICO_MASTER", sub="u-master")

    async def test_aceptar_ot(self, taller_client, ot_id):
        token = self._token_mecanico_asignado(taller_client)
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_id}/aceptar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["aceptada_en"] is not None
        assert data["vehiculo"]["modelo"] == "Bajaj RE"
        assert data["vehiculo"]["universo"] == "mototaxi"

    async def test_aceptar_ot_dos_veces_falla(self, taller_client, ot_id):
        token = self._token_mecanico_asignado(taller_client)
        headers = {"Authorization": f"Bearer {token}"}
        primera = await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aceptar", headers=headers)
        assert primera.status_code == 200
        segunda = await taller_client.post(f"/v1/ordenes-trabajo/{ot_id}/aceptar", headers=headers)
        assert segunda.status_code == 409

    async def test_aceptar_ot_mecanico_no_asignado(self, taller_client, ot_id):
        from src.taller.domain.models.orden_trabajo import Mecanico, NivelMecanico
        repo = taller_client.app.state.taller_repo
        otro = Mecanico(usuario_id="u-otro-mecanico", nivel=NivelMecanico.MASTER)
        await repo.guardar_mecanico(otro)
        token = make_test_token(taller_client._test_private_pem, "MECANICO_MASTER", sub="u-otro-mecanico")
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_id}/aceptar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    async def test_aceptar_ot_inexistente(self, taller_client):
        token = self._token_mecanico_asignado(taller_client)
        response = await taller_client.post(
            "/v1/ordenes-trabajo/id-99999/aceptar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_aceptar_ot_usuario_no_mecanico(self, taller_client, ot_id):
        # Token ADMINISTRADOR sin registro en la tabla mecanico.
        token = make_test_token(taller_client._test_private_pem, "ADMINISTRADOR", sub="admin-sin-mecanico")
        response = await taller_client.post(
            f"/v1/ordenes-trabajo/{ot_id}/aceptar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

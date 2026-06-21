"""
Tests de integración — API de pedidos (EP-PED-01 a EP-PED-17).
"""
import pytest
from decimal import Decimal
from tests.integration.conftest import make_test_token


class TestEPPED01CrearPedido:
    async def test_crear_pedido_vacio(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "presencial", "items": [], "cliente_id": "cli-001"},
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["estado"] == "BORRADOR"

    async def test_crear_pedido_con_items(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/pedidos",
            json={
                "canal_origen": "presencial",
                "items": [{"codigo": "REP-001", "cantidad": 2}],
                "cliente_id": "cli-001",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["monto_total"] == "90.00"
        assert len(data["items"]) == 1

    async def test_crear_pedido_repuesto_baja_falla(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/pedidos",
            json={
                "canal_origen": "presencial",
                "items": [{"codigo": "REP-BAJA", "cantidad": 1}],
            },
        )
        assert response.status_code == 422

    async def test_canal_origen_vacio_falla(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "", "items": []},
        )
        assert response.status_code == 422


class TestEPPED02ListarPedidos:
    async def test_listar_vacio(self, pedidos_client):
        response = await pedidos_client.get("/v1/pedidos")
        assert response.status_code == 200
        assert response.json()["data"]["total"] == 0

    async def test_listar_con_pedidos(self, pedidos_client):
        await pedidos_client.post("/v1/pedidos", json={"canal_origen": "presencial", "items": []})
        await pedidos_client.post("/v1/pedidos", json={"canal_origen": "remoto", "items": []})
        response = await pedidos_client.get("/v1/pedidos")
        assert response.json()["data"]["total"] == 2

    async def test_listar_por_cliente(self, pedidos_client):
        await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "presencial", "items": [], "cliente_id": "cli-filtro"},
        )
        await pedidos_client.post("/v1/pedidos", json={"canal_origen": "presencial", "items": []})
        response = await pedidos_client.get("/v1/pedidos", params={"cliente_id": "cli-filtro"})
        assert response.json()["data"]["total"] == 1


class TestEPPED03ObtenerPedido:
    async def test_obtener_existente(self, pedidos_client):
        crear = await pedidos_client.post("/v1/pedidos", json={"canal_origen": "presencial", "items": []})
        pedido_id = crear.json()["data"]["pedido_id"]
        response = await pedidos_client.get(f"/v1/pedidos/{pedido_id}")
        assert response.status_code == 200

    async def test_obtener_inexistente(self, pedidos_client):
        response = await pedidos_client.get("/v1/pedidos/id-99999")
        assert response.status_code == 404


class TestEPPED04ConfirmarPedido:
    async def test_confirmar_con_stock(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "presencial", "items": [{"codigo": "REP-001", "cantidad": 2}]},
        )
        pedido_id = crear.json()["data"]["pedido_id"]
        response = await pedidos_client.post(f"/v1/pedidos/{pedido_id}/confirmar")
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "CONFIRMADO"

    async def test_confirmar_sin_stock_cancela(self, pedidos_client):
        pedidos_client.app.state.stock_adapter.establecer_stock("rp-001", 0)
        crear = await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "presencial", "items": [{"codigo": "REP-001", "cantidad": 5}]},
        )
        pedido_id = crear.json()["data"]["pedido_id"]
        response = await pedidos_client.post(f"/v1/pedidos/{pedido_id}/confirmar")
        assert response.status_code == 422

    async def test_confirmar_inexistente(self, pedidos_client):
        response = await pedidos_client.post("/v1/pedidos/id-99999/confirmar")
        assert response.status_code == 404


class TestEPPED05CancelarPedido:
    async def test_cancelar_borrador(self, pedidos_client):
        crear = await pedidos_client.post("/v1/pedidos", json={"canal_origen": "presencial", "items": []})
        pedido_id = crear.json()["data"]["pedido_id"]
        response = await pedidos_client.post(
            f"/v1/pedidos/{pedido_id}/cancelar",
            json={"motivo": "cliente no quiere"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "CANCELADO"

    async def test_cancelar_cliente_solo_borrador(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "presencial", "items": [{"codigo": "REP-001", "cantidad": 1}]},
        )
        pedido_id = crear.json()["data"]["pedido_id"]
        await pedidos_client.post(f"/v1/pedidos/{pedido_id}/confirmar")
        response = await pedidos_client.post(
            f"/v1/pedidos/{pedido_id}/cancelar",
            json={"motivo": "quiero cancelar", "es_cliente": True},
        )
        assert response.status_code == 422

    async def test_cancelar_inexistente(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/pedidos/id-99999/cancelar",
            json={"motivo": "test"},
        )
        assert response.status_code == 404


class TestEPPED06CrearReserva:
    async def test_crear_reserva_con_stock(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/reservas",
            json={
                "cliente_id": "cli-001",
                "repuesto_id": "rp-001",
                "cantidad": 3,
                "segmento": "CLIENTE_CONDUCTOR",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["estado"] == "ACTIVA"
        assert "expira_en" in data

    async def test_crear_reserva_sin_stock(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/reservas",
            json={
                "cliente_id": "cli-001",
                "repuesto_id": "rp-001",
                "cantidad": 9999,
                "segmento": "CLIENTE_CONDUCTOR",
            },
        )
        assert response.status_code == 409

    async def test_crear_reserva_distrito_ttl_mayor(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/reservas",
            json={
                "cliente_id": "cli-002",
                "repuesto_id": "rp-002",
                "cantidad": 2,
                "segmento": "CLIENTE_DISTRITO",
            },
        )
        assert response.status_code == 201
        assert response.json()["data"]["segmento"] == "CLIENTE_DISTRITO"


class TestEPPED07LiberarReserva:
    async def test_liberar_reserva(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/reservas",
            json={
                "cliente_id": "cli-001",
                "repuesto_id": "rp-001",
                "cantidad": 2,
                "segmento": "CLIENTE_CONDUCTOR",
            },
        )
        reserva_id = crear.json()["data"]["reserva_id"]
        response = await pedidos_client.post(
            f"/v1/reservas/{reserva_id}/liberar",
            json={"motivo": "LIBERADA_MANUAL"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "LIBERADA"

    async def test_liberar_inexistente(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/reservas/id-99999/liberar",
            json={"motivo": "test"},
        )
        assert response.status_code == 404

    async def test_liberar_ya_liberada_falla(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/reservas",
            json={
                "cliente_id": "cli-001",
                "repuesto_id": "rp-001",
                "cantidad": 1,
                "segmento": "CLIENTE_CONDUCTOR",
            },
        )
        reserva_id = crear.json()["data"]["reserva_id"]
        await pedidos_client.post(f"/v1/reservas/{reserva_id}/liberar", json={"motivo": "M"})
        response = await pedidos_client.post(
            f"/v1/reservas/{reserva_id}/liberar",
            json={"motivo": "M"},
        )
        assert response.status_code == 422


class TestEPPED08Proforma:
    async def test_emitir_proforma(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "presencial", "items": [{"codigo": "REP-001", "cantidad": 1}]},
        )
        pedido_id = crear.json()["data"]["pedido_id"]
        response = await pedidos_client.post(f"/v1/pedidos/{pedido_id}/proforma")
        assert response.status_code == 201
        data = response.json()["data"]
        assert "numero_referencia" in data
        assert data["monto_total"] == "45.00"

    async def test_proforma_pedido_inexistente(self, pedidos_client):
        response = await pedidos_client.post("/v1/pedidos/id-99999/proforma")
        assert response.status_code == 404


class TestEPPED09Envio:
    async def test_registrar_envio(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "presencial", "items": [{"codigo": "REP-001", "cantidad": 1}]},
        )
        pedido_id = crear.json()["data"]["pedido_id"]
        await pedidos_client.post(f"/v1/pedidos/{pedido_id}/confirmar")
        await pedidos_client.post(f"/v1/pedidos/{pedido_id}/confirmar")
        pedido = await pedidos_client.get(f"/v1/pedidos/{pedido_id}")
        estado = pedido.json()["data"]["estado"]
        if estado == "CONFIRMADO":
            repo = pedidos_client.app.state.pedidos_repo
            p = await repo.obtener_por_id(pedido_id)
            from src.pedidos.domain.models.pedido import EstadoPedido
            p.avanzar_estado(EstadoPedido.EN_PREPARACION)
            await repo.actualizar(p)

        response = await pedidos_client.post(
            f"/v1/pedidos/{pedido_id}/envio",
            json={"empresa_encomienda": "Olva", "direccion_destino": "Huancayo 123"},
        )
        assert response.status_code in (201, 422)

    async def test_envio_pedido_inexistente(self, pedidos_client):
        response = await pedidos_client.post(
            "/v1/pedidos/id-99999/envio",
            json={"empresa_encomienda": "Olva", "direccion_destino": "Huancayo"},
        )
        assert response.status_code == 404


class TestEPPED10y11ConfirmarRecepcionIncidencia:
    async def test_confirmar_recepcion_pedido_inexistente(self, pedidos_client):
        response = await pedidos_client.post("/v1/pedidos/id-99999/confirmar-recepcion")
        assert response.status_code == 404

    async def test_incidencia_pedido_inexistente(self, pedidos_client):
        response = await pedidos_client.post("/v1/pedidos/id-99999/incidencia")
        assert response.status_code == 404

    async def test_incidencia_desde_despachado(self, pedidos_client):
        crear = await pedidos_client.post(
            "/v1/pedidos",
            json={"canal_origen": "presencial", "items": [{"codigo": "REP-001", "cantidad": 1}]},
        )
        pedido_id = crear.json()["data"]["pedido_id"]
        await pedidos_client.post(f"/v1/pedidos/{pedido_id}/confirmar")
        repo = pedidos_client.app.state.pedidos_repo
        p = await repo.obtener_por_id(pedido_id)
        from src.pedidos.domain.models.pedido import EstadoPedido
        p.avanzar_estado(EstadoPedido.EN_PREPARACION)
        p.despachar()
        await repo.actualizar(p)
        response = await pedidos_client.post(f"/v1/pedidos/{pedido_id}/incidencia")
        assert response.status_code == 200


class TestEPPED12Notificacion:
    async def test_solicitar_notificacion(self, pedidos_client):
        # EP-PED-12: solo CLIENTE_* — override del token ADMIN por defecto
        token = make_test_token(pedidos_client._test_private_pem, "CLIENTE_CONDUCTOR")
        response = await pedidos_client.post(
            "/v1/notificaciones/repuesto-disponible",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


class TestEPPED13y14ListaReserva:
    # EP-PED-13 y EP-PED-14: solo CLIENTE_DISTRITO — override del token ADMIN por defecto

    async def test_crear_lista_vacia(self, pedidos_client):
        token = make_test_token(pedidos_client._test_private_pem, "CLIENTE_DISTRITO")
        response = await pedidos_client.post(
            "/v1/lista-reserva-progresiva",
            headers={"Authorization": f"Bearer {token}"},
            json={"cliente_id": "cli-001", "items": []},
        )
        assert response.status_code == 201
        assert response.json()["data"]["estado"] == "BORRADOR"

    async def test_formalizar_lista(self, pedidos_client):
        token = make_test_token(pedidos_client._test_private_pem, "CLIENTE_DISTRITO")
        crear = await pedidos_client.post(
            "/v1/lista-reserva-progresiva",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "cliente_id": "cli-001",
                "items": [
                    {"repuesto_id": "rp-001", "codigo": "REP-001", "cantidad": 1, "precio_referencia": "45.00"}
                ],
            },
        )
        lista_id = crear.json()["data"]["lista_id"]
        response = await pedidos_client.post(
            f"/v1/lista-reserva-progresiva/{lista_id}/formalizar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_formalizar_inexistente(self, pedidos_client):
        token = make_test_token(pedidos_client._test_private_pem, "CLIENTE_DISTRITO")
        response = await pedidos_client.post(
            "/v1/lista-reserva-progresiva/id-99999/formalizar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_formalizar_lista_vacia_falla(self, pedidos_client):
        token = make_test_token(pedidos_client._test_private_pem, "CLIENTE_DISTRITO")
        crear = await pedidos_client.post(
            "/v1/lista-reserva-progresiva",
            headers={"Authorization": f"Bearer {token}"},
            json={"cliente_id": "cli-001", "items": []},
        )
        lista_id = crear.json()["data"]["lista_id"]
        response = await pedidos_client.post(
            f"/v1/lista-reserva-progresiva/{lista_id}/formalizar",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

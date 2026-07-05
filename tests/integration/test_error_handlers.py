"""
Tests para ramas de manejo de errores no cubiertas en api/ — 09 §10.1.
Cubre: dependencies.py·main.py·catalogo.py·pedidos.py·taller.py except-handlers faltantes.
"""
from __future__ import annotations

import decimal
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.dependencies import error_response, success_response


# ══════════════════════════════════════════════════════════════════════
# dependencies.py — líneas 19 y 36: UUID fallback cuando request_id=""
# ══════════════════════════════════════════════════════════════════════

def test_success_response_sin_request_id_genera_uuid():
    """dependencies.py línea 19: request_id vacío genera UUID."""
    r = success_response({"x": 1})  # sin request_id
    rid = r["meta"]["request_id"]
    assert rid and len(rid) == 36  # formato UUID4


def test_error_response_sin_request_id_genera_uuid():
    """dependencies.py línea 36: request_id vacío genera UUID."""
    r = error_response("CODE", "msg")  # sin request_id
    rid = r["error"]["request_id"]
    assert rid and len(rid) == 36


# ══════════════════════════════════════════════════════════════════════
# main.py — líneas 95-96: global exception handler (500)
# Test directo al handler — ASGITransport propaga RuntimeError antes de que
# FastAPI pueda convertirlo en respuesta, por lo que se prueba el handler
# llamándolo directamente como función async.
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_global_exception_handler_retorna_json_500():
    """main.py líneas 95-96: el handler de Exception devuelve JSONResponse 500."""
    from api.main import create_app
    from fastapi import Request
    from starlette.testclient import TestClient

    app = create_app()

    # Acceder directamente al handler registrado en la app
    handler = app.exception_handlers.get(Exception)
    assert handler is not None, "global_exception_handler no registrado"

    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()
    mock_request.state.request_id = "test-rid-500"

    exc = RuntimeError("fallo inesperado de prueba")
    response = await handler(mock_request, exc)

    assert response.status_code == 500
    import json
    body = json.loads(response.body)
    assert body["error"]["code"] == "ERROR_INTERNO"


# ══════════════════════════════════════════════════════════════════════
# catalogo.py — handlers de excepción faltantes
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_precio_repuesto_inexistente_retorna_404(app_client):
    """catalogo.py 229-230: RepuestoNoEncontradoError en consultar_precio → 404."""
    r = await app_client.get(
        "/v1/repuestos/NO-EXISTE/precio",
        params={"consultas_realizadas": 0, "nivel_visibilidad": 1},
    )
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "REPUESTO_NO_ENCONTRADO"


@pytest.mark.asyncio
async def test_crear_repuesto_domain_error_retorna_422(app_client):
    """catalogo.py 273-274: DomainError en crear_repuesto → 422 VALIDACION_FALLIDA."""
    from src.catalogo.domain.models.repuesto import DomainError as CatalogoDomainError
    with patch(
        "src.catalogo.application.use_cases.crear_repuesto.CrearRepuestoUseCase.execute",
        new=AsyncMock(side_effect=CatalogoDomainError("código duplicado")),
    ):
        r = await app_client.post("/v1/repuestos", json={
            "codigo": "DUP-001", "nombre": "Dup", "universo": "mototaxi_3r",
            "modelo": "Bajaj RE", "año": 2021, "categoria": "motor", "precio_venta": "10.00",
        })
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "VALIDACION_FALLIDA"


@pytest.mark.asyncio
async def test_actualizar_precio_repuesto_de_baja_retorna_409(app_client):
    """catalogo.py 326-327: RepuestoDadoDeBajaError en actualizar_precio → 409."""
    await app_client.post("/v1/repuestos", json={
        "codigo": "BAJA-001", "nombre": "Para baja", "universo": "mototaxi_3r",
        "modelo": "Bajaj RE", "año": 2021, "categoria": "motor", "precio_venta": "20.00",
    })
    await app_client.request("DELETE", "/v1/repuestos/BAJA-001", json={"motivo": "test"})
    r = await app_client.patch("/v1/repuestos/BAJA-001/precio", json={"precio_venta": "25.00"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_dar_de_baja_repuesto_ya_inactivo_retorna_409(app_client):
    """catalogo.py 378-379: DomainError en dar_de_baja cuando ya está inactivo → 409."""
    await app_client.post("/v1/repuestos", json={
        "codigo": "BAJA-002", "nombre": "Ya baja", "universo": "mototaxi_3r",
        "modelo": "Bajaj RE", "año": 2022, "categoria": "motor", "precio_venta": "30.00",
    })
    await app_client.request("DELETE", "/v1/repuestos/BAJA-002", json={"motivo": "primera"})
    r = await app_client.request("DELETE", "/v1/repuestos/BAJA-002", json={"motivo": "segunda"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_historial_precio_repuesto_inexistente_retorna_404(app_client):
    """catalogo.py 405-406: RepuestoNoEncontradoError en historial_precio → 404."""
    r = await app_client.get("/v1/repuestos/NO-EXISTE/historial-precio")
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "REPUESTO_NO_ENCONTRADO"


# ══════════════════════════════════════════════════════════════════════
# pedidos.py — handlers de excepción faltantes
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_proforma_domain_error_retorna_422(pedidos_client):
    """pedidos.py 364-365: DomainError en emitir_proforma → 422."""
    from src.pedidos.domain.models.pedido import DomainError as PedidosDomainError
    with patch(
        "src.pedidos.application.use_cases.gestionar_comprobante.EmitirProformaUseCase.execute",
        new=AsyncMock(side_effect=PedidosDomainError("pedido sin items")),
    ):
        r = await pedidos_client.post("/v1/pedidos/any-id/proforma")
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "VALIDACION_FALLIDA"


@pytest.mark.asyncio
async def test_registrar_envio_domain_error_retorna_422(pedidos_client):
    """pedidos.py 404-405: DomainError en registrar_envio → 422."""
    from src.pedidos.domain.models.pedido import DomainError as PedidosDomainError
    with patch(
        "src.pedidos.application.use_cases.gestionar_comprobante.RegistrarEnvioUseCase.execute",
        new=AsyncMock(side_effect=PedidosDomainError("estado no permite despacho")),
    ):
        r = await pedidos_client.post("/v1/pedidos/any-id/envio", json={
            "empresa_encomienda": "Olva", "direccion_destino": "Jr. Lima 123", "distrito": "AYACUCHO",
        })
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "TRANSICION_ESTADO_INVALIDA"


@pytest.mark.asyncio
async def test_confirmar_recepcion_transicion_invalida_retorna_422(pedidos_client):
    """pedidos.py 433-438: TransicionEstadoInvalidaError → 422."""
    from src.pedidos.domain.models.pedido import TransicionEstadoInvalidaError
    with patch(
        "src.pedidos.application.use_cases.gestionar_comprobante.ConfirmarRecepcionUseCase.execute",
        new=AsyncMock(side_effect=TransicionEstadoInvalidaError("estado inválido")),
    ):
        r = await pedidos_client.post("/v1/pedidos/any-id/confirmar-recepcion")
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "TRANSICION_ESTADO_INVALIDA"


@pytest.mark.asyncio
async def test_registrar_incidencia_transicion_invalida_retorna_422(pedidos_client):
    """pedidos.py 458-459: TransicionEstadoInvalidaError en registrar_incidencia → 422."""
    from src.pedidos.domain.models.pedido import TransicionEstadoInvalidaError
    with patch(
        "src.pedidos.application.use_cases.gestionar_comprobante.RegistrarIncidenciaUseCase.execute",
        new=AsyncMock(side_effect=TransicionEstadoInvalidaError("no en DESPACHADO")),
    ):
        r = await pedidos_client.post("/v1/pedidos/any-id/incidencia")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_lista_reserva_domain_error_retorna_422(pedidos_client):
    """pedidos.py 503-504: DomainError en crear_lista_reserva → 422. EP-PED-13: CLIENTE_DISTRITO."""
    from src.pedidos.domain.models.pedido import DomainError as PedidosDomainError
    from tests.integration.conftest import make_test_token
    token = make_test_token(pedidos_client._test_private_pem, "CLIENTE_DISTRITO")
    with patch(
        "src.pedidos.application.use_cases.gestionar_comprobante.CrearListaReservaUseCase.execute",
        new=AsyncMock(side_effect=PedidosDomainError("datos inválidos")),
    ):
        r = await pedidos_client.post(
            "/v1/lista-reserva-progresiva",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "cliente_id": "c-001",
                "items": [{"repuesto_id": "rp-001", "codigo": "REP-001",
                           "cantidad": 1, "precio_referencia": "10.00"}],
            },
        )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_generar_comprobante_pedido_inexistente_retorna_404(pedidos_client):
    """pedidos.py 568-569: PedidoNoEncontradoError en generar_comprobante → 404."""
    r = await pedidos_client.post("/v1/pedidos/pedido-inexistente/comprobante", json={
        "tipo": "boleta", "monto": "100.00",
        "emitido_por": "u-vendedor", "rol_emisor": "VENDEDOR",
    })
    assert r.status_code == 404
    assert r.json()["detail"]["error"]["code"] == "RECURSO_NO_ENCONTRADO"


@pytest.mark.asyncio
async def test_anular_comprobante_transicion_invalida_retorna_422(pedidos_client):
    """pedidos.py 636-637: anular comprobante en PENDIENTE_VALIDACION → 422."""
    # Crear pedido → generar comprobante (PENDIENTE_VALIDACION) → anular (requiere EMITIDO)
    rp = await pedidos_client.post("/v1/pedidos", json={
        "canal_origen": "mostrador", "origen_actor": "VENDEDOR",
        "cliente_id": "c-001", "items": [],
    })
    pedido_id = rp.json()["data"]["pedido_id"]
    comp_r = await pedidos_client.post(f"/v1/pedidos/{pedido_id}/comprobante", json={
        "tipo": "boleta", "monto": "45.00",
        "emitido_por": "u-vendedor", "rol_emisor": "VENDEDOR",
    })
    comp_id = comp_r.json()["data"]["comprobante_id"]
    r = await pedidos_client.post(f"/v1/comprobantes/{comp_id}/anular")
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "TRANSICION_ESTADO_INVALIDA"


# ══════════════════════════════════════════════════════════════════════
# taller.py — handlers de excepción faltantes
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_agregar_repuesto_ot_estado_incorrecto_retorna_422(taller_client):
    """taller.py 187-188: DomainError en agregar_repuesto cuando OT no está ABIERTA → 422."""
    from src.taller.domain.models.orden_trabajo import (
        ListaRepuestosOT, ModalidadIntervencion, NivelUrgencia, OrdenTrabajo,
    )
    repo = taller_client.app.state.taller_repo
    ot = OrdenTrabajo(vehiculo_id=taller_client._vehiculo_id, mecanico_master_id=taller_client._mecanico_id,
                      modalidad=ModalidadIntervencion.PREVENTIVO, urgencia=NivelUrgencia.BAJA)
    item = ListaRepuestosOT(orden_trabajo_id=ot.id, repuesto_id="rp-001", codigo="REP-001",
                            cantidad=1, precio_unitario=decimal.Decimal("25.00"),
                            momento_agregado="inicial")
    ot.agregar_repuesto_inicial(item)
    ot.presentar_lista_al_cliente()  # → LISTA_REPUESTOS
    await repo.guardar_ot(ot)
    r = await taller_client.post(f"/v1/ordenes-trabajo/{ot.id}/repuestos", json={
        "repuesto_id": "rp-001", "codigo": "REP-001",
        "cantidad": 1, "precio_unitario": "25.00",
    })
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "VALIDACION_FALLIDA"


@pytest.mark.asyncio
async def test_confirmar_adicional_domain_error_retorna_422(taller_client):
    """taller.py 241-242: DomainError en confirmar_adicional (ítem no encontrado) → 422."""
    from src.taller.domain.models.orden_trabajo import DomainError as TallerDomainError
    with patch(
        "src.taller.application.use_cases.gestionar_ot.ConfirmarAdicionalUseCase.execute",
        new=AsyncMock(side_effect=TallerDomainError("ítem no encontrado")),
    ):
        r = await taller_client.post(f"/v1/ordenes-trabajo/any-ot-id/confirmar-adicional",
                                      json={"item_id": "item-x"})
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "VALIDACION_FALLIDA"


@pytest.mark.asyncio
async def test_cerrar_ot_transicion_invalida_retorna_422(taller_client):
    """taller.py 359-360: TransicionEstadoInvalidaError en cerrar_ot → 422."""
    from src.taller.domain.models.orden_trabajo import (
        DomainError as TallerDomainError, TransicionEstadoInvalidaError,
    )
    with patch(
        "src.taller.application.use_cases.gestionar_ot.CerrarOrdenTrabajoUseCase.execute",
        new=AsyncMock(side_effect=TransicionEstadoInvalidaError("estado inválido para cierre")),
    ):
        r = await taller_client.post("/v1/ordenes-trabajo/any-ot-id/cerrar")
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "TRANSICION_ESTADO_INVALIDA"


@pytest.mark.asyncio
async def test_cancelar_ot_cerrada_retorna_422(taller_client):
    """taller.py 388-389: TransicionEstadoInvalidaError en cancelar OT ya CERRADA → 422."""
    from src.taller.domain.models.orden_trabajo import (
        ListaRepuestosOT, ModalidadIntervencion, NivelUrgencia, OrdenTrabajo,
    )
    repo = taller_client.app.state.taller_repo
    mecanico_id = taller_client._mecanico_id
    vehiculo_id = taller_client._vehiculo_id
    ot = OrdenTrabajo(vehiculo_id=vehiculo_id, mecanico_master_id=mecanico_id,
                      modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA)
    item = ListaRepuestosOT(orden_trabajo_id=ot.id, repuesto_id="rp-001", codigo="REP-001",
                            cantidad=1, precio_unitario=decimal.Decimal("25.00"),
                            momento_agregado="inicial")
    ot.agregar_repuesto_inicial(item)
    ot.presentar_lista_al_cliente()          # ABIERTA → LISTA_REPUESTOS
    ot.aprobar_lista()                       # LISTA_REPUESTOS → EN_EJECUCION
    ot.declarar_revision_final(decimal.Decimal("0.00"), mecanico_id)  # → REVISION_FINAL
    ot.confirmar_cobro()
    await repo.guardar_ot(ot)
    await taller_client.post(f"/v1/ordenes-trabajo/{ot.id}/cerrar")
    r = await taller_client.post(f"/v1/ordenes-trabajo/{ot.id}/cancelar", json={"motivo": "test"})
    assert r.status_code == 422
    assert r.json()["detail"]["error"]["code"] == "TRANSICION_ESTADO_INVALIDA"

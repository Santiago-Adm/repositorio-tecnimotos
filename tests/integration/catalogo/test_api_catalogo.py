"""
Tests de integración — API de catálogo (endpoints EP-CAT-01 a EP-CAT-06).
Usan TestClient de FastAPI con repositorio en memoria.
"""
import pytest
from decimal import Decimal
from httpx import AsyncClient, ASGITransport

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    Repuesto,
    UniversoRepuesto,
)


@pytest.fixture
async def client_with_data(app_client):
    """Cliente con datos de prueba precargados."""
    repo = app_client.app.state.catalogo_repo

    repuesto = Repuesto(
        codigo="REP-001",
        nombre="Filtro de aceite Bajaj RE",
        universo=UniversoRepuesto.MOTOTAXI_3R,
        modelo="Bajaj RE",
        año=2019,
        categoria=CategoriaRepuesto.MOTOR,
        precio_venta=Decimal("45.00"),
        descripcion="Filtro original",
    )
    await repo.guardar(repuesto)

    repuesto_motolineal = Repuesto(
        codigo="REP-100",
        nombre="Cadena TVS",
        universo=UniversoRepuesto.MOTOLINEAL,
        modelo="TVS Apache",
        año=2022,
        categoria=CategoriaRepuesto.TRANSMISION,
        precio_venta=Decimal("85.00"),
    )
    await repo.guardar(repuesto_motolineal)

    return app_client


@pytest.mark.asyncio
async def test_health_responde_ok(app_client):
    response = await app_client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["estado"] == "ok"
    assert "request_id" in data["meta"]


@pytest.mark.asyncio
async def test_ep_cat_01_busca_por_universo(client_with_data):
    """EP-CAT-01: búsqueda por universo — solo retorna el universo solicitado."""
    response = await client_with_data.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    repuestos = data["repuestos"]
    assert all(r["universo"] == "mototaxi_3r" for r in repuestos)


@pytest.mark.asyncio
async def test_ep_cat_01_no_incluye_precio_venta(client_with_data):
    """EP-CAT-01: NUNCA devuelve precio_venta (03 §6.2 regla crítica)."""
    response = await client_with_data.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r"}
    )
    repuestos = response.json()["data"]["repuestos"]
    for r in repuestos:
        assert "precio_venta" not in r


@pytest.mark.asyncio
async def test_ep_cat_01_separacion_universos_rnn05(client_with_data):
    """RNN-05: mototaxi y motolineal nunca se mezclan."""
    resp_mt = await client_with_data.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r"}
    )
    resp_ml = await client_with_data.get(
        "/v1/repuestos", params={"universo": "motolineal"}
    )
    codigos_mt = [r["codigo"] for r in resp_mt.json()["data"]["repuestos"]]
    codigos_ml = [r["codigo"] for r in resp_ml.json()["data"]["repuestos"]]
    assert "REP-001" in codigos_mt
    assert "REP-100" in codigos_ml
    assert "REP-100" not in codigos_mt
    assert "REP-001" not in codigos_ml


@pytest.mark.asyncio
async def test_ep_cat_01_filtro_q_matchea_nombre(client_with_data):
    """EP-CAT-01: q filtra por nombre, substring case-insensitive."""
    response = await client_with_data.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r", "q": "ACEITE"}
    )
    assert response.status_code == 200
    repuestos = response.json()["data"]["repuestos"]
    assert len(repuestos) == 1
    assert repuestos[0]["codigo"] == "REP-001"


@pytest.mark.asyncio
async def test_ep_cat_01_filtro_q_matchea_codigo_parcial(client_with_data):
    """EP-CAT-01: q también filtra por código, no solo nombre."""
    response = await client_with_data.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r", "q": "rep-00"}
    )
    assert response.status_code == 200
    repuestos = response.json()["data"]["repuestos"]
    assert len(repuestos) == 1
    assert repuestos[0]["codigo"] == "REP-001"


@pytest.mark.asyncio
async def test_ep_cat_01_filtro_q_sin_coincidencias(client_with_data):
    """EP-CAT-01: q sin coincidencias retorna lista vacía, no error."""
    response = await client_with_data.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r", "q": "esto-no-existe"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 0
    assert data["repuestos"] == []


@pytest.mark.asyncio
async def test_ep_cat_02_obtiene_por_codigo(client_with_data):
    """EP-CAT-02: obtiene repuesto por código."""
    response = await client_with_data.get("/v1/repuestos/REP-001")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["codigo"] == "REP-001"
    assert "precio_venta" not in data


@pytest.mark.asyncio
async def test_ep_cat_02_codigo_inexistente_404(app_client):
    """EP-CAT-02: código inexistente retorna 404."""
    response = await app_client.get("/v1/repuestos/REP-999")
    assert response.status_code == 404
    error = response.json()["detail"]["error"]
    assert error["code"] == "REPUESTO_NO_ENCONTRADO"


@pytest.mark.asyncio
async def test_ep_cat_02b_precio_visible_nivel_1(client_with_data):
    """EP-CAT-02-B: cliente nivel 1 con consultas disponibles ve precio."""
    response = await client_with_data.get(
        "/v1/repuestos/REP-001/precio",
        params={"consultas_realizadas": 0, "nivel_visibilidad": 1},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["precio_visible"] is True
    assert data["precio_venta"] == "45.00"


@pytest.mark.asyncio
async def test_ep_cat_02b_precio_no_visible_visitante(client_with_data):
    """HU-S1-05 Escenario 2: visitante sin cuenta no ve precio."""
    response = await client_with_data.get(
        "/v1/repuestos/REP-001/precio",
        params={"consultas_realizadas": 0, "nivel_visibilidad": 0},
    )
    data = response.json()["data"]
    assert data["precio_visible"] is False
    assert data["precio_venta"] is None


@pytest.mark.asyncio
async def test_ep_cat_03_crea_repuesto(app_client):
    """EP-CAT-03: crea repuesto y publica evento."""
    response = await app_client.post(
        "/v1/repuestos",
        json={
            "codigo": "REP-NEW-001",
            "nombre": "Repuesto nuevo",
            "universo": "mototaxi_3r",
            "modelo": "Bajaj RE",
            "año": 2021,
            "categoria": "motor",
            "precio_venta": "55.00",
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["codigo"] == "REP-NEW-001"

    # Verificar que el evento fue publicado
    eventos = app_client.app.state.event_bus.get_published()
    assert any(e.tipo == "repuesto.creado" for e in eventos)


@pytest.mark.asyncio
async def test_ep_cat_04_actualiza_precio(client_with_data):
    """EP-CAT-04: actualiza precio y publica evento."""
    response = await client_with_data.patch(
        "/v1/repuestos/REP-001/precio",
        json={"precio_venta": "52.00"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["precio_venta"] == "52.00"
    assert data["precio_anterior"] == "45.00"

    eventos = client_with_data.app.state.event_bus.get_published()
    assert any(e.tipo == "repuesto.precio_actualizado" for e in eventos)


@pytest.mark.asyncio
async def test_ep_cat_05_da_de_baja(client_with_data):
    """EP-CAT-05: baja lógica — activo=False, evento publicado."""
    response = await client_with_data.request(
        "DELETE",
        "/v1/repuestos/REP-001",
        json={"motivo": "Descontinuado"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["activo"] is False

    eventos = client_with_data.app.state.event_bus.get_published()
    assert any(e.tipo == "repuesto.dado_de_baja" for e in eventos)


@pytest.mark.asyncio
async def test_ep_cat_06_historial_precio(client_with_data):
    """EP-CAT-06: historial de precios tras actualización."""
    await client_with_data.patch(
        "/v1/repuestos/REP-001/precio",
        json={"precio_venta": "52.00"},
    )
    response = await client_with_data.get(
        "/v1/repuestos/REP-001/historial-precio"
    )
    assert response.status_code == 200
    historial = response.json()["data"]["historial"]
    assert len(historial) == 1
    assert historial[0]["precio_anterior"] == "45.00"
    assert historial[0]["precio_nuevo"] == "52.00"


@pytest.mark.asyncio
async def test_ep_s2_01_consulta_lista_codigos(client_with_data):
    """HU-S2-01: consulta múltiple por lista de códigos."""
    response = await client_with_data.post(
        "/v1/catalogo/repuestos/consulta-lista",
        json={"codigos": ["REP-001", "REP-999"]},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "disponibles" in data
    assert "sin_stock" in data
    codigos_disp = [item["codigo"] for item in data["disponibles"]]
    assert "REP-001" in codigos_disp
    codigos_sin = [item["codigo"] for item in data["sin_stock"]]
    assert "REP-999" in codigos_sin


@pytest.mark.asyncio
async def test_ep_cat_02_404_retorna_error_correcto(app_client):
    """EP-CAT-02: 404 tiene estructura error correcta."""
    response = await app_client.get("/v1/repuestos/NO-EXISTE")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert body["detail"]["error"]["code"] == "REPUESTO_NO_ENCONTRADO"


@pytest.mark.asyncio
async def test_ep_cat_04_codigo_inexistente_404(client_with_data):
    """EP-CAT-04: actualizar precio de repuesto inexistente retorna 404."""
    response = await client_with_data.patch(
        "/v1/repuestos/REP-999/precio",
        json={"precio_venta": "50.00"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ep_cat_05_codigo_inexistente_404(app_client):
    """EP-CAT-05: dar de baja repuesto inexistente retorna 404."""
    response = await app_client.request(
        "DELETE",
        "/v1/repuestos/REP-999",
        json={"motivo": "test"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_respuesta_incluye_envelope(client_with_data):
    """Toda respuesta incluye envelope {data, meta} (03 §6.8)."""
    response = await client_with_data.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r"}
    )
    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert "timestamp" in body["meta"]
    assert "request_id" in body["meta"]


@pytest.mark.asyncio
async def test_header_x_request_id(client_with_data):
    """CorrelationMiddleware añade X-Request-ID en la respuesta (02 §1.6)."""
    response = await client_with_data.get(
        "/v1/repuestos", params={"universo": "mototaxi_3r"}
    )
    assert "x-request-id" in response.headers

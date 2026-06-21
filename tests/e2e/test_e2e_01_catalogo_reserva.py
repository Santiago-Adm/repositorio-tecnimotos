"""
E2E-01 — Consulta de catálogo y reserva de repuesto (04 §7.1).
Flujo: Cliente busca repuesto → verifica disponibilidad → crea reserva
       → stock_repuesto.cantidad_apartada refleja el cambio.
HU: HU-S1-01 · HU-S1-02.

Notas de implementación:
- EP-CAT-01 requiere query param `universo` obligatorio.
- EP-STK-01 requiere INTERNO_ROLES (no accesible por CLIENTE_*).
  La disponibilidad se verifica vía EP-CAT-07 (consulta-lista pública).
- SegmentoCliente enum: CONDUCTOR = "CLIENTE_CONDUCTOR".
"""


class TestE2E01CatalogoReserva:
    """
    Criterio de éxito (04 §7.1): Cliente busca repuesto → verifica disponibilidad →
    crea reserva → cantidad_apartada refleja el cambio en ≤ 3 pasos.
    """

    async def test_buscar_repuesto_en_catalogo(self, client_conductor):
        """Paso 1 — EP-CAT-01: listar repuestos activos por universo."""
        response = await client_conductor.get("/v1/repuestos?universo=mototaxi")
        assert response.status_code == 200
        data = response.json()["data"]
        codigos = [r["codigo"] for r in data["repuestos"]]
        assert "REP-001" in codigos

    async def test_verificar_disponibilidad_via_consulta_lista(self, client_conductor):
        """
        Paso 2 — EP-CAT-07: verificar disponibilidad vía consulta múltiple.
        EP-STK-01 requiere INTERNO_ROLES — CLIENTE usa EP-CAT-07 para ver stock.
        """
        response = await client_conductor.post(
            "/v1/catalogo/repuestos/consulta-lista",
            json={"codigos": ["REP-001"]},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "disponibles" in data
        disponibles = [r["codigo"] for r in data["disponibles"]]
        assert "REP-001" in disponibles

    async def test_crear_reserva(self, client_conductor, e2e_app):
        """Paso 3 — EP-PED-06: crear reserva de repuesto disponible."""
        response = await client_conductor.post(
            "/v1/reservas",
            json={
                "cliente_id": "u-cliente-e2e",
                "repuesto_id": e2e_app._e2e_rep_filtro_id,
                "cantidad": 2,
                "segmento": "CLIENTE_CONDUCTOR",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert "reserva_id" in data
        assert data["estado"] == "ACTIVA"

    async def test_flujo_completo_en_3_pasos(self, client_conductor, e2e_app):
        """
        Criterio E2E-01 completo: 3 pasos encadenados (04 §7.1).
        Stock adapter refleja la cantidad apartada tras crear reserva.
        """
        # Paso 1 — buscar por universo
        r1 = await client_conductor.get("/v1/repuestos?universo=mototaxi")
        assert r1.status_code == 200
        assert any(r["codigo"] == "REP-001" for r in r1.json()["data"]["repuestos"])

        # Paso 2 — verificar disponibilidad (EP-CAT-07)
        r2 = await client_conductor.post(
            "/v1/catalogo/repuestos/consulta-lista",
            json={"codigos": ["REP-001"]},
        )
        assert r2.status_code == 200
        assert "REP-001" in [r["codigo"] for r in r2.json()["data"]["disponibles"]]

        # Paso 3 — crear reserva
        r3 = await client_conductor.post(
            "/v1/reservas",
            json={
                "cliente_id": "u-cliente-e2e",
                "repuesto_id": e2e_app._e2e_rep_filtro_id,
                "cantidad": 3,
                "segmento": "CLIENTE_CONDUCTOR",
            },
        )
        assert r3.status_code == 201
        assert r3.json()["data"]["estado"] == "ACTIVA"

        # Verificar que el stock adapter refleja la reserva (via app.state)
        stock_adapter = e2e_app.state.stock_adapter
        apartado = stock_adapter._apartado.get(e2e_app._e2e_rep_filtro_id, 0)
        assert apartado >= 3, (
            f"cantidad_apartada debería ser ≥ 3, es {apartado}"
        )

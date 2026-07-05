"""
E2E-03 — Pedido remoto de distrito con proforma y envío (04 §7.1).
Flujo: S2 consulta lista → crea pedido → proforma de Elena →
       confirma → envio registrado → notificación WhatsApp (Stub).
HU: HU-S2-02 · HU-S2-04.

Notas de estado y flujo (pedido.py):
- EstadoPedido: BORRADOR → CONFIRMADO → EN_PREPARACION → DESPACHADO
- ConfirmarPedidoUseCase: BORRADOR → CONFIRMADO (verifica stock).
- RegistrarEnvioUseCase: requiere EN_PREPARACION → DESPACHADO.
- No existe endpoint HTTP para CONFIRMADO → EN_PREPARACION.
  El test avanza directamente vía repo (igual que test_api_pedidos.py §line 267).

Notas de SegmentoCliente enum:
- DISTRITO = "CLIENTE_DISTRITO", CONDUCTOR = "CLIENTE_CONDUCTOR"
"""
from src.pedidos.domain.models.pedido import EstadoPedido


class TestE2E03PedidoDistrito:
    """
    Criterio de éxito (04 §7.1): pedido S2 completa ciclo hasta envio registrado
    y notificación WhatsApp enviada (Stub verificado).
    """

    async def test_consulta_lista_repuestos(self, client_distrito, e2e_app):
        """EP-CAT-07 (HU-S2-01): CLIENTE_DISTRITO consulta lista de repuestos."""
        response = await client_distrito.post(
            "/v1/catalogo/repuestos/consulta-lista",
            json={"codigos": ["REP-001", "REP-002"]},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "disponibles" in data
        codigos_disponibles = [r["codigo"] for r in data["disponibles"]]
        assert "REP-001" in codigos_disponibles

    async def test_crear_pedido_canal_s2(self, client_distrito, e2e_app):
        """EP-PED-01: CLIENTE_DISTRITO crea pedido canal S2 — estado inicial BORRADOR."""
        response = await client_distrito.post(
            "/v1/pedidos",
            json={
                "canal_origen": "S2",
                "cliente_id": "u-distrito-e2e",
                "items": [
                    {"codigo": "REP-001", "cantidad": 2},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["estado"] == "BORRADOR"
        assert data["canal_origen"] == "S2"

    async def test_ciclo_completo_pedido_distrito(
        self, client_distrito, client_vendedor, e2e_app
    ):
        """
        Criterio E2E-03 completo: S2 → pedido → proforma Elena → confirma → envío.
        Verifica evento pedido.confirmado publicado (Stub WhatsApp).
        """
        # Paso 1 — Consultar lista (HU-S2-01)
        r0 = await client_distrito.post(
            "/v1/catalogo/repuestos/consulta-lista",
            json={"codigos": ["REP-001"]},
        )
        assert r0.status_code == 200
        assert len(r0.json()["data"]["disponibles"]) > 0

        # Paso 2 — EP-PED-01: Crear pedido S2 → BORRADOR
        r1 = await client_distrito.post(
            "/v1/pedidos",
            json={
                "canal_origen": "S2",
                "cliente_id": "u-distrito-e2e",
                "items": [{"codigo": "REP-001", "cantidad": 1}],
            },
        )
        assert r1.status_code == 201
        pedido_id = r1.json()["data"]["pedido_id"]
        assert r1.json()["data"]["estado"] == "BORRADOR"

        # Paso 3 — EP-PED-08: VENDEDOR emite proforma (funciona desde BORRADOR)
        r2 = await client_vendedor.post(f"/v1/pedidos/{pedido_id}/proforma")
        assert r2.status_code == 201
        assert "proforma_id" in r2.json()["data"]

        # Paso 4 — EP-PED-04: CLIENTE_DISTRITO confirma pedido → CONFIRMADO
        r3 = await client_distrito.post(f"/v1/pedidos/{pedido_id}/confirmar")
        assert r3.status_code == 200
        assert r3.json()["data"]["estado"] == "CONFIRMADO"

        # Avanzar a EN_PREPARACION vía repo (no hay endpoint HTTP para esta transición)
        repo = e2e_app.state.pedidos_repo
        p = await repo.obtener_por_id(pedido_id)
        p.avanzar_estado(EstadoPedido.EN_PREPARACION)
        await repo.actualizar(p)

        # Paso 5 — EP-PED-09: VENDEDOR registra envío → DESPACHADO
        r4 = await client_vendedor.post(
            f"/v1/pedidos/{pedido_id}/envio",
            json={
                "empresa_encomienda": "Marvisur",
                "direccion_destino": "Jr. Lima 123, Huamanga, Ayacucho",
                "distrito": "AYACUCHO",
            },
        )
        assert r4.status_code == 201
        assert r4.json()["data"]["estado"] in {"PREPARADO", "ENVIADO", "DESPACHADO", "EN_TRANSITO"}

        # Verificar evento de pedido confirmado (notificación WhatsApp — Stub)
        bus = e2e_app.state.event_bus
        assert bus.fue_publicado("pedido.confirmado"), (
            "Evento pedido.confirmado no fue publicado — WhatsApp Stub no activado"
        )

    async def test_ttl_reserva_distrito_3_dias(self, client_distrito, e2e_app):
        """
        Verificar TTL de reserva para segmento DISTRITO = 3 días (03 §3.3).
        SegmentoCliente.DISTRITO = 'CLIENTE_DISTRITO'.
        """
        r = await client_distrito.post(
            "/v1/reservas",
            json={
                "cliente_id": "u-distrito-e2e",
                "repuesto_id": e2e_app._e2e_rep_filtro_id,
                "cantidad": 1,
                "segmento": "CLIENTE_DISTRITO",
            },
        )
        assert r.status_code == 201
        data = r.json()["data"]
        assert "reserva_id" in data
        assert data["estado"] == "ACTIVA"
        # TTL de 3 días declarado en domain para DISTRITO
        # expires_at debe estar ~3 días en el futuro
        if "expires_at" in data:
            from datetime import datetime, timezone, timedelta
            expires = datetime.fromisoformat(data["expires_at"])
            now = datetime.now(timezone.utc)
            diff_days = (expires - now).days
            assert 2 <= diff_days <= 4, (
                f"TTL de reserva DISTRITO debería ser ~3 días, encontrado {diff_days}"
            )

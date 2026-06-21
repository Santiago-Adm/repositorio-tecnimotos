"""
E2E-02 — Ciclo completo de orden_trabajo con cobro (04 §7.1).
Flujo: Mecánico abre OT → lista aprobada → ejecución → revisión final →
       cobro → cierre → evento cerrada publicado.
HU: HU-INT-02 · HU-INT-03 · HU-INT-04.

Notas de RBAC (03 §6.5):
- EP-TAL-01: INTERNO_ROLES — MECANICO_MASTER ✓
- EP-TAL-02: MECANICO_JUNIOR_ROLES — MECANICO_MASTER ✓
- EP-TAL-03: TAL_VENDEDOR_ROLES — VENDEDOR ✓
- EP-TAL-06: MECANICO_ROLES — MECANICO_MASTER ✓
- EP-TAL-07: ADMIN_ROLES solo — usa client_admin
- EP-TAL-08: ADMINISTRADOR, SUPERADMIN, MECANICO_MASTER — usa client_mecanico

Repuesto REP-001 a S/25.00 (< S/30 — automático, sin espera tácita).
Total cobro: S/25 (repuesto) + S/50 (mano obra) = S/75.
"""


class TestE2E02OTCobro:
    """
    Criterio de éxito (04 §7.1): OT completa el ciclo ABIERTA→CERRADA
    sin discrepancia y con evento publicado.
    """

    async def test_abrir_ot(self, client_mecanico, e2e_app):
        """EP-TAL-01: Mecánico abre OT para vehículo registrado."""
        response = await client_mecanico.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": e2e_app._e2e_vehiculo_id,
                "mecanico_master_id": e2e_app._e2e_mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["estado"] == "ABIERTA"
        assert "ot_id" in data

    async def test_ciclo_completo_ot(
        self, client_mecanico, client_vendedor, client_admin, e2e_app
    ):
        """
        Criterio E2E-02 completo: ABIERTA→CERRADA, evento orden_trabajo.cerrada publicado.
        EP-TAL-07 cobro-parcial requiere ADMIN_ROLES.
        EP-TAL-08 cerrar acepta MECANICO_MASTER.
        """
        # EP-TAL-01: MECANICO_MASTER abre OT
        r1 = await client_mecanico.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": e2e_app._e2e_vehiculo_id,
                "mecanico_master_id": e2e_app._e2e_mecanico_id,
                "modalidad": "correctivo",
                "urgencia": "alta",
            },
        )
        assert r1.status_code == 201
        ot_id = r1.json()["data"]["ot_id"]
        assert r1.json()["data"]["estado"] == "ABIERTA"

        # EP-TAL-02: MECANICO_MASTER agrega repuesto REP-001 (S/25 — automático)
        r2 = await client_mecanico.post(
            f"/v1/ordenes-trabajo/{ot_id}/repuestos",
            json={"codigo": "REP-001", "cantidad": 1},
        )
        assert r2.status_code == 201
        assert len(r2.json()["data"]["lista_repuestos"]) == 1

        # EP-TAL-03: VENDEDOR aprueba lista → EN_EJECUCION (AprobarListaUseCase condensa 2 pasos)
        r3 = await client_vendedor.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
        assert r3.status_code == 200
        assert r3.json()["data"]["estado"] == "EN_EJECUCION"

        # EP-TAL-06: MECANICO_MASTER declara revisión final
        r4 = await client_mecanico.post(
            f"/v1/ordenes-trabajo/{ot_id}/revision-final",
            json={"costo_mano_obra": "50.00"},
        )
        assert r4.status_code == 200
        assert r4.json()["data"]["estado"] == "REVISION_FINAL"

        # EP-TAL-07: ADMINISTRADOR registra cobro parcial — total = 25 + 50 = 75
        r5 = await client_admin.post(
            f"/v1/ordenes-trabajo/{ot_id}/cobro-parcial",
            json={"monto_pagado": "75.00", "plazo_dias": 1},
        )
        assert r5.status_code == 200

        # EP-TAL-08: MECANICO_MASTER cierra OT → CERRADA (descuento atómico)
        r6 = await client_mecanico.post(f"/v1/ordenes-trabajo/{ot_id}/cerrar")
        assert r6.status_code == 200
        assert r6.json()["data"]["estado"] == "CERRADA"

        # Verificar evento de cierre publicado (08 §8.1 Observabilidad)
        bus = e2e_app.state.event_bus
        assert bus.fue_publicado("orden_trabajo.cerrada"), (
            "Evento orden_trabajo.cerrada no fue publicado al cerrar OT"
        )

    async def test_no_cierra_sin_cobro(
        self, client_mecanico, client_vendedor, client_admin, e2e_app
    ):
        """Criterio negativo: MECANICO_MASTER no puede cerrar OT sin cobro registrado."""
        r = await client_mecanico.post(
            "/v1/ordenes-trabajo",
            json={
                "vehiculo_id": e2e_app._e2e_vehiculo_id,
                "mecanico_master_id": e2e_app._e2e_mecanico_id,
                "modalidad": "preventivo",
                "urgencia": "baja",
            },
        )
        ot_id = r.json()["data"]["ot_id"]
        await client_mecanico.post(
            f"/v1/ordenes-trabajo/{ot_id}/repuestos",
            json={"codigo": "REP-001", "cantidad": 1},
        )
        await client_vendedor.post(f"/v1/ordenes-trabajo/{ot_id}/aprobar-lista")
        await client_mecanico.post(
            f"/v1/ordenes-trabajo/{ot_id}/revision-final",
            json={"costo_mano_obra": "50.00"},
        )

        # Intentar cerrar sin cobro — MECANICO_MASTER puede cerrar pero dominio bloquea
        r_cierre = await client_mecanico.post(f"/v1/ordenes-trabajo/{ot_id}/cerrar")
        assert r_cierre.status_code in {409, 422}, (
            f"Esperado 409/422 al cerrar sin cobro, recibido {r_cierre.status_code}"
        )

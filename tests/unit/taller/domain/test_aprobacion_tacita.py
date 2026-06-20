"""
Test específico del criterio 09 §3.4 — Flujo aprobación tácita.
Verifica: aprobación automática < S/30, espera 30 min para S/30-S/100.
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from src.taller.domain.models.orden_trabajo import (
    DomainError,
    EstadoAprobacion,
    ListaRepuestosOT,
    ModalidadIntervencion,
    NivelUrgencia,
    OrdenTrabajo,
    TramoAdicional,
    UMBRAL_APROBACION_AUTOMATICA,
    UMBRAL_APROBACION_TACITA,
    MINUTOS_ESPERA_TACITA,
)
from src.taller.domain.services.taller_service import TallerService
from src.taller.application.use_cases.gestionar_ot import (
    AplicarAprobacionesTacitasUseCase,
)


class TestAprobacionTacita:
    """
    Verifica la lógica de tramos de precio (HU-INT-03, 09 §3.4).
    < S/30: automático sin espera.
    S/30-S/100: espera 30 min → tácita si no hay respuesta.
    > S/100: bloqueo hasta confirmación manual del cliente.
    """

    def _ot_en_ejecucion(self, item_inicial_precio=Decimal("20.00")) -> OrdenTrabajo:
        ot = OrdenTrabajo(
            vehiculo_id="v-1", mecanico_master_id="m-1",
            modalidad=ModalidadIntervencion.CORRECTIVO,
            urgencia=NivelUrgencia.MEDIA,
        )
        item = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-base", codigo="BASE",
            cantidad=1, precio_unitario=item_inicial_precio, momento_agregado="inicial",
        )
        ot.agregar_repuesto_inicial(item)
        ot.presentar_lista_al_cliente()
        ot.aprobar_lista()
        return ot

    def test_precio_bajo_30_aprobacion_automatica(self):
        ot = self._ot_en_ejecucion()
        adicional = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-a", codigo="A",
            cantidad=1, precio_unitario=Decimal("25.00"), momento_agregado="en_ejecucion",
        )
        ot.agregar_repuesto_en_ejecucion(adicional)
        assert adicional.aprobacion_cliente == EstadoAprobacion.APROBADO_AUTOMATICO
        assert adicional.tramo_precio == TramoAdicional.AUTOMATICO
        assert adicional.esta_aprobado() is True

    def test_precio_exactamente_bajo_30_automatico(self):
        ot = self._ot_en_ejecucion()
        adicional = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-a", codigo="A",
            cantidad=1, precio_unitario=Decimal("29.99"), momento_agregado="en_ejecucion",
        )
        ot.agregar_repuesto_en_ejecucion(adicional)
        assert adicional.tramo_precio == TramoAdicional.AUTOMATICO

    def test_precio_30_a_100_inicia_espera(self):
        ot = self._ot_en_ejecucion()
        adicional = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-b", codigo="B",
            cantidad=1, precio_unitario=Decimal("65.00"), momento_agregado="en_ejecucion",
        )
        ot.agregar_repuesto_en_ejecucion(adicional)
        assert adicional.tramo_precio == TramoAdicional.TACITO
        assert adicional.aprobacion_cliente == EstadoAprobacion.PENDIENTE_ADICIONAL
        assert adicional.espera_hasta is not None
        delta = adicional.espera_hasta - datetime.now(timezone.utc)
        assert delta.total_seconds() <= MINUTOS_ESPERA_TACITA * 60 + 5

    def test_precio_exactamente_30_es_tacito(self):
        ot = self._ot_en_ejecucion()
        adicional = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-b", codigo="B",
            cantidad=1, precio_unitario=UMBRAL_APROBACION_AUTOMATICA, momento_agregado="en_ejecucion",
        )
        ot.agregar_repuesto_en_ejecucion(adicional)
        assert adicional.tramo_precio == TramoAdicional.TACITO

    def test_precio_100_es_tacito(self):
        ot = self._ot_en_ejecucion()
        adicional = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-b", codigo="B",
            cantidad=1, precio_unitario=UMBRAL_APROBACION_TACITA, momento_agregado="en_ejecucion",
        )
        ot.agregar_repuesto_en_ejecucion(adicional)
        assert adicional.tramo_precio == TramoAdicional.TACITO

    def test_precio_mayor_100_requiere_manual(self):
        ot = self._ot_en_ejecucion()
        adicional = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-c", codigo="C",
            cantidad=1, precio_unitario=Decimal("150.00"), momento_agregado="en_ejecucion",
        )
        ot.agregar_repuesto_en_ejecucion(adicional)
        assert adicional.tramo_precio == TramoAdicional.MANUAL
        assert adicional.aprobacion_cliente == EstadoAprobacion.PENDIENTE_ADICIONAL
        assert not adicional.esta_aprobado()

    def test_revision_final_bloqueada_por_manual(self):
        ot = self._ot_en_ejecucion()
        adicional = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-c", codigo="C",
            cantidad=1, precio_unitario=Decimal("150.00"), momento_agregado="en_ejecucion",
        )
        ot.agregar_repuesto_en_ejecucion(adicional)
        with pytest.raises(DomainError) as exc_info:
            ot.declarar_revision_final(Decimal("80.00"), "m-1")
        assert "aprobación manual" in str(exc_info.value).lower() or "pendiente" in str(exc_info.value).lower()

    def test_tacito_aprobado_permite_revision(self):
        ot = self._ot_en_ejecucion()
        adicional = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-b", codigo="B",
            cantidad=1, precio_unitario=Decimal("65.00"), momento_agregado="en_ejecucion",
        )
        ot.agregar_repuesto_en_ejecucion(adicional)
        # Simular expiración y aplicar tácita
        adicional.espera_hasta = datetime.now(timezone.utc) - timedelta(seconds=1)
        for item in TallerService.items_con_espera_expirada(ot):
            item.aprobar_tacitamente()
        # Ahora sí puede avanzar a REVISION_FINAL
        ot.declarar_revision_final(Decimal("80.00"), "m-1")
        assert ot.estado.value == "REVISION_FINAL"

    def test_clasificar_tramo_servicio_correcto(self):
        assert TallerService.clasificar_tramo_adicional(Decimal("10")) == TramoAdicional.AUTOMATICO
        assert TallerService.clasificar_tramo_adicional(Decimal("50")) == TramoAdicional.TACITO
        assert TallerService.clasificar_tramo_adicional(Decimal("200")) == TramoAdicional.MANUAL

    async def test_aplicar_aprobaciones_tacitas_use_case(self, repo, event_bus):
        from src.taller.application.use_cases.gestionar_ot import (
            AbrirOrdenTrabajoCommand, AbrirOrdenTrabajoUseCase,
            AgregarRepuestoCommand, AgregarRepuestoUseCase,
            AprobarListaCommand, AprobarListaUseCase,
        )
        from src.taller.domain.models.orden_trabajo import ModalidadIntervencion, NivelUrgencia
        from src.taller.infrastructure.adapters.catalogo_taller_adapter import InMemoryCatalogoTallerAdapter
        from src.taller.domain.ports.catalogo_taller_port import RepuestoInfoTaller

        catalogo = InMemoryCatalogoTallerAdapter()
        catalogo.agregar_repuesto(RepuestoInfoTaller(
            repuesto_id="rp-base", codigo="BASE",
            precio_venta=Decimal("20.00"), nombre="Base", activo=True,
        ))
        catalogo.agregar_repuesto(RepuestoInfoTaller(
            repuesto_id="rp-tacito", codigo="TACITO",
            precio_venta=Decimal("65.00"), nombre="Tacito", activo=True,
        ))

        abrir_uc = AbrirOrdenTrabajoUseCase(repo, event_bus)
        ot = await abrir_uc.execute(AbrirOrdenTrabajoCommand(
            vehiculo_id=repo._vehiculo_id,
            mecanico_master_id=repo._mecanico_id,
            modalidad=ModalidadIntervencion.PREVENTIVO,
            urgencia=NivelUrgencia.BAJA,
            actor_id="m-1",
        ))

        agregar_uc = AgregarRepuestoUseCase(repo, catalogo, event_bus)
        await agregar_uc.execute(AgregarRepuestoCommand(ot_id=ot.id, codigo="BASE", cantidad=1, actor_id="m-1"))

        aprobar_uc = AprobarListaUseCase(repo, event_bus)
        await aprobar_uc.execute(AprobarListaCommand(ot_id=ot.id, actor_id="m-1"))

        await agregar_uc.execute(AgregarRepuestoCommand(ot_id=ot.id, codigo="TACITO", cantidad=1, actor_id="m-1"))

        ot_actual = await repo.obtener_ot(ot.id)
        tacito_item = next(i for i in ot_actual.lista_repuestos if i.codigo == "TACITO")
        tacito_item.espera_hasta = datetime.now(timezone.utc) - timedelta(seconds=1)
        await repo.actualizar_ot(ot_actual)

        aplicar_uc = AplicarAprobacionesTacitasUseCase(repo)
        ot_resuelto = await aplicar_uc.execute(ot.id)
        tacito_resuelto = next(i for i in ot_resuelto.lista_repuestos if i.codigo == "TACITO")
        assert tacito_resuelto.aprobacion_cliente == EstadoAprobacion.APROBADO_TACITO

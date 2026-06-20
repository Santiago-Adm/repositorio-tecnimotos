"""
Test específico del criterio 09 §3.4 — Registro consumo obligatorio.
Verifica: OT no cierra sin lista confirmada de consumo.
"""
import pytest
from decimal import Decimal

from src.taller.domain.models.orden_trabajo import (
    CobroNoConfirmadoError,
    DomainError,
    ListaNoConfirmadaError,
    ListaRepuestosOT,
    ModalidadIntervencion,
    NivelUrgencia,
    OrdenTrabajo,
)
from src.taller.domain.services.taller_service import TallerService


class TestConsumoObligatorio:
    """
    Verifica que la OT no cierra sin lista de consumo confirmada (HU-INT-04).
    """

    def _ot_base(self) -> OrdenTrabajo:
        return OrdenTrabajo(
            vehiculo_id="v-1", mecanico_master_id="m-1",
            modalidad=ModalidadIntervencion.CORRECTIVO,
            urgencia=NivelUrgencia.ALTA,
        )

    def test_ot_no_cierra_sin_lista(self):
        ot = self._ot_base()
        ot.cobro_confirmado = True
        with pytest.raises(ListaNoConfirmadaError):
            ot.cerrar()

    def test_ot_no_cierra_sin_cobro_confirmado(self):
        ot = self._ot_base()
        item = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-1", codigo="R",
            cantidad=1, precio_unitario=Decimal("20.00"), momento_agregado="inicial",
        )
        ot.agregar_repuesto_inicial(item)
        ot.presentar_lista_al_cliente()
        ot.aprobar_lista()
        ot.declarar_revision_final(Decimal("50.00"), "m-1")
        with pytest.raises(CobroNoConfirmadoError):
            ot.cerrar()

    def test_ot_cierra_con_lista_y_cobro(self):
        ot = self._ot_base()
        item = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-1", codigo="R",
            cantidad=1, precio_unitario=Decimal("20.00"), momento_agregado="inicial",
        )
        ot.agregar_repuesto_inicial(item)
        ot.presentar_lista_al_cliente()
        ot.aprobar_lista()
        ot.declarar_revision_final(Decimal("50.00"), "m-1")
        ot.confirmar_cobro()
        ot.cerrar()
        from src.taller.domain.models.orden_trabajo import EstadoOrdenTrabajo
        assert ot.estado == EstadoOrdenTrabajo.CERRADA

    def test_ot_cierra_solo_con_mano_obra_si_lista_vacia(self):
        """
        Caso borde: solo mano de obra sin repuestos.
        verificar_consumo_registrado pasa si hay costo_mano_obra.
        """
        ot = self._ot_base()
        ot.costo_mano_obra = Decimal("80.00")
        ot.cobro_confirmado = True
        ot.cliente_aprobo_lista = True
        assert TallerService.verificar_consumo_registrado(ot) is True

    def test_consumo_no_registrado_sin_lista_ni_mano_obra(self):
        ot = self._ot_base()
        assert TallerService.verificar_consumo_registrado(ot) is False

    def test_consumo_registrado_con_repuestos_aprobados(self):
        ot = self._ot_base()
        item = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-1", codigo="R",
            cantidad=1, precio_unitario=Decimal("20.00"), momento_agregado="inicial",
        )
        ot.agregar_repuesto_inicial(item)
        ot.presentar_lista_al_cliente()
        ot.aprobar_lista()
        assert TallerService.verificar_consumo_registrado(ot) is True

    def test_revision_final_requiere_lista_aprobada_cliente(self):
        """
        Transición EN_EJECUCION → REVISION_FINAL requiere lista aprobada
        (cliente_aprobo_lista se establece al llamar aprobar_lista).
        """
        ot = self._ot_base()
        item = ListaRepuestosOT(
            orden_trabajo_id=ot.id, repuesto_id="rp-1", codigo="R",
            cantidad=1, precio_unitario=Decimal("20.00"), momento_agregado="inicial",
        )
        ot.agregar_repuesto_inicial(item)
        ot.presentar_lista_al_cliente()
        ot.aprobar_lista()
        assert ot.cliente_aprobo_lista is True
        ot.declarar_revision_final(Decimal("50.00"), "m-1")
        from src.taller.domain.models.orden_trabajo import EstadoOrdenTrabajo
        assert ot.estado == EstadoOrdenTrabajo.REVISION_FINAL

    def test_no_puede_declarar_revision_sin_haber_aprobado_lista(self):
        """
        Sin aprobar_lista() → cliente_aprobo_lista=False → cerrar falla.
        """
        ot = self._ot_base()
        # Forzamos estado EN_EJECUCION sin el flujo normal
        from src.taller.domain.models.orden_trabajo import EstadoOrdenTrabajo
        ot.estado = EstadoOrdenTrabajo.EN_EJECUCION
        ot.cobro_confirmado = True
        with pytest.raises(ListaNoConfirmadaError):
            ot.cerrar()

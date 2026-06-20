"""
Tests unitarios — dominio del módulo taller.
Meta: ≥ 85% branch coverage (09 §3.4).
"""
import pytest
from datetime import timedelta
from decimal import Decimal

from src.taller.domain.models.orden_trabajo import (
    CobroNoConfirmadoError,
    DomainError,
    Entrada,
    EstadoAprobacion,
    EstadoEntrada,
    EstadoOrdenTrabajo,
    HistorialIntervencion,
    ListaNoConfirmadaError,
    ListaRepuestosOT,
    Mecanico,
    ModalidadIntervencion,
    NivelMecanico,
    NivelUrgencia,
    OrdenTrabajo,
    TramoAdicional,
    TransicionEstadoInvalidaError,
    Vehiculo,
    UMBRAL_APROBACION_AUTOMATICA,
    UMBRAL_APROBACION_TACITA,
)
from src.taller.domain.services.taller_service import TallerService
from datetime import datetime, timezone


# ── Vehiculo ──────────────────────────────────────────────────────────────────

class TestVehiculo:
    def test_crea_vehiculo_valido(self):
        v = Vehiculo(universo="mototaxi", modelo="Bajaj RE", año=2020)
        assert v.año == 2020

    def test_rechaza_año_antiguo(self):
        with pytest.raises(DomainError):
            Vehiculo(universo="mototaxi", modelo="X", año=1980)

    def test_rechaza_año_futuro(self):
        with pytest.raises(DomainError):
            Vehiculo(universo="mototaxi", modelo="X", año=2200)

    def test_rechaza_salud_negativa(self):
        with pytest.raises(DomainError):
            Vehiculo(universo="mototaxi", modelo="X", año=2020, salud_estimada=-1)

    def test_rechaza_salud_mayor_100(self):
        with pytest.raises(DomainError):
            Vehiculo(universo="mototaxi", modelo="X", año=2020, salud_estimada=101)


# ── ListaRepuestosOT ──────────────────────────────────────────────────────────

class TestListaRepuestosOT:
    def test_crea_item_valido(self, item_barato):
        assert item_barato.subtotal == Decimal("25.00")

    def test_rechaza_cantidad_cero(self):
        with pytest.raises(DomainError):
            ListaRepuestosOT(
                orden_trabajo_id="ot", repuesto_id="r", codigo="C",
                cantidad=0, precio_unitario=Decimal("10"), momento_agregado="inicial",
            )

    def test_rechaza_precio_cero(self):
        with pytest.raises(DomainError):
            ListaRepuestosOT(
                orden_trabajo_id="ot", repuesto_id="r", codigo="C",
                cantidad=1, precio_unitario=Decimal("0"), momento_agregado="inicial",
            )

    def test_tramo_automatico(self, item_barato):
        assert item_barato.determinar_tramo() == TramoAdicional.AUTOMATICO

    def test_tramo_tacito(self):
        item = ListaRepuestosOT(
            orden_trabajo_id="ot", repuesto_id="r", codigo="C",
            cantidad=1, precio_unitario=Decimal("65.00"), momento_agregado="en_ejecucion",
        )
        assert item.determinar_tramo() == TramoAdicional.TACITO

    def test_tramo_manual(self, item_costoso):
        assert item_costoso.determinar_tramo() == TramoAdicional.MANUAL

    def test_tramo_tacito_exacto_en_limite_tacito(self):
        item = ListaRepuestosOT(
            orden_trabajo_id="ot", repuesto_id="r", codigo="C",
            cantidad=1, precio_unitario=Decimal("100.00"), momento_agregado="en_ejecucion",
        )
        assert item.determinar_tramo() == TramoAdicional.TACITO

    def test_tramo_automatico_exacto_en_limite_inferior(self):
        item = ListaRepuestosOT(
            orden_trabajo_id="ot", repuesto_id="r", codigo="C",
            cantidad=1, precio_unitario=Decimal("29.99"), momento_agregado="en_ejecucion",
        )
        assert item.determinar_tramo() == TramoAdicional.AUTOMATICO

    def test_aprobar_automaticamente(self, item_barato):
        item_barato.aprobar_automaticamente()
        assert item_barato.aprobacion_cliente == EstadoAprobacion.APROBADO_AUTOMATICO
        assert item_barato.esta_aprobado() is True

    def test_iniciar_espera_tacita(self):
        item = ListaRepuestosOT(
            orden_trabajo_id="ot", repuesto_id="r", codigo="C",
            cantidad=1, precio_unitario=Decimal("65.00"), momento_agregado="en_ejecucion",
        )
        item.iniciar_espera_tacita()
        assert item.aprobacion_cliente == EstadoAprobacion.PENDIENTE_ADICIONAL
        assert item.espera_hasta is not None

    def test_aprobar_tacitamente(self):
        item = ListaRepuestosOT(
            orden_trabajo_id="ot", repuesto_id="r", codigo="C",
            cantidad=1, precio_unitario=Decimal("65.00"), momento_agregado="en_ejecucion",
        )
        item.iniciar_espera_tacita()
        item.aprobar_tacitamente()
        assert item.aprobacion_cliente == EstadoAprobacion.APROBADO_TACITO
        assert item.esta_aprobado() is True

    def test_aprobar_explicitamente(self, item_costoso):
        item_costoso.aprobar_explicitamente()
        assert item_costoso.aprobacion_cliente == EstadoAprobacion.APROBADO_EXPLICITO
        assert item_costoso.esta_aprobado() is True

    def test_rechazar(self, item_costoso):
        item_costoso.rechazar()
        assert item_costoso.aprobacion_cliente == EstadoAprobacion.RECHAZADO
        assert item_costoso.esta_aprobado() is False

    def test_espera_no_expirada(self):
        item = ListaRepuestosOT(
            orden_trabajo_id="ot", repuesto_id="r", codigo="C",
            cantidad=1, precio_unitario=Decimal("65.00"), momento_agregado="en_ejecucion",
        )
        item.iniciar_espera_tacita()
        assert item.espera_expirada() is False

    def test_espera_expirada_forzada(self):
        item = ListaRepuestosOT(
            orden_trabajo_id="ot", repuesto_id="r", codigo="C",
            cantidad=1, precio_unitario=Decimal("65.00"), momento_agregado="en_ejecucion",
        )
        item.espera_hasta = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert item.espera_expirada() is True

    def test_espera_expirada_sin_espera_hasta(self, item_barato):
        assert item_barato.espera_expirada() is False

    def test_pendiente_no_aprobado(self, item_barato):
        assert item_barato.esta_aprobado() is False


# ── OrdenTrabajo ──────────────────────────────────────────────────────────────

class TestOrdenTrabajo:
    def test_crea_ot_en_abierta(self, ot_abierta):
        assert ot_abierta.estado == EstadoOrdenTrabajo.ABIERTA

    def test_agregar_repuesto_inicial(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        assert len(ot_abierta.lista_repuestos) == 1
        assert ot_abierta.monto_estimado == Decimal("25.00")

    def test_agregar_repuesto_inicial_fuera_abierta(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        with pytest.raises(DomainError):
            ot_abierta.agregar_repuesto_inicial(item_barato)

    def test_presentar_lista(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        assert ot_abierta.estado == EstadoOrdenTrabajo.LISTA_REPUESTOS

    def test_no_presentar_lista_vacia(self, ot_abierta):
        with pytest.raises(DomainError):
            ot_abierta.presentar_lista_al_cliente()

    def test_aprobar_lista_en_ejecucion(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        assert ot_abierta.estado == EstadoOrdenTrabajo.EN_EJECUCION
        assert ot_abierta.cliente_aprobo_lista is True

    def test_aprobar_lista_fuera_lista_repuestos_falla(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        with pytest.raises(DomainError):
            ot_abierta.aprobar_lista()

    def test_agregar_repuesto_en_ejecucion_automatico(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(
            ListaRepuestosOT(
                orden_trabajo_id=ot_abierta.id, repuesto_id="rp-x", codigo="X",
                cantidad=1, precio_unitario=Decimal("20"), momento_agregado="inicial",
            )
        )
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        item_adicional = ListaRepuestosOT(
            orden_trabajo_id=ot_abierta.id, repuesto_id="rp-001", codigo="REP-001",
            cantidad=1, precio_unitario=Decimal("20.00"), momento_agregado="en_ejecucion",
        )
        ot_abierta.agregar_repuesto_en_ejecucion(item_adicional)
        assert item_adicional.aprobacion_cliente == EstadoAprobacion.APROBADO_AUTOMATICO

    def test_agregar_repuesto_en_ejecucion_tacito(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        item_medio = ListaRepuestosOT(
            orden_trabajo_id=ot_abierta.id, repuesto_id="rp-m", codigo="M",
            cantidad=1, precio_unitario=Decimal("65.00"), momento_agregado="en_ejecucion",
        )
        ot_abierta.agregar_repuesto_en_ejecucion(item_medio)
        assert item_medio.aprobacion_cliente == EstadoAprobacion.PENDIENTE_ADICIONAL
        assert item_medio.tramo_precio == TramoAdicional.TACITO

    def test_agregar_repuesto_en_ejecucion_manual(self, ot_abierta, item_barato, item_costoso):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.agregar_repuesto_en_ejecucion(item_costoso)
        assert item_costoso.tramo_precio == TramoAdicional.MANUAL
        assert item_costoso.aprobacion_cliente == EstadoAprobacion.PENDIENTE_ADICIONAL

    def test_no_agregar_en_ejecucion_fuera_estado(self, ot_abierta, item_costoso):
        with pytest.raises(DomainError):
            ot_abierta.agregar_repuesto_en_ejecucion(item_costoso)

    def test_declarar_revision_final(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.declarar_revision_final(Decimal("80.00"), "mecanico-1")
        assert ot_abierta.estado == EstadoOrdenTrabajo.REVISION_FINAL
        assert ot_abierta.costo_mano_obra == Decimal("80.00")

    def test_revision_final_bloquea_con_pendiente_manual(self, ot_abierta, item_barato, item_costoso):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.agregar_repuesto_en_ejecucion(item_costoso)
        with pytest.raises(DomainError):
            ot_abierta.declarar_revision_final(Decimal("80.00"), "m-1")

    def test_revision_final_rechaza_mano_obra_negativa(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        with pytest.raises(DomainError):
            ot_abierta.declarar_revision_final(Decimal("-10.00"), "m-1")

    def test_revision_final_fuera_en_ejecucion_falla(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        with pytest.raises(DomainError):
            ot_abierta.declarar_revision_final(Decimal("50"), "m-1")

    def test_cerrar_con_cobro_y_lista(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.declarar_revision_final(Decimal("50"), "m-1")
        ot_abierta.confirmar_cobro()
        ot_abierta.cerrar()
        assert ot_abierta.estado == EstadoOrdenTrabajo.CERRADA

    def test_cerrar_sin_cobro_falla(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.declarar_revision_final(Decimal("50"), "m-1")
        with pytest.raises(CobroNoConfirmadoError):
            ot_abierta.cerrar()

    def test_cerrar_sin_lista_aprobada_falla(self):
        ot = OrdenTrabajo(
            vehiculo_id="v", mecanico_master_id="m",
            modalidad=ModalidadIntervencion.CORRECTIVO,
            urgencia=NivelUrgencia.ALTA,
        )
        ot.cobro_confirmado = True
        with pytest.raises(ListaNoConfirmadaError):
            ot.cerrar()

    def test_cancelar(self, ot_abierta):
        ot_abierta.cancelar()
        assert ot_abierta.estado == EstadoOrdenTrabajo.CANCELADA

    def test_no_cancelar_desde_cerrada(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.declarar_revision_final(Decimal("50"), "m-1")
        ot_abierta.confirmar_cobro()
        ot_abierta.cerrar()
        with pytest.raises(TransicionEstadoInvalidaError):
            ot_abierta.cancelar()

    def test_transicion_invalida_genérica(self, ot_abierta):
        with pytest.raises(TransicionEstadoInvalidaError):
            ot_abierta.avanzar_estado(EstadoOrdenTrabajo.CERRADA)

    def test_autorizar_precio_cliente(self, ot_abierta):
        ot_abierta.autorizar_precio_cliente()
        assert ot_abierta.visibilidad_precio_cliente is True

    def test_confirmar_cobro(self, ot_abierta):
        ot_abierta.confirmar_cobro()
        assert ot_abierta.cobro_confirmado is True

    def test_repuestos_aprobados(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        assert len(ot_abierta.repuestos_aprobados()) == 1

    def test_tiene_pendiente_manual(self, ot_abierta, item_barato, item_costoso):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.agregar_repuesto_en_ejecucion(item_costoso)
        assert ot_abierta.tiene_pendiente_manual() is True

    def test_no_tiene_pendiente_manual_sin_costosos(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        assert ot_abierta.tiene_pendiente_manual() is False

    def test_monto_total_con_mano_obra(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.declarar_revision_final(Decimal("80.00"), "m-1")
        assert ot_abierta.monto_total_con_mano_obra() == Decimal("105.00")

    def test_monto_total_sin_mano_obra(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        assert ot_abierta.monto_total_con_mano_obra() == Decimal("25.00")


# ── Entrada ───────────────────────────────────────────────────────────────────

class TestEntrada:
    def test_cerrar_activa(self):
        e = Entrada(vehiculo_id="v")
        e.cerrar()
        assert e.estado == EstadoEntrada.CERRADA

    def test_no_cerrar_ya_cerrada(self):
        e = Entrada(vehiculo_id="v")
        e.cerrar()
        with pytest.raises(DomainError):
            e.cerrar()


# ── TallerService ─────────────────────────────────────────────────────────────

class TestTallerService:
    def test_clasificar_automatico(self):
        assert TallerService.clasificar_tramo_adicional(Decimal("20")) == TramoAdicional.AUTOMATICO

    def test_clasificar_tacito(self):
        assert TallerService.clasificar_tramo_adicional(Decimal("50")) == TramoAdicional.TACITO

    def test_clasificar_manual(self):
        assert TallerService.clasificar_tramo_adicional(Decimal("150")) == TramoAdicional.MANUAL

    def test_lista_completamente_aprobada(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        assert TallerService.lista_completamente_aprobada(ot_abierta) is True

    def test_lista_no_aprobada(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        assert TallerService.lista_completamente_aprobada(ot_abierta) is False

    def test_lista_vacia_no_aprobada(self, ot_abierta):
        assert TallerService.lista_completamente_aprobada(ot_abierta) is False

    def test_calcular_monto_total(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.declarar_revision_final(Decimal("80.00"), "m")
        total = TallerService.calcular_monto_total(ot_abierta)
        assert total == Decimal("105.00")

    def test_puede_avanzar_a_revision_ok(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ok, _ = TallerService.puede_avanzar_a_revision(ot_abierta)
        assert ok is True

    def test_puede_avanzar_a_revision_falla_estado(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ok, motivo = TallerService.puede_avanzar_a_revision(ot_abierta)
        assert ok is False
        assert "EN_EJECUCION" in motivo

    def test_puede_avanzar_a_revision_falla_pendiente_manual(self, ot_abierta, item_barato, item_costoso):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        ot_abierta.agregar_repuesto_en_ejecucion(item_costoso)
        ok, motivo = TallerService.puede_avanzar_a_revision(ot_abierta)
        assert ok is False

    def test_items_con_espera_expirada(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        item_medio = ListaRepuestosOT(
            orden_trabajo_id=ot_abierta.id, repuesto_id="rp-m", codigo="M",
            cantidad=1, precio_unitario=Decimal("65.00"), momento_agregado="en_ejecucion",
        )
        ot_abierta.agregar_repuesto_en_ejecucion(item_medio)
        item_medio.espera_hasta = datetime.now(timezone.utc) - timedelta(seconds=1)
        expirados = TallerService.items_con_espera_expirada(ot_abierta)
        assert len(expirados) == 1

    def test_verificar_consumo_registrado_con_repuestos(self, ot_abierta, item_barato):
        ot_abierta.agregar_repuesto_inicial(item_barato)
        ot_abierta.presentar_lista_al_cliente()
        ot_abierta.aprobar_lista()
        assert TallerService.verificar_consumo_registrado(ot_abierta) is True

    def test_verificar_consumo_registrado_sin_lista_pero_con_mano_obra(self, ot_abierta):
        ot_abierta.costo_mano_obra = Decimal("50.00")
        assert TallerService.verificar_consumo_registrado(ot_abierta) is True

    def test_verificar_consumo_no_registrado(self, ot_abierta):
        assert TallerService.verificar_consumo_registrado(ot_abierta) is False

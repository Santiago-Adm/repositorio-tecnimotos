"""
Tests unitarios — modelos y servicio de dominio del módulo pedidos.
Meta: ≥ 90% branch coverage (09 §3.2).
"""
import pytest
from datetime import timedelta
from decimal import Decimal

from src.pedidos.domain.models.pedido import (
    Comprobante,
    DeudaActiva,
    DomainError,
    Envio,
    EstadoComprobante,
    EstadoEnvio,
    EstadoListaReserva,
    EstadoPedido,
    EstadoProforma,
    EstadoReserva,
    ListaReservaProg,
    ListaReservaProg_Item,
    Pedido,
    PedidoItem,
    Proforma,
    Reserva,
    SegmentoCliente,
    TipoComprobante,
    TransicionEstadoInvalidaError,
    ttl_para_segmento,
)
from src.pedidos.domain.services.pedido_service import PedidoService


# ── TTL por segmento ──────────────────────────────────────────────────────────

class TestTTLSegmento:
    def test_conductor_un_dia(self):
        assert ttl_para_segmento(SegmentoCliente.CONDUCTOR) == timedelta(days=1)

    def test_flota_dueno_un_dia(self):
        assert ttl_para_segmento(SegmentoCliente.FLOTA_DUENO) == timedelta(days=1)

    def test_flota_conductor_un_dia(self):
        assert ttl_para_segmento(SegmentoCliente.FLOTA_CONDUCTOR) == timedelta(days=1)

    def test_distrito_tres_dias(self):
        assert ttl_para_segmento(SegmentoCliente.DISTRITO) == timedelta(days=3)

    def test_rural_tres_dias(self):
        assert ttl_para_segmento(SegmentoCliente.RURAL) == timedelta(days=3)

    def test_motolineal_dos_dias(self):
        assert ttl_para_segmento(SegmentoCliente.MOTOLINEAL) == timedelta(days=2)


# ── PedidoItem ────────────────────────────────────────────────────────────────

class TestPedidoItem:
    def test_crea_item_valido(self):
        item = PedidoItem(
            pedido_id="ped-1",
            repuesto_id="rp-1",
            codigo="REP-001",
            cantidad=2,
            precio_unitario=Decimal("45.00"),
        )
        assert item.subtotal == Decimal("90.00")

    def test_subtotal_con_precio_ajustado(self):
        item = PedidoItem(
            pedido_id="ped-1",
            repuesto_id="rp-1",
            codigo="REP-001",
            cantidad=2,
            precio_unitario=Decimal("45.00"),
            precio_ajustado_unit=Decimal("40.00"),
        )
        assert item.subtotal == Decimal("80.00")

    def test_rechaza_cantidad_cero(self):
        with pytest.raises(DomainError):
            PedidoItem(pedido_id="p", repuesto_id="r", codigo="C", cantidad=0, precio_unitario=Decimal("10"))

    def test_rechaza_precio_cero(self):
        with pytest.raises(DomainError):
            PedidoItem(pedido_id="p", repuesto_id="r", codigo="C", cantidad=1, precio_unitario=Decimal("0"))


# ── Pedido ────────────────────────────────────────────────────────────────────

class TestPedido:
    def test_crea_pedido_en_borrador(self):
        p = Pedido(canal_origen="presencial", origen_actor="user-1")
        assert p.estado == EstadoPedido.BORRADOR
        assert p.monto_total == Decimal("0")

    def test_rechaza_canal_vacio(self):
        with pytest.raises(DomainError):
            Pedido(canal_origen="", origen_actor="user-1")

    def test_agregar_item_en_borrador(self, pedido_borrador):
        assert len(pedido_borrador.items) == 1
        assert pedido_borrador.monto_total == Decimal("90.00")

    def test_no_agregar_item_fuera_borrador(self, pedido_borrador):
        pedido_borrador.confirmar()
        with pytest.raises(DomainError):
            pedido_borrador.agregar_item(
                PedidoItem(pedido_id=pedido_borrador.id, repuesto_id="r", codigo="C", cantidad=1, precio_unitario=Decimal("10"))
            )

    def test_confirmar(self, pedido_borrador):
        pedido_borrador.confirmar()
        assert pedido_borrador.estado == EstadoPedido.CONFIRMADO

    def test_cancelar_desde_borrador(self, pedido_borrador):
        pedido_borrador.cancelar("cliente canceló")
        assert pedido_borrador.estado == EstadoPedido.CANCELADO
        assert pedido_borrador.motivo_cancelacion == "cliente canceló"

    def test_cancelar_desde_confirmado(self, pedido_borrador):
        pedido_borrador.confirmar()
        pedido_borrador.cancelar("sin stock")
        assert pedido_borrador.estado == EstadoPedido.CANCELADO

    def test_no_cancelar_desde_despachado(self, pedido_borrador):
        pedido_borrador.confirmar()
        pedido_borrador.avanzar_estado(EstadoPedido.EN_PREPARACION)
        pedido_borrador.despachar()
        with pytest.raises(TransicionEstadoInvalidaError):
            pedido_borrador.cancelar("tarde")

    def test_entregar_desde_despachado(self, pedido_borrador):
        pedido_borrador.confirmar()
        pedido_borrador.avanzar_estado(EstadoPedido.EN_PREPARACION)
        pedido_borrador.despachar()
        pedido_borrador.entregar()
        assert pedido_borrador.estado == EstadoPedido.ENTREGADO

    def test_no_transicion_desde_entregado(self, pedido_borrador):
        pedido_borrador.confirmar()
        pedido_borrador.avanzar_estado(EstadoPedido.EN_PREPARACION)
        pedido_borrador.despachar()
        pedido_borrador.entregar()
        with pytest.raises(TransicionEstadoInvalidaError):
            pedido_borrador.cancelar("no puede")

    def test_registrar_incidencia(self, pedido_borrador):
        pedido_borrador.confirmar()
        pedido_borrador.avanzar_estado(EstadoPedido.EN_PREPARACION)
        pedido_borrador.despachar()
        pedido_borrador.registrar_incidencia()
        assert pedido_borrador.estado == EstadoPedido.INCIDENCIA

    def test_entregar_desde_incidencia(self, pedido_borrador):
        pedido_borrador.confirmar()
        pedido_borrador.avanzar_estado(EstadoPedido.EN_PREPARACION)
        pedido_borrador.despachar()
        pedido_borrador.registrar_incidencia()
        pedido_borrador.entregar()
        assert pedido_borrador.estado == EstadoPedido.ENTREGADO

    def test_aplicar_descuento(self, pedido_borrador):
        pedido_borrador.aplicar_descuento(Decimal("10.00"), Decimal("80.00"))
        assert pedido_borrador.descuento_aplicado == Decimal("10.00")
        assert pedido_borrador.monto_efectivo() == Decimal("80.00")

    def test_descuento_negativo_rechazado(self, pedido_borrador):
        with pytest.raises(DomainError):
            pedido_borrador.aplicar_descuento(Decimal("-5.00"), Decimal("95.00"))

    def test_descuento_fuera_borrador_rechazado(self, pedido_borrador):
        pedido_borrador.confirmar()
        with pytest.raises(DomainError):
            pedido_borrador.aplicar_descuento(Decimal("5.00"), Decimal("85.00"))

    def test_monto_efectivo_sin_descuento(self, pedido_borrador):
        assert pedido_borrador.monto_efectivo() == Decimal("90.00")

    def test_esta_cancelado_true(self, pedido_borrador):
        pedido_borrador.cancelar("test")
        assert pedido_borrador.esta_cancelado() is True

    def test_esta_cancelado_false(self, pedido_borrador):
        assert pedido_borrador.esta_cancelado() is False

    def test_esta_entregado(self, pedido_borrador):
        assert pedido_borrador.esta_entregado() is False

    def test_transicion_invalida_genérica(self, pedido_borrador):
        with pytest.raises(TransicionEstadoInvalidaError):
            pedido_borrador.avanzar_estado(EstadoPedido.ENTREGADO)


# ── Reserva ───────────────────────────────────────────────────────────────────

class TestReserva:
    def test_crea_reserva_conductor(self, reserva_conductor):
        assert reserva_conductor.estado == EstadoReserva.ACTIVA
        assert reserva_conductor.expira_en > reserva_conductor.created_at

    def test_ttl_conductor_un_dia(self, reserva_conductor):
        delta = reserva_conductor.expira_en - reserva_conductor.created_at
        assert delta == timedelta(days=1)

    def test_ttl_distrito_tres_dias(self):
        r = Reserva(
            cliente_id="cli-1", repuesto_id="rp-1",
            cantidad=2, segmento=SegmentoCliente.DISTRITO,
        )
        delta = r.expira_en - r.created_at
        assert delta == timedelta(days=3)

    def test_ttl_rural_tres_dias(self):
        r = Reserva(
            cliente_id="cli-1", repuesto_id="rp-1",
            cantidad=2, segmento=SegmentoCliente.RURAL,
        )
        assert (r.expira_en - r.created_at) == timedelta(days=3)

    def test_ttl_motolineal_dos_dias(self):
        r = Reserva(
            cliente_id="cli-1", repuesto_id="rp-1",
            cantidad=2, segmento=SegmentoCliente.MOTOLINEAL,
        )
        assert (r.expira_en - r.created_at) == timedelta(days=2)

    def test_rechaza_cantidad_cero(self):
        with pytest.raises(DomainError):
            Reserva(cliente_id="c", repuesto_id="r", cantidad=0, segmento=SegmentoCliente.CONDUCTOR)

    def test_esta_vigente(self, reserva_conductor):
        assert reserva_conductor.esta_vigente() is True

    def test_confirmar(self, reserva_conductor):
        reserva_conductor.confirmar()
        assert reserva_conductor.estado == EstadoReserva.CONFIRMADA

    def test_liberar_desde_activa(self, reserva_conductor):
        reserva_conductor.liberar()
        assert reserva_conductor.estado == EstadoReserva.LIBERADA

    def test_liberar_desde_confirmada(self, reserva_conductor):
        reserva_conductor.confirmar()
        reserva_conductor.liberar()
        assert reserva_conductor.estado == EstadoReserva.LIBERADA

    def test_expirar(self, reserva_conductor):
        reserva_conductor.expirar()
        assert reserva_conductor.estado == EstadoReserva.EXPIRADA

    def test_no_transicion_desde_liberada(self, reserva_conductor):
        reserva_conductor.liberar()
        with pytest.raises(TransicionEstadoInvalidaError):
            reserva_conductor.expirar()

    def test_no_transicion_desde_expirada(self, reserva_conductor):
        reserva_conductor.expirar()
        with pytest.raises(TransicionEstadoInvalidaError):
            reserva_conductor.liberar()


# ── Proforma ──────────────────────────────────────────────────────────────────

class TestProforma:
    def test_crea_proforma_valida(self):
        p = Proforma(pedido_id="ped-1", numero_referencia="PRF-001", monto_total=Decimal("100.00"))
        assert p.estado == EstadoProforma.BORRADOR

    def test_rechaza_monto_cero(self):
        with pytest.raises(DomainError):
            Proforma(pedido_id="p", numero_referencia="PRF-001", monto_total=Decimal("0"))

    def test_rechaza_referencia_vacia(self):
        with pytest.raises(DomainError):
            Proforma(pedido_id="p", numero_referencia="  ", monto_total=Decimal("10"))

    def test_enviar(self):
        p = Proforma(pedido_id="ped-1", numero_referencia="PRF-001", monto_total=Decimal("50.00"))
        p.enviar()
        assert p.estado == EstadoProforma.ENVIADA

    def test_no_enviar_dos_veces(self):
        p = Proforma(pedido_id="ped-1", numero_referencia="PRF-001", monto_total=Decimal("50.00"))
        p.enviar()
        with pytest.raises(TransicionEstadoInvalidaError):
            p.enviar()


# ── Envio ─────────────────────────────────────────────────────────────────────

class TestEnvio:
    def test_crea_envio_valido(self):
        e = Envio(pedido_id="p", empresa_encomienda="Olva", direccion_destino="Huancayo")
        assert e.estado == EstadoEnvio.PREPARADO

    def test_rechaza_empresa_vacia(self):
        with pytest.raises(DomainError):
            Envio(pedido_id="p", empresa_encomienda="", direccion_destino="Huancayo")

    def test_rechaza_direccion_vacia(self):
        with pytest.raises(DomainError):
            Envio(pedido_id="p", empresa_encomienda="Olva", direccion_destino="")

    def test_avanzar_estado_valido(self):
        e = Envio(pedido_id="p", empresa_encomienda="Olva", direccion_destino="Huancayo")
        e.avanzar_estado(EstadoEnvio.ENTREGADO_AGENCIA)
        assert e.estado == EstadoEnvio.ENTREGADO_AGENCIA

    def test_avanzar_estado_invalido(self):
        e = Envio(pedido_id="p", empresa_encomienda="Olva", direccion_destino="Huancayo")
        with pytest.raises(TransicionEstadoInvalidaError):
            e.avanzar_estado(EstadoEnvio.ENTREGADO_CLIENTE)

    def test_flujo_completo(self):
        e = Envio(pedido_id="p", empresa_encomienda="Olva", direccion_destino="Huancayo")
        e.avanzar_estado(EstadoEnvio.ENTREGADO_AGENCIA)
        e.avanzar_estado(EstadoEnvio.EN_TRANSITO)
        e.avanzar_estado(EstadoEnvio.ENTREGADO_CLIENTE)
        assert e.estado == EstadoEnvio.ENTREGADO_CLIENTE

    def test_incidencia_y_resolucion(self):
        e = Envio(pedido_id="p", empresa_encomienda="Olva", direccion_destino="Huancayo")
        e.avanzar_estado(EstadoEnvio.ENTREGADO_AGENCIA)
        e.avanzar_estado(EstadoEnvio.INCIDENCIA)
        e.avanzar_estado(EstadoEnvio.RESUELTO)
        assert e.estado == EstadoEnvio.RESUELTO


# ── Comprobante ───────────────────────────────────────────────────────────────

class TestComprobante:
    def test_crea_en_pendiente_validacion(self):
        c = Comprobante(
            pedido_id="p", tipo=TipoComprobante.BOLETA,
            monto=Decimal("75.00"), emitido_por="vendedor-1",
        )
        assert c.estado == EstadoComprobante.PENDIENTE_VALIDACION

    def test_rechaza_monto_cero(self):
        with pytest.raises(DomainError):
            Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("0"), emitido_por="v")

    def test_aprobar(self):
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        c.aprobar()
        assert c.estado == EstadoComprobante.EMITIDO
        assert c.esta_emitido() is True

    def test_no_aprobar_desde_emitido(self):
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        c.aprobar()
        with pytest.raises(TransicionEstadoInvalidaError):
            c.aprobar()

    def test_marcar_enviado(self):
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        c.aprobar()
        c.marcar_enviado()
        assert c.estado == EstadoComprobante.ENVIADO_CLIENTE

    def test_no_marcar_enviado_desde_pendiente(self):
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        with pytest.raises(TransicionEstadoInvalidaError):
            c.marcar_enviado()

    def test_anular_desde_emitido(self):
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        c.aprobar()
        c.anular("nota-001")
        assert c.estado == EstadoComprobante.ANULADO
        assert c.nota_credito_id == "nota-001"

    def test_anular_desde_enviado_cliente(self):
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        c.aprobar()
        c.marcar_enviado()
        c.anular("nota-002")
        assert c.estado == EstadoComprobante.ANULADO

    def test_no_anular_desde_pendiente(self):
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        with pytest.raises(TransicionEstadoInvalidaError):
            c.anular("nota")

    def test_esta_emitido_false_cuando_pendiente(self):
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        assert c.esta_emitido() is False


# ── DeudaActiva ───────────────────────────────────────────────────────────────

class TestDeudaActiva:
    def test_crea_deuda_valida(self):
        d = DeudaActiva(pedido_id="p", cliente_id="c", monto_deuda=Decimal("50.00"), plazo_dias=7)
        assert d.vence_en > d.created_at

    def test_rechaza_monto_cero(self):
        with pytest.raises(DomainError):
            DeudaActiva(pedido_id="p", cliente_id="c", monto_deuda=Decimal("0"), plazo_dias=7)

    def test_rechaza_plazo_cero(self):
        with pytest.raises(DomainError):
            DeudaActiva(pedido_id="p", cliente_id="c", monto_deuda=Decimal("10"), plazo_dias=0)

    def test_alertas_calculadas(self):
        d = DeudaActiva(pedido_id="p", cliente_id="c", monto_deuda=Decimal("50"), plazo_dias=6)
        assert d.alerta_50_en < d.alerta_vencimiento_en < d.vence_en


# ── ListaReservaProg ──────────────────────────────────────────────────────────

class TestListaReservaProg:
    def test_crea_lista(self):
        lista = ListaReservaProg(cliente_id="cli-1")
        assert lista.estado == EstadoListaReserva.BORRADOR

    def test_agregar_item(self):
        lista = ListaReservaProg(cliente_id="cli-1")
        lista.agregar_item(ListaReservaProg_Item(
            lista_id=lista.id, repuesto_id="rp-1", codigo="R",
            cantidad=2, precio_referencia=Decimal("30.00"),
        ))
        assert len(lista.items) == 1

    def test_no_agregar_item_fuera_borrador(self):
        lista = ListaReservaProg(cliente_id="cli-1")
        lista.agregar_item(ListaReservaProg_Item(
            lista_id=lista.id, repuesto_id="rp-1", codigo="R",
            cantidad=1, precio_referencia=Decimal("10.00"),
        ))
        lista.confirmar()
        with pytest.raises(DomainError):
            lista.agregar_item(ListaReservaProg_Item(
                lista_id=lista.id, repuesto_id="rp-2", codigo="R2",
                cantidad=1, precio_referencia=Decimal("20.00"),
            ))

    def test_confirmar_sin_items_falla(self):
        lista = ListaReservaProg(cliente_id="cli-1")
        with pytest.raises(DomainError):
            lista.confirmar()

    def test_formalizar(self):
        lista = ListaReservaProg(cliente_id="cli-1")
        lista.agregar_item(ListaReservaProg_Item(
            lista_id=lista.id, repuesto_id="rp-1", codigo="R",
            cantidad=1, precio_referencia=Decimal("10.00"),
        ))
        lista.confirmar()
        lista.formalizar()
        assert lista.estado == EstadoListaReserva.FORMALIZADA

    def test_no_formalizar_desde_borrador(self):
        lista = ListaReservaProg(cliente_id="cli-1")
        lista.agregar_item(ListaReservaProg_Item(
            lista_id=lista.id, repuesto_id="rp-1", codigo="R",
            cantidad=1, precio_referencia=Decimal("10.00"),
        ))
        with pytest.raises(TransicionEstadoInvalidaError):
            lista.formalizar()

    def test_item_cantidad_cero_falla(self):
        with pytest.raises(DomainError):
            ListaReservaProg_Item(
                lista_id="l", repuesto_id="r", codigo="C",
                cantidad=0, precio_referencia=Decimal("10.00"),
            )


# ── PedidoService ─────────────────────────────────────────────────────────────

class TestPedidoService:
    def test_cancelacion_permitida_cliente_borrador(self, pedido_borrador):
        PedidoService.verificar_cancelacion_permitida(pedido_borrador, es_cliente=True)

    def test_cancelacion_prohibida_cliente_confirmado(self, pedido_borrador):
        pedido_borrador.confirmar()
        with pytest.raises(DomainError):
            PedidoService.verificar_cancelacion_permitida(pedido_borrador, es_cliente=True)

    def test_cancelacion_permitida_interno_cualquier_estado(self, pedido_borrador):
        pedido_borrador.confirmar()
        PedidoService.verificar_cancelacion_permitida(pedido_borrador, es_cliente=False)

    def test_pago_completo(self):
        ok, deuda = PedidoService.verificar_pago_minimo(Decimal("100"), Decimal("100"))
        assert ok is True
        assert deuda == Decimal("0")

    def test_pago_80_con_aprobacion(self):
        ok, deuda = PedidoService.verificar_pago_minimo(
            Decimal("100"), Decimal("85"), tiene_aprobacion_conjunta=True
        )
        assert ok is True
        assert deuda == Decimal("15")

    def test_pago_70_sin_aprobacion(self):
        ok, deuda = PedidoService.verificar_pago_minimo(Decimal("100"), Decimal("70"))
        assert ok is False
        assert deuda == Decimal("30")

    def test_pago_80_sin_aprobacion_falla(self):
        ok, deuda = PedidoService.verificar_pago_minimo(
            Decimal("100"), Decimal("85"), tiene_aprobacion_conjunta=False
        )
        assert ok is False

    def test_tramo_automatico(self):
        assert PedidoService.determinar_tipo_tramo(Decimal("20.00")) == "automatico"

    def test_tramo_tacito_limite_exacto(self):
        assert PedidoService.determinar_tipo_tramo(Decimal("30.00")) == "tacito"

    def test_tramo_tacito(self):
        assert PedidoService.determinar_tipo_tramo(Decimal("65.00")) == "tacito"

    def test_tramo_manual(self):
        assert PedidoService.determinar_tipo_tramo(Decimal("150.00")) == "manual"

    def test_vendedor_requiere_validacion(self):
        assert PedidoService.comprobante_requiere_validacion("VENDEDOR") is True

    def test_administrador_no_requiere_validacion(self):
        assert PedidoService.comprobante_requiere_validacion("ADMINISTRADOR") is False

    def test_superadmin_no_requiere_validacion(self):
        assert PedidoService.comprobante_requiere_validacion("SUPERADMIN") is False

    def test_tipo_boleta_sin_ruc(self):
        t = PedidoService.determinar_tipo_comprobante(Decimal("50"), tiene_ruc=False)
        from src.pedidos.domain.models.pedido import TipoComprobante
        assert t == TipoComprobante.BOLETA

    def test_tipo_factura_con_ruc_alto(self):
        t = PedidoService.determinar_tipo_comprobante(Decimal("100"), tiene_ruc=True)
        from src.pedidos.domain.models.pedido import TipoComprobante
        assert t == TipoComprobante.FACTURA

    def test_tipo_ticket_bajo_umbral(self):
        t = PedidoService.determinar_tipo_comprobante(Decimal("15"), tiene_ruc=False)
        from src.pedidos.domain.models.pedido import TipoComprobante
        assert t == TipoComprobante.TICKET

    def test_reserva_libera_stock_activa(self, reserva_conductor):
        assert PedidoService.reserva_libera_stock(reserva_conductor) is True

    def test_reserva_no_libera_stock_expirada(self, reserva_conductor):
        reserva_conductor.expirar()
        assert PedidoService.reserva_libera_stock(reserva_conductor) is False

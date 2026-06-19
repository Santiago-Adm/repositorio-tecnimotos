"""
Tests unitarios — modelos y servicio de dominio del módulo stock.
Cubre StockRepuesto, Reabastecimiento, MovimientoStock, ReabastecimientoItem,
StockService. Meta: ≥ 95% branch coverage (09 §3.3).
"""
import pytest
from decimal import Decimal

from src.stock.domain.models.stock import (
    DomainError,
    EstadoReabastecimiento,
    MovimientoStock,
    Reabastecimiento,
    ReabastecimientoItem,
    StockInsuficienteError,
    StockRepuesto,
    TipoMovimiento,
    TransicionEstadoInvalidaError,
)
from src.stock.domain.services.stock_service import StockService


# ── MovimientoStock ───────────────────────────────────────────────────────────

class TestMovimientoStock:
    def test_crea_movimiento_valido(self):
        m = MovimientoStock(
            repuesto_id="rp-1",
            tipo_movimiento=TipoMovimiento.SALIDA_VENTA,
            cantidad=5,
            estado_origen="disponible",
            estado_destino="descontado",
            actor_id="user-1",
        )
        assert m.cantidad == 5

    def test_rechaza_cantidad_cero(self):
        with pytest.raises(DomainError):
            MovimientoStock(
                repuesto_id="rp-1",
                tipo_movimiento=TipoMovimiento.SALIDA_VENTA,
                cantidad=0,
                estado_origen="disponible",
                estado_destino="descontado",
                actor_id="user-1",
            )

    def test_rechaza_cantidad_negativa(self):
        with pytest.raises(DomainError):
            MovimientoStock(
                repuesto_id="rp-1",
                tipo_movimiento=TipoMovimiento.SALIDA_VENTA,
                cantidad=-3,
                estado_origen="disponible",
                estado_destino="descontado",
                actor_id="user-1",
            )


# ── ReabastecimientoItem ──────────────────────────────────────────────────────

class TestReabastecimientoItem:
    def test_crea_item_valido(self):
        item = ReabastecimientoItem(
            repuesto_id="rp-1",
            codigo="REP-001",
            cantidad_solicitada=10,
            precio_costo_unitario=Decimal("25.00"),
        )
        assert item.cantidad_solicitada == 10

    def test_rechaza_cantidad_cero(self):
        with pytest.raises(DomainError):
            ReabastecimientoItem(
                repuesto_id="rp-1",
                codigo="REP-001",
                cantidad_solicitada=0,
                precio_costo_unitario=Decimal("25.00"),
            )

    def test_rechaza_precio_cero(self):
        with pytest.raises(DomainError):
            ReabastecimientoItem(
                repuesto_id="rp-1",
                codigo="REP-001",
                cantidad_solicitada=5,
                precio_costo_unitario=Decimal("0"),
            )

    def test_rechaza_precio_negativo(self):
        with pytest.raises(DomainError):
            ReabastecimientoItem(
                repuesto_id="rp-1",
                codigo="REP-001",
                cantidad_solicitada=5,
                precio_costo_unitario=Decimal("-1.00"),
            )


# ── StockRepuesto ─────────────────────────────────────────────────────────────

class TestStockRepuesto:
    def test_crea_stock_valido(self, stock_filtro):
        assert stock_filtro.cantidad_disponible == 20
        assert stock_filtro.codigo == "REP-001"

    def test_rechaza_disponible_negativo(self):
        with pytest.raises(DomainError):
            StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_disponible=-1)

    def test_rechaza_apartado_negativo(self):
        with pytest.raises(DomainError):
            StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_apartada=-1)

    def test_stock_total_suma_tres_cantidades(self, stock_filtro):
        # disponible=20, apartada=0, en_transito=5
        assert stock_filtro.stock_total() == 25

    def test_esta_agotado_true(self, stock_agotado):
        assert stock_agotado.esta_agotado() is True

    def test_esta_agotado_false(self, stock_filtro):
        assert stock_filtro.esta_agotado() is False

    def test_esta_bajo_umbral_sin_umbral(self):
        s = StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_disponible=1, umbral_minimo=0)
        assert s.esta_bajo_umbral() is False

    def test_esta_bajo_umbral_por_debajo(self, stock_cadena):
        # disponible=3, umbral=5 → bajo umbral
        assert stock_cadena.esta_bajo_umbral() is True

    def test_esta_bajo_umbral_encima(self, stock_filtro):
        # disponible=20, umbral=5
        assert stock_filtro.esta_bajo_umbral() is False

    def test_registrar_entrada(self, stock_filtro):
        antes = stock_filtro.cantidad_disponible
        mov = stock_filtro.registrar_entrada(10, actor_id="user-1", referencia_id="reab-1")
        assert stock_filtro.cantidad_disponible == antes + 10
        assert mov.tipo_movimiento == TipoMovimiento.ENTRADA_REABASTECIMIENTO
        assert len(stock_filtro.movimientos) == 1

    def test_registrar_entrada_rechaza_cero(self, stock_filtro):
        with pytest.raises(DomainError):
            stock_filtro.registrar_entrada(0, actor_id="user-1")

    def test_apartar_reduce_disponible_y_aumenta_apartado(self, stock_filtro):
        stock_filtro.apartar(5, actor_id="user-1", referencia_id="ped-1")
        assert stock_filtro.cantidad_disponible == 15
        assert stock_filtro.cantidad_apartada == 5

    def test_apartar_rechaza_cero(self, stock_filtro):
        with pytest.raises(DomainError):
            stock_filtro.apartar(0, actor_id="user-1")

    def test_apartar_rechaza_insuficiente(self, stock_agotado):
        with pytest.raises(StockInsuficienteError):
            stock_agotado.apartar(1, actor_id="user-1")

    def test_liberar_apartado_correcto(self, stock_cadena):
        # apartado=2
        stock_cadena.liberar_apartado(2, actor_id="user-1")
        assert stock_cadena.cantidad_apartada == 0
        assert stock_cadena.cantidad_disponible == 5

    def test_liberar_apartado_rechaza_cero(self, stock_cadena):
        with pytest.raises(DomainError):
            stock_cadena.liberar_apartado(0, actor_id="user-1")

    def test_liberar_apartado_rechaza_mas_de_lo_apartado(self, stock_cadena):
        # apartado=2, intentamos liberar 3
        with pytest.raises(DomainError):
            stock_cadena.liberar_apartado(3, actor_id="user-1")

    def test_descontar_venta_correcto(self, stock_filtro):
        mov = stock_filtro.descontar_venta(5, actor_id="user-1")
        assert stock_filtro.cantidad_disponible == 15
        assert mov.tipo_movimiento == TipoMovimiento.SALIDA_VENTA

    def test_descontar_venta_rechaza_cero(self, stock_filtro):
        with pytest.raises(DomainError):
            stock_filtro.descontar_venta(0, actor_id="user-1")

    def test_descontar_venta_rechaza_insuficiente(self, stock_agotado):
        with pytest.raises(StockInsuficienteError):
            stock_agotado.descontar_venta(1, actor_id="user-1")

    def test_descontar_apartado_taller_correcto(self, stock_cadena):
        # apartado=2
        mov = stock_cadena.descontar_apartado_taller(2, actor_id="user-1", referencia_id="ot-1")
        assert stock_cadena.cantidad_apartada == 0
        assert mov.tipo_movimiento == TipoMovimiento.SALIDA_TALLER

    def test_descontar_apartado_taller_rechaza_cero(self, stock_cadena):
        with pytest.raises(DomainError):
            stock_cadena.descontar_apartado_taller(0, actor_id="user-1")

    def test_descontar_apartado_taller_rechaza_insuficiente(self, stock_filtro):
        # apartado=0
        with pytest.raises(StockInsuficienteError):
            stock_filtro.descontar_apartado_taller(1, actor_id="user-1")

    def test_ajustar_umbral_correcto(self, stock_filtro):
        stock_filtro.ajustar_umbral(10)
        assert stock_filtro.umbral_minimo == 10

    def test_ajustar_umbral_a_cero(self, stock_filtro):
        stock_filtro.ajustar_umbral(0)
        assert stock_filtro.umbral_minimo == 0

    def test_ajustar_umbral_rechaza_negativo(self, stock_filtro):
        with pytest.raises(DomainError):
            stock_filtro.ajustar_umbral(-1)

    def test_descontar_venta_tipo_taller(self, stock_filtro):
        mov = stock_filtro.descontar_venta(
            2, actor_id="user-1", tipo=TipoMovimiento.SALIDA_TALLER
        )
        assert mov.tipo_movimiento == TipoMovimiento.SALIDA_TALLER

    def test_apartar_registra_movimiento(self, stock_filtro):
        stock_filtro.apartar(3, actor_id="user-1", referencia_id="ped-1")
        assert len(stock_filtro.movimientos) == 1
        mov = stock_filtro.movimientos[0]
        assert mov.tipo_movimiento == TipoMovimiento.RESERVA
        assert mov.referencia_id == "ped-1"

    def test_liberar_apartado_registra_movimiento(self, stock_cadena):
        stock_cadena.liberar_apartado(1, actor_id="user-1", referencia_id="lib-1")
        assert len(stock_cadena.movimientos) == 1
        assert stock_cadena.movimientos[0].tipo_movimiento == TipoMovimiento.LIBERACION_RESERVA


# ── Reabastecimiento ──────────────────────────────────────────────────────────

class TestReabastecimiento:
    def test_crea_reabastecimiento_valido(self, reab_basico):
        assert reab_basico.proveedor == "Bajaj Perú"
        assert reab_basico.estado == EstadoReabastecimiento.SOLICITADO
        assert len(reab_basico.items) == 1

    def test_rechaza_proveedor_vacio(self):
        with pytest.raises(DomainError):
            Reabastecimiento(proveedor="", solicitado_por="user-1")

    def test_rechaza_proveedor_solo_espacios(self):
        with pytest.raises(DomainError):
            Reabastecimiento(proveedor="   ", solicitado_por="user-1")

    def test_avanzar_estado_solicitado_a_confirmado(self, reab_basico):
        reab_basico.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)
        assert reab_basico.estado == EstadoReabastecimiento.CONFIRMADO_PROVEEDOR

    def test_avanzar_estado_solicitado_a_cancelado(self, reab_basico):
        reab_basico.avanzar_estado(EstadoReabastecimiento.CANCELADO)
        assert reab_basico.estado == EstadoReabastecimiento.CANCELADO

    def test_avanzar_estado_confirmado_a_en_transito(self, reab_basico):
        reab_basico.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)
        reab_basico.avanzar_estado(EstadoReabastecimiento.EN_TRANSITO)
        assert reab_basico.estado == EstadoReabastecimiento.EN_TRANSITO

    def test_avanzar_estado_confirmado_a_cancelado(self, reab_basico):
        reab_basico.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)
        reab_basico.avanzar_estado(EstadoReabastecimiento.CANCELADO)
        assert reab_basico.esta_cancelado() is True

    def test_avanzar_estado_en_transito_a_recibido(self, reab_basico):
        reab_basico.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)
        reab_basico.avanzar_estado(EstadoReabastecimiento.EN_TRANSITO)
        reab_basico.avanzar_estado(EstadoReabastecimiento.RECIBIDO)
        assert reab_basico.esta_recibido() is True

    def test_avanzar_estado_invalido_lanza_error(self, reab_basico):
        with pytest.raises(TransicionEstadoInvalidaError):
            reab_basico.avanzar_estado(EstadoReabastecimiento.RECIBIDO)

    def test_estado_recibido_no_permite_transicion(self, reab_basico):
        reab_basico.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)
        reab_basico.avanzar_estado(EstadoReabastecimiento.EN_TRANSITO)
        reab_basico.avanzar_estado(EstadoReabastecimiento.RECIBIDO)
        with pytest.raises(TransicionEstadoInvalidaError):
            reab_basico.avanzar_estado(EstadoReabastecimiento.CANCELADO)

    def test_estado_cancelado_no_permite_transicion(self, reab_basico):
        reab_basico.avanzar_estado(EstadoReabastecimiento.CANCELADO)
        with pytest.raises(TransicionEstadoInvalidaError):
            reab_basico.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)

    def test_agregar_item_en_estado_solicitado(self, reab_basico):
        reab_basico.agregar_item(
            ReabastecimientoItem(
                repuesto_id="rp-2",
                codigo="REP-002",
                cantidad_solicitada=5,
                precio_costo_unitario=Decimal("15.00"),
            )
        )
        assert len(reab_basico.items) == 2

    def test_agregar_item_fuera_de_solicitado_falla(self, reab_basico):
        reab_basico.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)
        with pytest.raises(DomainError):
            reab_basico.agregar_item(
                ReabastecimientoItem(
                    repuesto_id="rp-2",
                    codigo="REP-002",
                    cantidad_solicitada=5,
                    precio_costo_unitario=Decimal("15.00"),
                )
            )

    def test_esta_recibido_false_cuando_solicitado(self, reab_basico):
        assert reab_basico.esta_recibido() is False

    def test_esta_cancelado_false_cuando_solicitado(self, reab_basico):
        assert reab_basico.esta_cancelado() is False


# ── StockService ──────────────────────────────────────────────────────────────

class TestStockService:
    def test_validar_no_negativo_ok(self, stock_filtro):
        StockService.validar_no_negativo(stock_filtro)

    def test_validar_no_negativo_falla(self):
        s = StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_disponible=5)
        s.cantidad_disponible = -1
        with pytest.raises(DomainError):
            StockService.validar_no_negativo(s)

    def test_verificar_disponibilidad_suficiente(self, stock_filtro):
        assert StockService.verificar_disponibilidad(stock_filtro, 10) is True

    def test_verificar_disponibilidad_insuficiente(self, stock_filtro):
        assert StockService.verificar_disponibilidad(stock_filtro, 100) is False

    def test_verificar_disponibilidad_exacto(self, stock_filtro):
        assert StockService.verificar_disponibilidad(stock_filtro, 20) is True

    def test_detectar_agotado(self, stock_filtro, stock_agotado):
        # stock_filtro tenía disponible, stock_agotado no tiene
        eventos = StockService.detectar_eventos_necesarios(stock_filtro, stock_agotado)
        assert "stock.agotado" in eventos

    def test_detectar_disponible_tras_reposicion(self, stock_agotado, stock_filtro):
        eventos = StockService.detectar_eventos_necesarios(stock_agotado, stock_filtro)
        assert "stock.disponible" in eventos

    def test_detectar_bajo_umbral(self):
        antes = StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_disponible=10, umbral_minimo=5)
        despues = StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_disponible=4, umbral_minimo=5)
        eventos = StockService.detectar_eventos_necesarios(antes, despues)
        assert "stock.bajo_umbral" in eventos

    def test_no_detecta_bajo_umbral_si_ya_estaba_bajo(self, stock_cadena):
        # stock_cadena: disponible=3, umbral=5 → ya estaba bajo
        antes = StockRepuesto(repuesto_id="rp-2", codigo="REP-002", cantidad_disponible=2, umbral_minimo=5)
        despues = StockRepuesto(repuesto_id="rp-2", codigo="REP-002", cantidad_disponible=1, umbral_minimo=5)
        eventos = StockService.detectar_eventos_necesarios(antes, despues)
        assert "stock.bajo_umbral" not in eventos

    def test_no_detecta_evento_si_sin_cambio(self, stock_filtro):
        copia = StockRepuesto(
            repuesto_id=stock_filtro.repuesto_id,
            codigo=stock_filtro.codigo,
            cantidad_disponible=stock_filtro.cantidad_disponible,
            umbral_minimo=stock_filtro.umbral_minimo,
        )
        eventos = StockService.detectar_eventos_necesarios(stock_filtro, copia)
        assert len(eventos) == 0

    def test_no_detecta_bajo_umbral_si_ambos_agotados(self, stock_agotado):
        otro_agotado = StockRepuesto(repuesto_id="rp-y", codigo="Y", cantidad_disponible=0, umbral_minimo=3)
        eventos = StockService.detectar_eventos_necesarios(stock_agotado, otro_agotado)
        assert "stock.bajo_umbral" not in eventos

    def test_calcular_alerta_margen_precio_anterior_none(self):
        assert StockService.calcular_alerta_margen(None, Decimal("50.00")) is False

    def test_calcular_alerta_margen_precio_anterior_cero(self):
        assert StockService.calcular_alerta_margen(Decimal("0"), Decimal("50.00")) is False

    def test_calcular_alerta_margen_supera_umbral(self):
        resultado = StockService.calcular_alerta_margen(
            Decimal("100.00"), Decimal("115.00")
        )
        assert resultado is True

    def test_calcular_alerta_margen_bajo_umbral(self):
        resultado = StockService.calcular_alerta_margen(
            Decimal("100.00"), Decimal("108.00")
        )
        assert resultado is False

    def test_calcular_alerta_margen_umbral_personalizado(self):
        resultado = StockService.calcular_alerta_margen(
            Decimal("100.00"), Decimal("106.00"), umbral_porcentual=Decimal("0.05")
        )
        assert resultado is True

    def test_validar_descuento_atomico_todos_ok(self, stock_filtro, stock_cadena):
        stocks = [stock_filtro, stock_cadena]
        descuentos = {
            stock_filtro.repuesto_id: 5,
            stock_cadena.repuesto_id: 2,
        }
        StockService.validar_descuento_atomico(stocks, descuentos)

    def test_validar_descuento_atomico_falla_uno(self, stock_filtro, stock_agotado):
        stocks = [stock_filtro, stock_agotado]
        descuentos = {
            stock_filtro.repuesto_id: 5,
            stock_agotado.repuesto_id: 1,
        }
        with pytest.raises(StockInsuficienteError):
            StockService.validar_descuento_atomico(stocks, descuentos)

    def test_validar_descuento_atomico_sin_descuento(self, stock_filtro):
        StockService.validar_descuento_atomico([stock_filtro], {stock_filtro.repuesto_id: 0})

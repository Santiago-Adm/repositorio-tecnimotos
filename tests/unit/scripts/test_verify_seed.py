"""
Tests unitarios de scripts/verify_seed.py.
Usa InMemorySeedQuery — sin BD real.
"""
import logging

import pytest

from scripts.verify_seed import (
    CONTEOS_MINIMOS,
    ESTADOS_ORDEN_TRABAJO,
    ESTADOS_PEDIDO,
    ESTADOS_REPUESTO,
    SEGMENTOS_CLIENTE,
    InMemorySeedQuery,
    ResultadoVerificacion,
    verificar_seed,
)


def _query_nivel1_completo() -> InMemorySeedQuery:
    """Seed nivel 1 que cumple todos los requisitos."""
    return InMemorySeedQuery({
        "count_repuesto": 5,
        "count_pedido": 3,
        "count_cliente": 2,
        "count_orden_trabajo": 2,
        "count_reabastecimiento": 1,
    })


def _query_nivel2_completo() -> InMemorySeedQuery:
    """Seed nivel 2 que cumple todos los requisitos — conteos y contenido."""
    return InMemorySeedQuery({
        "count_repuesto": 25,
        "count_pedido": 15,
        "count_cliente": 10,
        "count_orden_trabajo": 8,
        "count_reabastecimiento": 5,
        "values_repuesto_estado_disponibilidad": ESTADOS_REPUESTO,
        "values_orden_trabajo_estado": ESTADOS_ORDEN_TRABAJO,
        "values_cliente_segmento": SEGMENTOS_CLIENTE,
        "values_pedido_estado": ESTADOS_PEDIDO,
    })


def _query_nivel2_incompleto() -> InMemorySeedQuery:
    """Seed nivel 2 con conteos OK pero sin todos los estados."""
    return InMemorySeedQuery({
        "count_repuesto": 25,
        "count_pedido": 15,
        "count_cliente": 10,
        "count_orden_trabajo": 8,
        "count_reabastecimiento": 5,
        "values_repuesto_estado_disponibilidad": ["disponible"],
        "values_orden_trabajo_estado": ["ABIERTA", "CERRADA"],
        "values_cliente_segmento": ["S1"],
        "values_pedido_estado": ["BORRADOR", "CONFIRMADO"],
    })


# ── Nivel 1 ───────────────────────────────────────────────────────────────────

class TestNivel1:
    def test_todos_pasan_con_conteos_minimos(self):
        query = _query_nivel1_completo()
        resultados = verificar_seed(1, query)
        assert all(r.pasa for r in resultados), [r for r in resultados if not r.pasa]

    def test_falla_si_repuesto_insuficiente(self):
        query = InMemorySeedQuery({
            "count_repuesto": 4,
            "count_pedido": 3,
            "count_cliente": 2,
            "count_orden_trabajo": 2,
            "count_reabastecimiento": 1,
        })
        resultados = verificar_seed(1, query)
        fallo = next(r for r in resultados if r.tabla == "repuesto")
        assert not fallo.pasa

    def test_falla_si_pedido_cero(self):
        query = InMemorySeedQuery({
            "count_repuesto": 5,
            "count_pedido": 0,
            "count_cliente": 2,
            "count_orden_trabajo": 2,
            "count_reabastecimiento": 1,
        })
        resultados = verificar_seed(1, query)
        fallo = next(r for r in resultados if r.tabla == "pedido")
        assert not fallo.pasa

    def test_nivel1_no_verifica_contenido(self):
        """Nivel 1 solo verifica conteos — sin reglas de contenido de §5.2."""
        query = _query_nivel1_completo()
        resultados = verificar_seed(1, query)
        criterios = [r.criterio for r in resultados]
        assert all(c == "conteo_minimo" for c in criterios)

    def test_conteos_exactos_nivel1(self):
        conteos = CONTEOS_MINIMOS[1]
        assert conteos["repuesto"] == 5
        assert conteos["pedido"] == 3
        assert conteos["cliente"] == 2
        assert conteos["orden_trabajo"] == 2
        assert conteos["reabastecimiento"] == 1

    def test_exactamente_en_el_limite_pasa(self):
        """Exactamente el mínimo debe pasar (≥, no >)."""
        query = _query_nivel1_completo()
        resultados = verificar_seed(1, query)
        repuesto = next(r for r in resultados if r.tabla == "repuesto")
        assert repuesto.pasa
        assert repuesto.obtenido == 5


# ── Nivel 2 ───────────────────────────────────────────────────────────────────

class TestNivel2:
    def test_todos_pasan_con_seed_completo(self):
        query = _query_nivel2_completo()
        resultados = verificar_seed(2, query)
        fallos = [r for r in resultados if not r.pasa]
        assert not fallos, fallos

    def test_verifica_conteos_nivel2(self):
        query = _query_nivel2_completo()
        resultados = verificar_seed(2, query)
        conteos = [r for r in resultados if r.criterio == "conteo_minimo"]
        assert len(conteos) == 5
        assert all(r.pasa for r in conteos)

    def test_verifica_estados_repuesto(self):
        query = _query_nivel2_completo()
        resultados = verificar_seed(2, query)
        estados_rep = [r for r in resultados if r.tabla == "repuesto" and "estado_disponibilidad" in r.criterio]
        assert len(estados_rep) == len(ESTADOS_REPUESTO)
        assert all(r.pasa for r in estados_rep)

    def test_falla_si_falta_estado_repuesto(self):
        query = _query_nivel2_incompleto()
        resultados = verificar_seed(2, query)
        estados_faltantes = [
            r for r in resultados
            if r.tabla == "repuesto" and "estado_disponibilidad" in r.criterio and not r.pasa
        ]
        assert len(estados_faltantes) == 2  # no_disponible y bajo_pedido faltan

    def test_verifica_los_6_estados_ot(self):
        query = _query_nivel2_completo()
        resultados = verificar_seed(2, query)
        estados_ot = [r for r in resultados if r.tabla == "orden_trabajo" and r.criterio != "conteo_minimo"]
        assert len(estados_ot) == len(ESTADOS_ORDEN_TRABAJO)
        assert all(r.pasa for r in estados_ot)

    def test_verifica_los_3_segmentos_cliente(self):
        query = _query_nivel2_completo()
        resultados = verificar_seed(2, query)
        segmentos = [r for r in resultados if r.tabla == "cliente" and r.criterio != "conteo_minimo"]
        assert len(segmentos) == len(SEGMENTOS_CLIENTE)
        assert all(r.pasa for r in segmentos)

    def test_verifica_los_7_estados_pedido(self):
        query = _query_nivel2_completo()
        resultados = verificar_seed(2, query)
        estados_ped = [r for r in resultados if r.tabla == "pedido" and r.criterio != "conteo_minimo"]
        assert len(estados_ped) == len(ESTADOS_PEDIDO)
        assert all(r.pasa for r in estados_ped)

    def test_conteos_exactos_nivel2(self):
        conteos = CONTEOS_MINIMOS[2]
        assert conteos["repuesto"] == 25
        assert conteos["pedido"] == 15
        assert conteos["cliente"] == 10
        assert conteos["orden_trabajo"] == 8
        assert conteos["reabastecimiento"] == 5

    def test_falla_si_conteo_insuficiente(self):
        datos = {k: v for k, v in _query_nivel2_completo()._datos.items()}
        datos["count_repuesto"] = 24
        query = InMemorySeedQuery(datos)
        resultados = verificar_seed(2, query)
        conteo_rep = next(r for r in resultados if r.tabla == "repuesto" and r.criterio == "conteo_minimo")
        assert not conteo_rep.pasa

    def test_falla_si_falta_segmento_s4(self):
        datos = {k: v for k, v in _query_nivel2_completo()._datos.items()}
        datos["values_cliente_segmento"] = ["S1", "S2"]
        query = InMemorySeedQuery(datos)
        resultados = verificar_seed(2, query)
        s4 = next(r for r in resultados if r.tabla == "cliente" and "S4" in r.criterio)
        assert not s4.pasa


# ── Nivel 3 ───────────────────────────────────────────────────────────────────

class TestNivel3:
    def test_conteos_exactos_nivel3(self):
        conteos = CONTEOS_MINIMOS[3]
        assert conteos["repuesto"] == 55
        assert conteos["pedido"] == 50
        assert conteos["cliente"] == 30
        assert conteos["orden_trabajo"] == 20
        assert conteos["reabastecimiento"] == 10

    def test_nivel3_tambien_verifica_contenido(self):
        """Nivel 3 incluye todas las reglas de §5.2."""
        datos = {k: v for k, v in _query_nivel2_completo()._datos.items()}
        datos.update({
            "count_repuesto": 55,
            "count_pedido": 50,
            "count_cliente": 30,
            "count_orden_trabajo": 20,
            "count_reabastecimiento": 10,
        })
        query = InMemorySeedQuery(datos)
        resultados = verificar_seed(3, query)
        fallos = [r for r in resultados if not r.pasa]
        assert not fallos, fallos


# ── ResultadoVerificacion ─────────────────────────────────────────────────────

class TestResultadoVerificacion:
    def test_pasa_true(self):
        r = ResultadoVerificacion("repuesto", "conteo_minimo", ">= 5", 10, pasa=True)
        assert r.pasa is True

    def test_pasa_false(self):
        r = ResultadoVerificacion("repuesto", "conteo_minimo", ">= 5", 3, pasa=False)
        assert r.pasa is False

    def test_log_no_lanza(self, caplog):
        r = ResultadoVerificacion("repuesto", "conteo_minimo", ">= 5", 10, pasa=True)
        with caplog.at_level(logging.DEBUG):
            r.log()

    def test_fallo_no_lanza(self, caplog):
        r = ResultadoVerificacion("repuesto", "conteo_minimo", ">= 25", 3, pasa=False)
        with caplog.at_level(logging.DEBUG):
            r.log()

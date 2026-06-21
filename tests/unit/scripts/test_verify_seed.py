"""
Tests unitarios de scripts/verify_seed.py.
Usa InMemorySeedQuery — sin BD real.
verificar_seed() es async — todos los tests que la llaman son async.
"""
import logging

import pytest

from scripts.verify_seed import (
    CONTEOS_MINIMOS,
    ESTADOS_ORDEN_TRABAJO,
    ESTADOS_PEDIDO,
    ESTADOS_REPUESTO,
    InMemorySeedQuery,
    ResultadoVerificacion,
    SEGMENTOS_CLIENTE,
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
        # ESTADOS_REPUESTO ahora son valores de repuesto.activo ("true"/"false")
        "values_repuesto_activo": ESTADOS_REPUESTO,
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
        "values_repuesto_activo": ["true"],      # falta "false"
        "values_orden_trabajo_estado": ["ABIERTA", "CERRADA"],
        "values_cliente_segmento": ["S1"],
        "values_pedido_estado": ["BORRADOR", "CONFIRMADO"],
    })


# ── Nivel 1 ───────────────────────────────────────────────────────────────────

class TestNivel1:
    async def test_todos_pasan_con_conteos_minimos(self):
        query = _query_nivel1_completo()
        resultados = await verificar_seed(1, query)
        assert all(r.pasa for r in resultados), [r for r in resultados if not r.pasa]

    async def test_falla_si_repuesto_insuficiente(self):
        query = InMemorySeedQuery({
            "count_repuesto": 4,
            "count_pedido": 3,
            "count_cliente": 2,
            "count_orden_trabajo": 2,
            "count_reabastecimiento": 1,
        })
        resultados = await verificar_seed(1, query)
        fallo = next(r for r in resultados if r.tabla == "repuesto")
        assert not fallo.pasa

    async def test_falla_si_pedido_cero(self):
        query = InMemorySeedQuery({
            "count_repuesto": 5,
            "count_pedido": 0,
            "count_cliente": 2,
            "count_orden_trabajo": 2,
            "count_reabastecimiento": 1,
        })
        resultados = await verificar_seed(1, query)
        fallo = next(r for r in resultados if r.tabla == "pedido")
        assert not fallo.pasa

    async def test_nivel1_no_verifica_contenido(self):
        """Nivel 1 solo verifica conteos — sin reglas de contenido de §5.2."""
        query = _query_nivel1_completo()
        resultados = await verificar_seed(1, query)
        criterios = [r.criterio for r in resultados]
        assert all(c == "conteo_minimo" for c in criterios)

    def test_conteos_exactos_nivel1(self):
        conteos = CONTEOS_MINIMOS[1]
        assert conteos["repuesto"] == 5
        assert conteos["pedido"] == 3
        assert conteos["cliente"] == 2
        assert conteos["orden_trabajo"] == 2
        assert conteos["reabastecimiento"] == 1

    async def test_exactamente_en_el_limite_pasa(self):
        """Exactamente el mínimo debe pasar (≥, no >)."""
        query = _query_nivel1_completo()
        resultados = await verificar_seed(1, query)
        repuesto = next(r for r in resultados if r.tabla == "repuesto")
        assert repuesto.pasa
        assert repuesto.obtenido == 5


# ── Nivel 2 ───────────────────────────────────────────────────────────────────

class TestNivel2:
    async def test_todos_pasan_con_seed_completo(self):
        query = _query_nivel2_completo()
        resultados = await verificar_seed(2, query)
        fallos = [r for r in resultados if not r.pasa]
        assert not fallos, fallos

    async def test_verifica_conteos_nivel2(self):
        query = _query_nivel2_completo()
        resultados = await verificar_seed(2, query)
        conteos = [r for r in resultados if r.criterio == "conteo_minimo"]
        assert len(conteos) == 5
        assert all(r.pasa for r in conteos)

    async def test_verifica_activo_repuesto(self):
        """§5.2: repuesto debe tener activos y no-activos (activo=true y activo=false)."""
        query = _query_nivel2_completo()
        resultados = await verificar_seed(2, query)
        activos = [r for r in resultados if r.tabla == "repuesto" and "activo=" in r.criterio]
        assert len(activos) == len(ESTADOS_REPUESTO)
        assert all(r.pasa for r in activos)

    async def test_falla_si_falta_activo_false(self):
        """Si no hay repuestos inactivos, debe fallar el criterio activo=false."""
        query = _query_nivel2_incompleto()
        resultados = await verificar_seed(2, query)
        faltan = [
            r for r in resultados
            if r.tabla == "repuesto" and "activo=false" in r.criterio and not r.pasa
        ]
        assert len(faltan) == 1

    async def test_verifica_los_6_estados_ot(self):
        query = _query_nivel2_completo()
        resultados = await verificar_seed(2, query)
        estados_ot = [r for r in resultados if r.tabla == "orden_trabajo" and r.criterio != "conteo_minimo"]
        assert len(estados_ot) == len(ESTADOS_ORDEN_TRABAJO)
        assert all(r.pasa for r in estados_ot)

    async def test_verifica_los_3_segmentos_cliente(self):
        query = _query_nivel2_completo()
        resultados = await verificar_seed(2, query)
        segmentos = [r for r in resultados if r.tabla == "cliente" and r.criterio != "conteo_minimo"]
        assert len(segmentos) == len(SEGMENTOS_CLIENTE)
        assert all(r.pasa for r in segmentos)

    async def test_verifica_los_7_estados_pedido(self):
        query = _query_nivel2_completo()
        resultados = await verificar_seed(2, query)
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

    async def test_falla_si_conteo_insuficiente(self):
        datos = dict(_query_nivel2_completo()._datos)
        datos["count_repuesto"] = 24
        query = InMemorySeedQuery(datos)
        resultados = await verificar_seed(2, query)
        conteo_rep = next(r for r in resultados if r.tabla == "repuesto" and r.criterio == "conteo_minimo")
        assert not conteo_rep.pasa

    async def test_falla_si_falta_segmento_s4(self):
        datos = dict(_query_nivel2_completo()._datos)
        datos["values_cliente_segmento"] = ["S1", "S2"]
        query = InMemorySeedQuery(datos)
        resultados = await verificar_seed(2, query)
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

    async def test_nivel3_tambien_verifica_contenido(self):
        """Nivel 3 incluye todas las reglas de §5.2."""
        datos = dict(_query_nivel2_completo()._datos)
        datos.update({
            "count_repuesto": 55,
            "count_pedido": 50,
            "count_cliente": 30,
            "count_orden_trabajo": 20,
            "count_reabastecimiento": 10,
        })
        query = InMemorySeedQuery(datos)
        resultados = await verificar_seed(3, query)
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

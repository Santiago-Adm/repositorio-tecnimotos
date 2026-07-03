"""Tests unitarios — validación y transformación de filas (sin BD)."""
from __future__ import annotations

from decimal import Decimal

from scripts.migracion.migrar_bajaj import _procesar_fila, _R_A_UNIVERSO


class TestMapeoUniverso:
    def test_2r_mapea_motolineal(self):
        assert _R_A_UNIVERSO["2R"] == "motolineal"

    def test_3r_mapea_mototaxi_3r(self):
        assert _R_A_UNIVERSO["3R"] == "mototaxi_3r"

    def test_4r_mapea_mototaxi_4r(self):
        assert _R_A_UNIVERSO["4R"] == "mototaxi_4r"


class TestProcesarFilaValida:
    def test_fila_valida_2r(self):
        valida, rechazo = _procesar_fila(2, "39050302", "TORNILLO", "2R", "SUNNY ZIP", 0.1)
        assert rechazo is None
        assert valida.codigo == "39050302"
        assert valida.nombre == "TORNILLO"
        assert valida.modelo == "SUNNY ZIP"
        assert valida.universo == "motolineal"
        assert valida.precio_venta == Decimal("0.1")

    def test_precio_costo_es_precio_venta_sobre_1_16(self):
        valida, _ = _procesar_fila(2, "COD-001", "DESC", "3R", "MODELO", 100)
        assert valida.precio_costo == Decimal("86.21")  # 100/1.16 = 86.2068... -> 86.21

    def test_codigo_numerico_se_castea_a_string(self):
        valida, rechazo = _procesar_fila(2, 39050302, "TORNILLO", "4R", "MODELO", 5)
        assert rechazo is None
        assert valida.codigo == "39050302"


class TestProcesarFilaRechazada:
    def test_codigo_vacio_se_rechaza(self):
        valida, rechazo = _procesar_fila(2, None, "DESC", "2R", "MODELO", 10)
        assert valida is None
        assert "código vacío" in rechazo.motivo

    def test_codigo_solo_espacios_se_rechaza(self):
        valida, rechazo = _procesar_fila(2, "   ", "DESC", "2R", "MODELO", 10)
        assert valida is None
        assert "código vacío" in rechazo.motivo

    def test_pvp_none_se_rechaza(self):
        valida, rechazo = _procesar_fila(2, "COD-001", "DESC", "2R", "MODELO", None)
        assert valida is None
        assert "PVP" in rechazo.motivo

    def test_pvp_no_numerico_se_rechaza(self):
        valida, rechazo = _procesar_fila(2, "COD-001", "DESC", "2R", "MODELO", "S/. 10.00")
        assert valida is None
        assert "PVP" in rechazo.motivo

    def test_pvp_cero_se_rechaza(self):
        valida, rechazo = _procesar_fila(2, "COD-001", "DESC", "2R", "MODELO", 0)
        assert valida is None
        assert "PVP" in rechazo.motivo

    def test_pvp_negativo_se_rechaza(self):
        valida, rechazo = _procesar_fila(2, "COD-001", "DESC", "2R", "MODELO", -5)
        assert valida is None
        assert "PVP" in rechazo.motivo

    def test_r_invalido_se_rechaza(self):
        valida, rechazo = _procesar_fila(2, "COD-001", "DESC", "5R", "MODELO", 10)
        assert valida is None
        assert "R inválido" in rechazo.motivo

    def test_r_none_se_rechaza(self):
        valida, rechazo = _procesar_fila(2, "COD-001", "DESC", None, "MODELO", 10)
        assert valida is None
        assert "R inválido" in rechazo.motivo

    def test_fila_completamente_vacia_se_rechaza_por_codigo(self):
        valida, rechazo = _procesar_fila(17196, None, None, None, None, None)
        assert valida is None
        assert "código vacío" in rechazo.motivo

"""Tests unitarios — RepuestoService (reglas de negocio puras)."""
import pytest

from src.catalogo.domain.models.repuesto import (
    DomainError,
    RepuestoDadoDeBajaError,
    UniversoRepuesto,
)
from src.catalogo.domain.services.repuesto_service import RepuestoService


class TestValidarSeparacionUniverso:
    def test_universo_correcto_no_lanza(self, repuesto_mototaxi):
        RepuestoService.validar_separacion_universo(
            repuesto_mototaxi, UniversoRepuesto.MOTOTAXI
        )

    def test_universo_incorrecto_lanza_error(self, repuesto_mototaxi):
        with pytest.raises(DomainError):
            RepuestoService.validar_separacion_universo(
                repuesto_mototaxi, UniversoRepuesto.MOTOLINEAL
            )


class TestValidarActivo:
    def test_repuesto_activo_no_lanza(self, repuesto_mototaxi):
        RepuestoService.validar_activo(repuesto_mototaxi)

    def test_repuesto_inactivo_lanza_error(self, repuesto_mototaxi):
        repuesto_mototaxi.dar_de_baja("test")
        with pytest.raises(RepuestoDadoDeBajaError):
            RepuestoService.validar_activo(repuesto_mototaxi)


class TestCalcularVisibilidadPrecio:
    def test_nivel_0_visitante_no_visible(self):
        visible, msg = RepuestoService.calcular_visibilidad_precio(
            consultas_realizadas=0,
            max_consultas=3,
            es_cliente=False,
            nivel_visibilidad=0,
        )
        assert visible is False
        assert msg is None

    def test_nivel_1_cliente_con_consultas_disponibles(self):
        visible, msg = RepuestoService.calcular_visibilidad_precio(
            consultas_realizadas=1,
            max_consultas=3,
            es_cliente=True,
            nivel_visibilidad=1,
        )
        assert visible is True
        assert msg is None

    def test_nivel_1_cliente_limite_alcanzado(self):
        visible, msg = RepuestoService.calcular_visibilidad_precio(
            consultas_realizadas=3,
            max_consultas=3,
            es_cliente=True,
            nivel_visibilidad=1,
        )
        assert visible is False
        assert "visítanos" in msg

    def test_nivel_2_siempre_visible(self):
        visible, msg = RepuestoService.calcular_visibilidad_precio(
            consultas_realizadas=10,
            max_consultas=3,
            es_cliente=True,
            nivel_visibilidad=2,
        )
        assert visible is True
        assert msg is None

    def test_nivel_0_no_cliente_no_visible(self):
        """Visitante sin cuenta — precio nunca visible (02 §4.2 Nivel 0)."""
        visible, _ = RepuestoService.calcular_visibilidad_precio(
            consultas_realizadas=0,
            max_consultas=3,
            es_cliente=False,
            nivel_visibilidad=0,
        )
        assert visible is False

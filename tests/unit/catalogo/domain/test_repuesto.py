"""
Tests unitarios — entidad Repuesto (dominio puro).
Cubre: creación, invariantes, actualizar_precio, dar_de_baja, advertencia.
"""
import pytest
from decimal import Decimal

from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    DomainError,
    HistorialPrecio,
    PrecioInvalidoError,
    Repuesto,
    RepuestoDadoDeBajaError,
    UniversoRepuesto,
)


class TestRepuestoCreacion:
    def test_crea_repuesto_valido(self):
        r = Repuesto(
            codigo="REP-001",
            nombre="Filtro",
            universo=UniversoRepuesto.MOTOTAXI,
            modelo="Bajaj RE",
            año=2019,
            categoria=CategoriaRepuesto.MOTOR,
            precio_venta=Decimal("45.00"),
        )
        assert r.codigo == "REP-001"
        assert r.activo is True
        assert r.eliminado_en is None

    def test_precio_cero_lanza_error(self):
        with pytest.raises(PrecioInvalidoError):
            Repuesto(
                codigo="REP-X",
                nombre="X",
                universo=UniversoRepuesto.MOTOTAXI,
                modelo="Bajaj RE",
                año=2019,
                categoria=CategoriaRepuesto.MOTOR,
                precio_venta=Decimal("0"),
            )

    def test_precio_negativo_lanza_error(self):
        with pytest.raises(PrecioInvalidoError):
            Repuesto(
                codigo="REP-X",
                nombre="X",
                universo=UniversoRepuesto.MOTOTAXI,
                modelo="Bajaj RE",
                año=2019,
                categoria=CategoriaRepuesto.MOTOR,
                precio_venta=Decimal("-10"),
            )

    def test_año_fuera_de_rango_lanza_error(self):
        with pytest.raises(DomainError):
            Repuesto(
                codigo="REP-X",
                nombre="X",
                universo=UniversoRepuesto.MOTOTAXI,
                modelo="Bajaj RE",
                año=1980,
                categoria=CategoriaRepuesto.MOTOR,
                precio_venta=Decimal("10"),
            )

    def test_año_limite_superior_lanza_error(self):
        with pytest.raises(DomainError):
            Repuesto(
                codigo="REP-X",
                nombre="X",
                universo=UniversoRepuesto.MOTOTAXI,
                modelo="Bajaj RE",
                año=2101,
                categoria=CategoriaRepuesto.MOTOR,
                precio_venta=Decimal("10"),
            )


class TestActualizarPrecio:
    def test_actualiza_precio_registra_historial(self, repuesto_mototaxi):
        r = repuesto_mototaxi
        entrada = r.actualizar_precio(Decimal("52.00"), "admin-001")
        assert r.precio_venta == Decimal("52.00")
        assert isinstance(entrada, HistorialPrecio)
        assert entrada.precio_anterior == Decimal("45.00")
        assert entrada.precio_nuevo == Decimal("52.00")
        assert len(r.historial_precio) == 1

    def test_actualizar_precio_cero_lanza_error(self, repuesto_mototaxi):
        with pytest.raises(PrecioInvalidoError):
            repuesto_mototaxi.actualizar_precio(Decimal("0"), "admin-001")

    def test_multiples_actualizaciones_acumulan_historial(self, repuesto_mototaxi):
        repuesto_mototaxi.actualizar_precio(Decimal("52.00"), "admin-001")
        repuesto_mototaxi.actualizar_precio(Decimal("58.00"), "admin-001")
        assert len(repuesto_mototaxi.historial_precio) == 2
        assert repuesto_mototaxi.precio_venta == Decimal("58.00")


class TestDarDeBaja:
    def test_dar_de_baja_desactiva_repuesto(self, repuesto_mototaxi):
        repuesto_mototaxi.dar_de_baja("Descontinuado")
        assert repuesto_mototaxi.activo is False
        assert repuesto_mototaxi.eliminado_en is not None

    def test_dar_de_baja_no_elimina_fisicamente(self, repuesto_mototaxi):
        repuesto_mototaxi.dar_de_baja("Motivo")
        assert repuesto_mototaxi.codigo == "REP-001"
        assert repuesto_mototaxi.nombre is not None


class TestAdvertenciaInstalacion:
    def test_tecnico_especializado_requiere_advertencia(
        self, repuesto_tecnico_especializado
    ):
        assert repuesto_tecnico_especializado.es_tecnico_especializado() is True
        assert repuesto_tecnico_especializado.requiere_advertencia_instalacion() is True

    def test_categoria_normal_sin_advertencia(self, repuesto_mototaxi):
        assert repuesto_mototaxi.es_tecnico_especializado() is False
        assert repuesto_mototaxi.requiere_advertencia_instalacion() is False


class TestUniversos:
    def test_universo_mototaxi(self, repuesto_mototaxi):
        assert repuesto_mototaxi.universo == UniversoRepuesto.MOTOTAXI

    def test_universo_motolineal(self, repuesto_motolineal):
        assert repuesto_motolineal.universo == UniversoRepuesto.MOTOLINEAL

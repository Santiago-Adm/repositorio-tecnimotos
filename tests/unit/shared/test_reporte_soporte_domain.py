"""
Tests unitarios para ReporteSoporte y EstadoReporteSoporte (02 §1.3).
Cobertura branch ≥ 95% — umbral declarado como decisión de sesión por tratarse
de entidad que toca auditoría y seguridad (09 §4.1, umbral piso stock 95%).
"""
from __future__ import annotations

import pytest

from src.shared.domain.models.reporte_soporte import (
    EstadoReporteSoporte,
    ReporteSoporte,
    ReporteSoporteNoEncontradoError,
    TransicionEstadoReporteSoporteInvalidaError,
)


# ══════════════════════════════════════════════════════════════════════
# Creación y estado inicial
# ══════════════════════════════════════════════════════════════════════

def test_reporte_se_crea_en_estado_abierto():
    r = ReporteSoporte(
        usuario_reportante_id="u-001",
        rol_usuario_reportante="CLIENTE_RURAL",
        descripcion="No pude confirmar mi reserva, salió error",
    )
    assert r.estado == EstadoReporteSoporte.ABIERTO
    assert r.resuelto_en is None
    assert r.resuelto_por is None
    assert r.id  # UUID asignado


def test_reporte_preserva_datos_del_reportante():
    r = ReporteSoporte(
        usuario_reportante_id="u-cli-005",
        rol_usuario_reportante="CLIENTE_CONDUCTOR",
        descripcion="Error al ver mi historial",
    )
    assert r.usuario_reportante_id == "u-cli-005"
    assert r.rol_usuario_reportante == "CLIENTE_CONDUCTOR"
    assert r.descripcion == "Error al ver mi historial"
    assert r.creado_en is not None


# ══════════════════════════════════════════════════════════════════════
# Transición ABIERTO → EN_INVESTIGACION (02 §1.3, Escenario 2)
# ══════════════════════════════════════════════════════════════════════

def test_activar_investigacion_desde_abierto():
    r = ReporteSoporte(usuario_reportante_id="u-001", rol_usuario_reportante="CLIENTE_RURAL", descripcion="x")
    r.activar_investigacion()
    assert r.estado == EstadoReporteSoporte.EN_INVESTIGACION


def test_activar_investigacion_desde_en_investigacion_lanza_error():
    r = ReporteSoporte(usuario_reportante_id="u-001", rol_usuario_reportante="CLIENTE_RURAL", descripcion="x")
    r.activar_investigacion()
    with pytest.raises(TransicionEstadoReporteSoporteInvalidaError):
        r.activar_investigacion()


def test_activar_investigacion_desde_resuelto_lanza_error():
    r = ReporteSoporte(usuario_reportante_id="u-001", rol_usuario_reportante="CLIENTE_RURAL", descripcion="x")
    r.activar_investigacion()
    r.resolver("admin-001")
    with pytest.raises(TransicionEstadoReporteSoporteInvalidaError):
        r.activar_investigacion()


# ══════════════════════════════════════════════════════════════════════
# Transición EN_INVESTIGACION → RESUELTO
# ══════════════════════════════════════════════════════════════════════

def test_resolver_desde_en_investigacion():
    r = ReporteSoporte(usuario_reportante_id="u-001", rol_usuario_reportante="CLIENTE_RURAL", descripcion="x")
    r.activar_investigacion()
    r.resolver("superadmin-001")
    assert r.estado == EstadoReporteSoporte.RESUELTO
    assert r.resuelto_por == "superadmin-001"
    assert r.resuelto_en is not None


def test_resolver_desde_abierto_lanza_error():
    r = ReporteSoporte(usuario_reportante_id="u-001", rol_usuario_reportante="CLIENTE_RURAL", descripcion="x")
    with pytest.raises(TransicionEstadoReporteSoporteInvalidaError):
        r.resolver("superadmin-001")


# ══════════════════════════════════════════════════════════════════════
# Transición → CERRADO_SIN_RESOLUCION
# ══════════════════════════════════════════════════════════════════════

def test_cerrar_sin_resolucion_desde_abierto():
    r = ReporteSoporte(usuario_reportante_id="u-001", rol_usuario_reportante="CLIENTE_RURAL", descripcion="x")
    r.cerrar_sin_resolucion()
    assert r.estado == EstadoReporteSoporte.CERRADO_SIN_RESOLUCION


def test_cerrar_sin_resolucion_desde_en_investigacion():
    r = ReporteSoporte(usuario_reportante_id="u-001", rol_usuario_reportante="CLIENTE_RURAL", descripcion="x")
    r.activar_investigacion()
    r.cerrar_sin_resolucion()
    assert r.estado == EstadoReporteSoporte.CERRADO_SIN_RESOLUCION


def test_cerrar_sin_resolucion_desde_resuelto_lanza_error():
    r = ReporteSoporte(usuario_reportante_id="u-001", rol_usuario_reportante="CLIENTE_RURAL", descripcion="x")
    r.activar_investigacion()
    r.resolver("superadmin-001")
    with pytest.raises(TransicionEstadoReporteSoporteInvalidaError):
        r.cerrar_sin_resolucion()


def test_cerrar_sin_resolucion_ya_cerrado_lanza_error():
    r = ReporteSoporte(usuario_reportante_id="u-001", rol_usuario_reportante="CLIENTE_RURAL", descripcion="x")
    r.cerrar_sin_resolucion()
    with pytest.raises(TransicionEstadoReporteSoporteInvalidaError):
        r.cerrar_sin_resolucion()


# ══════════════════════════════════════════════════════════════════════
# Errores de dominio importables (Escenario 2 — sin ID válido)
# ══════════════════════════════════════════════════════════════════════

def test_reporte_soporte_no_encontrado_error_es_importable():
    exc = ReporteSoporteNoEncontradoError("reporte-inexistente")
    assert "reporte-inexistente" in str(exc)

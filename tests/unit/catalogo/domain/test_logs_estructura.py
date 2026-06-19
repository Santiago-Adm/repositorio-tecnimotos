"""
Test de logging estructurado JSON (09 §4.1 criterio transversal).
Verifica que todos los eventos del módulo catalogo emiten JSON con los 5 campos obligatorios.
"""
import json
import logging
from io import StringIO

import pytest

from src.shared.infrastructure.logging import JSONFormatter, configure_logging, request_id_var


class TestJSONFormatter:
    def test_cinco_campos_obligatorios_presentes(self):
        formatter = JSONFormatter(
            service="catalogo",
            version="0.1.0",
            environment="test",
            strict=True,
        )
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="mensaje de prueba",
            args=(),
            exc_info=None,
        )
        output = json.loads(formatter.format(record))

        assert "timestamp" in output
        assert "level" in output
        assert "service" in output
        assert "version" in output
        assert "environment" in output

    def test_campo_service_correcto(self):
        formatter = JSONFormatter(
            service="catalogo",
            version="0.1.0",
            environment="test",
        )
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="",
            lineno=0, msg="msg", args=(), exc_info=None,
        )
        output = json.loads(formatter.format(record))
        assert output["service"] == "catalogo"

    def test_request_id_incluido(self):
        formatter = JSONFormatter(
            service="catalogo",
            version="0.1.0",
            environment="test",
        )
        token = request_id_var.set("test-request-123")
        try:
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="",
                lineno=0, msg="msg", args=(), exc_info=None,
            )
            output = json.loads(formatter.format(record))
            assert output["request_id"] == "test-request-123"
        finally:
            request_id_var.reset(token)

    def test_campos_extra_incluidos(self):
        formatter = JSONFormatter(
            service="catalogo",
            version="0.1.0",
            environment="test",
        )
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="",
            lineno=0, msg="msg", args=(), exc_info=None,
        )
        record.repuesto_id = "REP-001"
        record.codigo = "REP-001"
        output = json.loads(formatter.format(record))
        assert output.get("repuesto_id") == "REP-001"

    def test_formato_es_json_valido(self):
        formatter = JSONFormatter(
            service="catalogo",
            version="0.1.0",
            environment="test",
        )
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="",
            lineno=0, msg="mensaje", args=(), exc_info=None,
        )
        output_str = formatter.format(record)
        # Debe ser JSON válido — no lanza excepción
        parsed = json.loads(output_str)
        assert isinstance(parsed, dict)

    def test_nivel_correcto(self):
        formatter = JSONFormatter(
            service="catalogo",
            version="0.1.0",
            environment="test",
        )
        for level_name, level in [("INFO", logging.INFO), ("ERROR", logging.ERROR)]:
            record = logging.LogRecord(
                name="test", level=level, pathname="",
                lineno=0, msg="msg", args=(), exc_info=None,
            )
            output = json.loads(formatter.format(record))
            assert output["level"] == level_name

"""
Test de seguridad — settings.py NO debe tener defaults embebidos para
credenciales de base de datos (incidente 2026-07-04, remediación del
Blocker de SonarQube). La app debe fallar al arrancar (fail-fast) si
DATABASE_URL/DATABASE_URL_SYNC no están configuradas, en vez de degradar
silenciosamente a una credencial de desarrollo conocida y pública.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


def test_settings_falla_sin_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
    from src.shared.infrastructure.settings import Settings

    # _env_file=None fuerza a ignorar el .env real del entorno de desarrollo —
    # simula un clon nuevo del repo sin .env configurado todavía.
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    errores = {e["loc"][0] for e in exc_info.value.errors()}
    assert "database_url" in errores
    assert "database_url_sync" in errores


def test_settings_no_tiene_default_hardcodeado():
    """Verifica que el campo no declara un valor por defecto en el código
    fuente — regresión directa del incidente de seguridad."""
    from src.shared.infrastructure.settings import Settings

    campo = Settings.model_fields["database_url"]
    assert campo.is_required(), "database_url no debe tener un default embebido"

    campo_sync = Settings.model_fields["database_url_sync"]
    assert campo_sync.is_required(), "database_url_sync no debe tener un default embebido"

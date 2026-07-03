"""Tests unitarios — src/shared/infrastructure/mfa_auditoria.py (R29)."""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock

import pytest

from src.shared.infrastructure.mfa_auditoria import registrar_intento_mfa


async def test_sin_db_no_lanza_y_registra_log(caplog):
    with caplog.at_level(logging.INFO):
        await registrar_intento_mfa(None, "usuario-1", "EXITOSO", "127.0.0.1")
    assert "sin BD" in caplog.text


async def test_con_db_ejecuta_insert():
    db = AsyncMock()
    await registrar_intento_mfa(db, "usuario-2", "CODIGO_INCORRECTO", "10.0.0.5")
    db.execute.assert_awaited_once()
    args, kwargs = db.execute.call_args
    params = args[1]
    assert params["usuario_id"] == "usuario-2"
    assert params["resultado"] == "CODIGO_INCORRECTO"
    assert params["ip"] == "10.0.0.5"


async def test_fallo_de_insert_no_propaga_excepcion():
    db = AsyncMock()
    db.execute.side_effect = RuntimeError("BD caída")
    # No debe lanzar — la auditoría nunca bloquea el login
    await registrar_intento_mfa(db, "usuario-3", "EXITOSO", None)

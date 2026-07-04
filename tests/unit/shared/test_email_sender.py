"""Tests unitarios — src/shared/infrastructure/email_sender.py (ADR-011 MFA)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.infrastructure.email_sender import EmailSendError, enviar_correo


@pytest.fixture(autouse=True)
def _limpiar_cache_settings():
    from src.shared.infrastructure.settings import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_sin_api_key_no_envia_ni_lanza(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    with patch("httpx.AsyncClient.post", new=AsyncMock()) as mock_post:
        await enviar_correo("test@example.com", "Asunto", "Cuerpo con código 123456")
    mock_post.assert_not_called()


async def test_con_api_key_envia_correctamente(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    fake_response = MagicMock(status_code=200, text="")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake_response)) as mock_post:
        await enviar_correo("admin@tecnimotos.test", "Tu código", "Tu código es 654321")
    mock_post.assert_awaited_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["to"] == ["admin@tecnimotos.test"]
    assert kwargs["json"]["subject"] == "Tu código"
    assert "654321" in kwargs["json"]["text"]
    assert "Bearer re_test_key" in kwargs["headers"]["Authorization"]


async def test_error_http_lanza_email_send_error(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    fake_response = MagicMock(status_code=422, text="dominio no verificado")
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake_response)):
        with pytest.raises(EmailSendError):
            await enviar_correo("admin@tecnimotos.test", "Tu código", "Tu código es 111111")


async def test_produccion_nunca_loguea_el_codigo_aunque_falte_api_key(monkeypatch, caplog):
    """Fail-safe: ENVIRONMENT != 'development' nunca expone el código, ni
    siquiera si alguien desconfigura RESEND_API_KEY por error (PIEZA D)."""
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    codigo_secreto = "999999"
    with patch("httpx.AsyncClient.post", new=AsyncMock()):
        await enviar_correo("admin@tecnimotos.test", "Tu código", f"Tu código es {codigo_secreto}")
    assert codigo_secreto not in caplog.text


async def test_desarrollo_sin_api_key_loguea_codigo_marcado(monkeypatch, caplog):
    """PIEZA D (sesión 2026-07-03): en development, sin RESEND_API_KEY, el
    código real aparece en el log — marcado explícitamente como solo-desarrollo."""
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    codigo_secreto = "888888"
    with patch("httpx.AsyncClient.post", new=AsyncMock()):
        await enviar_correo("admin@tecnimotos.test", "Tu código", f"Tu código es {codigo_secreto}")
    assert codigo_secreto in caplog.text
    assert "SOLO DESARROLLO" in caplog.text
    assert "NUNCA EN PRODUCCIÓN" in caplog.text

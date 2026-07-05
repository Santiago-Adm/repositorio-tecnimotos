"""Tests unitarios — src/shared/infrastructure/email_sender.py (ADR-011 MFA)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.infrastructure.email_sender import EmailSendError, enviar_correo


@pytest.fixture(autouse=True)
def _limpiar_cache_settings():
    from src.shared.infrastructure.settings import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _fake_settings(*, resend_api_key: str = "", environment: str = "development"):
    """monkeypatch.delenv solo limpia os.environ — Settings también lee del
    archivo .env en disco (pydantic-settings), que en este repo SÍ tiene una
    RESEND_API_KEY real configurada (Pieza 6-bis). Sin este fake, estos tests
    dejan de aislar el escenario "sin API key" en cuanto .env tiene una key
    real, sin que el código de producción tenga ningún problema."""
    return SimpleNamespace(
        resend_api_key=resend_api_key,
        environment=environment,
        mfa_email_from="Tecnimotos <onboarding@resend.dev>",
    )


async def test_sin_api_key_no_envia_ni_lanza(monkeypatch):
    monkeypatch.setattr(
        "src.shared.infrastructure.email_sender.get_settings",
        lambda: _fake_settings(resend_api_key=""),
    )
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
    monkeypatch.setattr(
        "src.shared.infrastructure.email_sender.get_settings",
        lambda: _fake_settings(resend_api_key="", environment="production"),
    )
    codigo_secreto = "999999"
    with patch("httpx.AsyncClient.post", new=AsyncMock()):
        await enviar_correo("admin@tecnimotos.test", "Tu código", f"Tu código es {codigo_secreto}")
    assert codigo_secreto not in caplog.text


async def test_desarrollo_sin_api_key_loguea_codigo_marcado(monkeypatch, caplog):
    """PIEZA D (sesión 2026-07-03): en development, sin RESEND_API_KEY, el
    código real aparece en el log — marcado explícitamente como solo-desarrollo."""
    monkeypatch.setattr(
        "src.shared.infrastructure.email_sender.get_settings",
        lambda: _fake_settings(resend_api_key="", environment="development"),
    )
    codigo_secreto = "888888"
    with patch("httpx.AsyncClient.post", new=AsyncMock()):
        await enviar_correo("admin@tecnimotos.test", "Tu código", f"Tu código es {codigo_secreto}")
    assert codigo_secreto in caplog.text
    assert "SOLO DESARROLLO" in caplog.text
    assert "NUNCA EN PRODUCCIÓN" in caplog.text

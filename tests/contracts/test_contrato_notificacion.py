"""
Suite de contrato LSP: NotificacionPort (04 §6.2).
Valida que InMemoryNotificacionAdapter, WhatsAppAdapter y SMSAdapter
siguen el mismo contrato de comportamiento.
Protocol: NotificacionPort (03 §9.1).
"""
import pytest

from src.shared.domain.notificacion_port import (
    ComandoNotificacion,
    ResultadoNotificacion,
)
from src.shared.infrastructure.notificacion_adapters import (
    InMemoryNotificacionAdapter,
    SMSAdapter,
    WhatsAppAdapter,
)


def _comando_fixture() -> ComandoNotificacion:
    return ComandoNotificacion(
        destinatario_id="cli-contrato-001",
        canal="whatsapp",
        tipo="stock.bajo_umbral",
        payload={"repuesto_id": "rp-001", "cantidad_actual": 2},
    )


@pytest.fixture(params=["inmemory", "whatsapp", "sms"])
async def adapter(request):
    """Fixture parametrizado — misma suite corre sobre las 3 implementaciones."""
    if request.param == "inmemory":
        return InMemoryNotificacionAdapter()
    if request.param == "whatsapp":
        return WhatsAppAdapter(api_token="stub-token")
    return SMSAdapter(api_key="stub-key")


# ── Casos de contrato — deben pasar en TODAS las implementaciones ─────────────

@pytest.mark.asyncio
async def test_enviar_notificacion_retorna_resultado_correcto(adapter):
    resultado = await adapter.enviar_notificacion(_comando_fixture())
    assert isinstance(resultado, ResultadoNotificacion)


@pytest.mark.asyncio
async def test_enviar_notificacion_enviado_true(adapter):
    resultado = await adapter.enviar_notificacion(_comando_fixture())
    assert resultado.enviado is True


@pytest.mark.asyncio
async def test_enviar_notificacion_canal_usado_no_vacio(adapter):
    resultado = await adapter.enviar_notificacion(_comando_fixture())
    assert isinstance(resultado.canal_usado, str)
    assert len(resultado.canal_usado) > 0


@pytest.mark.asyncio
async def test_enviar_notificacion_mensaje_id_str(adapter):
    resultado = await adapter.enviar_notificacion(_comando_fixture())
    assert isinstance(resultado.mensaje_id, str)

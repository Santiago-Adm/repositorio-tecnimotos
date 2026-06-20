"""
Suite de contrato LSP: ParametrosSistemaPort (04 §6.2).
Valida que InMemoryParametrosService y ParametrosServiceImpl
siguen el mismo contrato de comportamiento.
Protocol: ParametrosSistemaPort (03 §8.2, §8.4).
"""
import pytest

from src.shared.domain.parametros_port import (
    ParametroNoEncontradoError,
    ParametroResponse,
)
from src.shared.infrastructure.parametros_adapters import (
    InMemoryParametrosService,
    ParametrosServiceImpl,
)


@pytest.fixture(params=["inmemory", "real"])
async def service(request):
    """Fixture parametrizado — misma suite corre sobre Fake e implementación real."""
    if request.param == "inmemory":
        return InMemoryParametrosService()
    backend = InMemoryParametrosService()
    return ParametrosServiceImpl(backend=backend)


# ── Casos de contrato — deben pasar en AMBAS implementaciones ─────────────────

@pytest.mark.asyncio
async def test_obtener_parametro_existente(service):
    result = await service.obtener_parametro("max_consultas_precio_sesion")
    assert isinstance(result, ParametroResponse)


@pytest.mark.asyncio
async def test_obtener_parametro_retorna_clave_correcta(service):
    result = await service.obtener_parametro("max_consultas_precio_sesion")
    assert result.clave == "max_consultas_precio_sesion"


@pytest.mark.asyncio
async def test_obtener_parametro_valor_no_none(service):
    result = await service.obtener_parametro("max_consultas_precio_sesion")
    assert result.valor is not None


@pytest.mark.asyncio
async def test_obtener_parametro_valor_correcto(service):
    result = await service.obtener_parametro("max_consultas_precio_sesion")
    assert result.valor == 3


@pytest.mark.asyncio
async def test_obtener_parametro_reintentos_notificacion(service):
    result = await service.obtener_parametro("reintentos_notificacion")
    assert result.valor == 3


@pytest.mark.asyncio
async def test_obtener_parametro_inexistente_lanza(service):
    with pytest.raises(ParametroNoEncontradoError):
        await service.obtener_parametro("parametro_que_no_existe_9999")


@pytest.mark.asyncio
async def test_retorno_desde_cache_es_bool(service):
    result = await service.obtener_parametro("ttl_cache_parametros_segundos")
    assert isinstance(result.desde_cache, bool)

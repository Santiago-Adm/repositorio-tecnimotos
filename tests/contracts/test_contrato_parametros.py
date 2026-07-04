"""
Suite de contrato LSP: ParametrosSistemaPort (04 §6.2, ADR-015).
Valida que InMemoryParametrosService y ParametrosRepositoryPG (real, contra
Postgres) siguen el mismo contrato de comportamiento. Antes de ADR-015 esta
suite comparaba InMemoryParametrosService contra ParametrosServiceImpl —
una clase que nunca se instanciaba en producción y que por dentro delegaba
al mismo InMemoryParametrosService, así que no probaba nada distinto.
Protocol: ParametrosSistemaPort (03 §8.2, §8.4).
"""
import pytest

from src.shared.domain.parametros_port import (
    ParametroNoEncontradoError,
    ParametroResponse,
)
from src.shared.infrastructure.parametros_adapters import InMemoryParametrosService
from tests.integration.conftest_pg import pg_session


@pytest.fixture(params=["inmemory", "pg"])
async def service(request, pg_session):
    """Fixture parametrizado — misma suite corre sobre Fake e implementación PG real."""
    if request.param == "inmemory":
        return InMemoryParametrosService()

    from src.shared.infrastructure.repositories.parametros_repository_pg import ParametrosRepositoryPG
    from src.shared.infrastructure.seed_parametros import seed_parametros_pg
    from sqlalchemy.ext.asyncio import async_sessionmaker

    # Sembrar los parámetros base en la transacción anidada del pg_session
    # (misma conexión, rollback automático al final del test).
    repo = ParametrosRepositoryPG(pg_session)
    from src.shared.infrastructure.seed_parametros import PARAMETROS_SEED
    from src.shared.infrastructure.models.sistema_model import ParametrosSistemaModel
    from sqlalchemy import select

    for clave, modulo, valor, descripcion, modificable_por in PARAMETROS_SEED:
        existente = (await pg_session.execute(
            select(ParametrosSistemaModel).where(ParametrosSistemaModel.clave == clave)
        )).scalar_one_or_none()
        if existente is None:
            from src.shared.infrastructure.repositories.parametros_repository_pg import _serializar
            valor_str, tipo_valor = _serializar(valor)
            pg_session.add(ParametrosSistemaModel(
                clave=clave, modulo=modulo, valor=valor_str, tipo_valor=tipo_valor,
                valor_defecto=valor_str, descripcion=descripcion, modificable_por=modificable_por,
            ))
    await pg_session.flush()
    return repo


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


@pytest.mark.asyncio
async def test_listar_incluye_parametros_base(service):
    resultados = await service.listar()
    claves = {r.clave for r in resultados}
    assert "max_consultas_precio_sesion" in claves
    assert "taller.ot_activa.dias_maximo" in claves


@pytest.mark.asyncio
async def test_establecer_actualiza_valor(service):
    await service.establecer("reintentos_notificacion", 5)
    result = await service.obtener_parametro("reintentos_notificacion")
    assert result.valor == 5


@pytest.mark.asyncio
async def test_modificable_por_ttl_es_superadmin(service):
    result = await service.obtener_parametro("ttl_cache_parametros_segundos")
    assert result.modificable_por == "SUPERADMIN"

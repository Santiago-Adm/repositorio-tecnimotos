"""
Tests unitarios para shared/infrastructure/ y shared/events/event_bus.py.
Todos los componentes de infraestructura real se substituyen con mocks.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ══════════════════════════════════════════════════════════════════════
# shared/events/event_bus.py — EventBus con Redis mockeado
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_eventbus_initialize_crea_consumer_groups():
    """EventBus.initialize() crea consumer groups en Redis Streams."""
    from src.shared.events.event_bus import EventBus, CONSUMER_GROUPS, TOPICO_SUBSCRIPTIONS

    redis_mock = AsyncMock()
    redis_mock.xgroup_create = AsyncMock(return_value="OK")

    bus = EventBus(redis_mock)
    await bus.initialize()

    assert bus._initialized is True
    # Cada combinación group/tópico debe haber llamado xgroup_create
    total_calls = sum(len(v) for v in TOPICO_SUBSCRIPTIONS.values())
    assert redis_mock.xgroup_create.call_count == total_calls


@pytest.mark.asyncio
async def test_eventbus_initialize_idempotente():
    """EventBus.initialize() no ejecuta de nuevo si ya fue inicializado."""
    from src.shared.events.event_bus import EventBus

    redis_mock = AsyncMock()
    bus = EventBus(redis_mock)
    await bus.initialize()
    call_count_1 = redis_mock.xgroup_create.call_count
    await bus.initialize()  # segunda llamada — debe ser noop
    assert redis_mock.xgroup_create.call_count == call_count_1  # sin cambio


@pytest.mark.asyncio
async def test_eventbus_initialize_ignora_busygroup():
    """EventBus.initialize() ignora 'BUSYGROUP' (consumer group ya existe)."""
    from src.shared.events.event_bus import EventBus

    redis_mock = AsyncMock()
    redis_mock.xgroup_create = AsyncMock(side_effect=Exception("BUSYGROUP Consumer Group name already exists"))

    bus = EventBus(redis_mock)
    await bus.initialize()  # no debe propagar la excepción
    assert bus._initialized is True


@pytest.mark.asyncio
async def test_eventbus_initialize_loguea_otros_errores():
    """EventBus.initialize() loguea como warning errores distintos a BUSYGROUP."""
    from src.shared.events.event_bus import EventBus

    redis_mock = AsyncMock()
    redis_mock.xgroup_create = AsyncMock(side_effect=Exception("Connection refused"))

    bus = EventBus(redis_mock)
    with patch("src.shared.events.event_bus.logger") as mock_logger:
        await bus.initialize()
    assert mock_logger.warning.called


@pytest.mark.asyncio
async def test_eventbus_publish_retorna_msg_id():
    """EventBus.publish() llama xadd y retorna el message ID."""
    from src.shared.events.event_bus import EventBus
    from src.shared.events.envelope import EventEnvelope

    redis_mock = AsyncMock()
    redis_mock.xadd = AsyncMock(return_value="1234567890-0")

    bus = EventBus(redis_mock)
    env = EventEnvelope(tipo="repuesto.creado", modulo_origen="catalogo", payload={"id": "r1"})
    msg_id = await bus.publish(env)

    assert msg_id == "1234567890-0"
    redis_mock.xadd.assert_called_once()
    call_args = redis_mock.xadd.call_args
    assert call_args[0][0] == "repuesto.creado"


# ══════════════════════════════════════════════════════════════════════
# shared/infrastructure/fernet.py
# ══════════════════════════════════════════════════════════════════════

def test_fernet_genera_key_cuando_no_configurada(monkeypatch):
    """get_fernet() genera una clave si FERNET_KEY está vacío."""
    import src.shared.infrastructure.fernet as fernet_mod
    fernet_mod._fernet = None  # reset singleton

    monkeypatch.setenv("FERNET_KEY", "")
    # limpiar cache de settings para que tome el env var
    from src.shared.infrastructure.settings import get_settings
    get_settings.cache_clear()

    f = fernet_mod.get_fernet()
    assert f is not None
    fernet_mod._fernet = None  # cleanup
    get_settings.cache_clear()


def test_fernet_usa_key_configurada(monkeypatch):
    """get_fernet() usa la clave provista en settings cuando existe."""
    from cryptography.fernet import Fernet
    import src.shared.infrastructure.fernet as fernet_mod
    fernet_mod._fernet = None  # reset singleton

    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("FERNET_KEY", test_key)
    from src.shared.infrastructure.settings import get_settings
    get_settings.cache_clear()

    f = fernet_mod.get_fernet()
    assert f is not None
    fernet_mod._fernet = None
    get_settings.cache_clear()


def test_fernet_singleton_retorna_misma_instancia(monkeypatch):
    """get_fernet() retorna la misma instancia en llamadas sucesivas."""
    from cryptography.fernet import Fernet
    import src.shared.infrastructure.fernet as fernet_mod
    fernet_mod._fernet = None

    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("FERNET_KEY", test_key)
    from src.shared.infrastructure.settings import get_settings
    get_settings.cache_clear()

    f1 = fernet_mod.get_fernet()
    f2 = fernet_mod.get_fernet()
    assert f1 is f2
    fernet_mod._fernet = None
    get_settings.cache_clear()


def test_fernet_encrypt_decrypt_roundtrip(monkeypatch):
    """encrypt() y decrypt() son operaciones inversas."""
    from cryptography.fernet import Fernet
    import src.shared.infrastructure.fernet as fernet_mod
    fernet_mod._fernet = None

    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("FERNET_KEY", test_key)
    from src.shared.infrastructure.settings import get_settings
    get_settings.cache_clear()

    plaintext = "precio_costo_secreto_123"
    encrypted = fernet_mod.encrypt(plaintext)
    decrypted = fernet_mod.decrypt(encrypted)

    assert decrypted == plaintext
    assert encrypted != plaintext
    fernet_mod._fernet = None
    get_settings.cache_clear()


# ══════════════════════════════════════════════════════════════════════
# shared/infrastructure/database.py
# ══════════════════════════════════════════════════════════════════════

def test_create_engine_usa_database_url_parametro():
    """create_engine() usa el url pasado como parámetro — asyncpg mockeado."""
    mock_engine = MagicMock()
    with patch("src.shared.infrastructure.database.create_async_engine", return_value=mock_engine) as m:
        from src.shared.infrastructure.database import create_engine
        engine = create_engine(database_url="postgresql+asyncpg://test/db")
    assert engine is mock_engine
    call_url = m.call_args[0][0]
    assert "test/db" in call_url


def test_create_engine_usa_settings_por_defecto():
    """create_engine() sin parámetro lee la URL de settings (branch: database_url is None)."""
    mock_engine = MagicMock()
    with patch("src.shared.infrastructure.database.create_async_engine", return_value=mock_engine):
        from src.shared.infrastructure.database import create_engine
        engine = create_engine()  # url = None → usa settings.database_url
    assert engine is mock_engine


def test_create_session_factory_con_engine_dado():
    """create_session_factory() acepta engine externo sin crear uno nuevo."""
    mock_engine = MagicMock()
    mock_factory = MagicMock()
    with patch("src.shared.infrastructure.database.async_sessionmaker", return_value=mock_factory):
        from src.shared.infrastructure.database import create_session_factory
        factory = create_session_factory(engine=mock_engine)
    assert factory is mock_factory


def test_create_session_factory_sin_engine_crea_uno():
    """create_session_factory() sin engine entra en la rama if engine is None."""
    mock_engine = MagicMock()
    mock_factory = MagicMock()
    with patch("src.shared.infrastructure.database.create_async_engine", return_value=mock_engine), \
         patch("src.shared.infrastructure.database.async_sessionmaker", return_value=mock_factory):
        from src.shared.infrastructure.database import create_session_factory
        factory = create_session_factory()  # engine=None → create_engine() interno
    assert factory is mock_factory


@pytest.mark.asyncio
async def test_get_db_session_commit_en_exito():
    """get_db_session() hace commit al salir sin excepción."""
    from src.shared.infrastructure.database import get_db_session

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_factory = MagicMock(return_value=mock_session)

    gen = get_db_session(mock_factory)
    session = await gen.__anext__()
    assert session is mock_session
    try:
        await gen.asend(None)
    except StopAsyncIteration:
        pass
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_db_session_rollback_en_excepcion():
    """get_db_session() hace rollback cuando ocurre una excepción."""
    from src.shared.infrastructure.database import get_db_session

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    mock_factory = MagicMock(return_value=mock_session)

    gen = get_db_session(mock_factory)
    await gen.__anext__()
    try:
        await gen.athrow(RuntimeError("db error"))
    except RuntimeError:
        pass
    mock_session.rollback.assert_called_once()

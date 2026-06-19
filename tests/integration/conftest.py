"""Fixtures compartidos para todos los tests de integración."""
import pytest
from httpx import AsyncClient, ASGITransport

from api.main import create_app


@pytest.fixture
async def app_client():
    """AsyncClient contra la app FastAPI con repositorios en memoria."""
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        client.app = app
        yield client

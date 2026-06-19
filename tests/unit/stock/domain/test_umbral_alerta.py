"""
Test específico del criterio 09 §3.3 — Umbral de alerta.
Verifica: alerta generada al cruzar umbral mínimo.
"""
import pytest
from decimal import Decimal

from src.stock.application.use_cases.ajustar_stock import (
    AjustarStockCommand,
    AjustarStockUseCase,
    ActualizarUmbralCommand,
    ActualizarUmbralUseCase,
)
from src.stock.domain.models.stock import StockRepuesto
from src.stock.infrastructure.repositories.stock_repository_inmemory import (
    InMemoryStockRepository,
)
from src.shared.events.event_bus import InMemoryEventBus


@pytest.fixture
async def repo_con_stock_sobre_umbral() -> InMemoryStockRepository:
    repo = InMemoryStockRepository()
    await repo.guardar(StockRepuesto(
        repuesto_id="rp-001",
        codigo="REP-001",
        cantidad_disponible=10,
        umbral_minimo=3,
    ))
    return repo


@pytest.fixture
async def repo_con_stock_agotado() -> InMemoryStockRepository:
    repo = InMemoryStockRepository()
    await repo.guardar(StockRepuesto(
        repuesto_id="rp-002",
        codigo="REP-002",
        cantidad_disponible=0,
        umbral_minimo=2,
    ))
    return repo


class TestUmbralAlerta:
    async def test_alerta_bajo_umbral_al_descontar(self, repo_con_stock_sobre_umbral, event_bus):
        """Descontar de 10 a 2 cruza umbral=3 → alerta publicada."""
        uc = AjustarStockUseCase(repo_con_stock_sobre_umbral, event_bus)
        await uc.execute(
            AjustarStockCommand(
                codigo="REP-001",
                cantidad=-8,
                actor_id="user-1",
                motivo="ajuste test",
            )
        )
        assert event_bus.fue_publicado("stock.bajo_umbral")

    async def test_no_alerta_si_sobre_umbral(self, repo_con_stock_sobre_umbral, event_bus):
        """Descontar de 10 a 6 no cruza umbral=3 → sin alerta."""
        uc = AjustarStockUseCase(repo_con_stock_sobre_umbral, event_bus)
        await uc.execute(
            AjustarStockCommand(
                codigo="REP-001",
                cantidad=-4,
                actor_id="user-1",
            )
        )
        assert not event_bus.fue_publicado("stock.bajo_umbral")

    async def test_alerta_agotado_al_llegar_a_cero(self, repo_con_stock_sobre_umbral, event_bus):
        """Descontar de 10 a 0 → alerta agotado."""
        uc = AjustarStockUseCase(repo_con_stock_sobre_umbral, event_bus)
        await uc.execute(
            AjustarStockCommand(
                codigo="REP-001",
                cantidad=-10,
                actor_id="user-1",
            )
        )
        assert event_bus.fue_publicado("stock.agotado")

    async def test_alerta_disponible_al_reabastecer_desde_cero(
        self, repo_con_stock_agotado, event_bus
    ):
        """Agregar stock desde 0 → alerta disponible."""
        uc = AjustarStockUseCase(repo_con_stock_agotado, event_bus)
        await uc.execute(
            AjustarStockCommand(
                codigo="REP-002",
                cantidad=5,
                actor_id="user-1",
            )
        )
        assert event_bus.fue_publicado("stock.disponible")

    async def test_no_alerta_al_ajustar_a_cero_sin_umbral(self, event_bus):
        """Sin umbral configurado, no se genera alerta bajo_umbral."""
        repo = InMemoryStockRepository()
        await repo.guardar(StockRepuesto(
            repuesto_id="rp-x",
            codigo="REP-X",
            cantidad_disponible=5,
            umbral_minimo=0,
        ))
        uc = AjustarStockUseCase(repo, event_bus)
        await uc.execute(
            AjustarStockCommand(codigo="REP-X", cantidad=-4, actor_id="user-1")
        )
        assert not event_bus.fue_publicado("stock.bajo_umbral")

    async def test_ajuste_sin_cambio_cuando_cantidad_cero(
        self, repo_con_stock_sobre_umbral, event_bus
    ):
        """Ajuste con cantidad=0 no modifica stock ni publica eventos."""
        uc = AjustarStockUseCase(repo_con_stock_sobre_umbral, event_bus)
        await uc.execute(
            AjustarStockCommand(codigo="REP-001", cantidad=0, actor_id="user-1")
        )
        s = await repo_con_stock_sobre_umbral.obtener_por_codigo("REP-001")
        assert s.cantidad_disponible == 10
        assert len(event_bus.get_published()) == 0

    async def test_actualizar_umbral(self, repo_con_stock_sobre_umbral):
        uc = ActualizarUmbralUseCase(repo_con_stock_sobre_umbral)
        stock = await uc.execute(
            ActualizarUmbralCommand(
                codigo="REP-001",
                umbral_minimo=15,
                actor_id="user-1",
            )
        )
        assert stock.umbral_minimo == 15
        assert stock.esta_bajo_umbral() is True

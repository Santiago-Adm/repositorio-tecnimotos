"""
Test específico del criterio 09 §3.3 — Descuento atómico.
Verifica: sin stock negativo posible, todos o ninguno.
"""
import pytest
from decimal import Decimal

from src.stock.application.use_cases.descuento_atomico import (
    DescontarStockAtomicoCommand,
    DescontarStockAtomicoUseCase,
    ItemDescuento,
)
from src.stock.domain.models.stock import StockInsuficienteError, StockNoEncontradoError, StockRepuesto
from src.stock.infrastructure.repositories.stock_repository_inmemory import (
    InMemoryStockRepository,
)
from src.shared.events.event_bus import InMemoryEventBus


@pytest.fixture
async def repo_con_stocks() -> InMemoryStockRepository:
    repo = InMemoryStockRepository()
    await repo.guardar(StockRepuesto(
        repuesto_id="rp-001", codigo="REP-001",
        cantidad_disponible=10, umbral_minimo=3,
    ))
    await repo.guardar(StockRepuesto(
        repuesto_id="rp-002", codigo="REP-002",
        cantidad_disponible=5, umbral_minimo=2,
    ))
    await repo.guardar(StockRepuesto(
        repuesto_id="rp-003", codigo="REP-003",
        cantidad_disponible=0, umbral_minimo=1,
    ))
    return repo


class TestDescontarStockAtomico:
    async def test_descuenta_todos_cuando_hay_suficiente(self, repo_con_stocks, event_bus):
        uc = DescontarStockAtomicoUseCase(repo_con_stocks, event_bus)
        result = await uc.execute(
            DescontarStockAtomicoCommand(
                orden_trabajo_id="ot-001",
                repuestos=[
                    ItemDescuento(repuesto_id="rp-001", cantidad=3),
                    ItemDescuento(repuesto_id="rp-002", cantidad=2),
                ],
                actor_id="user-1",
            )
        )
        assert len(result.movimientos) == 2
        s1 = await repo_con_stocks.obtener_por_repuesto_id("rp-001")
        s2 = await repo_con_stocks.obtener_por_repuesto_id("rp-002")
        assert s1.cantidad_disponible == 7
        assert s2.cantidad_disponible == 3

    async def test_rollback_si_uno_falla(self, repo_con_stocks, event_bus):
        """Si rp-003 tiene 0 unidades, el descuento debe fallar y no tocar rp-001."""
        uc = DescontarStockAtomicoUseCase(repo_con_stocks, event_bus)
        with pytest.raises(StockInsuficienteError):
            await uc.execute(
                DescontarStockAtomicoCommand(
                    orden_trabajo_id="ot-002",
                    repuestos=[
                        ItemDescuento(repuesto_id="rp-001", cantidad=5),
                        ItemDescuento(repuesto_id="rp-003", cantidad=1),
                    ],
                    actor_id="user-1",
                )
            )
        # rp-001 no fue modificado — rollback implícito por validación previa
        s1 = await repo_con_stocks.obtener_por_repuesto_id("rp-001")
        assert s1.cantidad_disponible == 10

    async def test_disponible_nunca_negativo(self, repo_con_stocks, event_bus):
        uc = DescontarStockAtomicoUseCase(repo_con_stocks, event_bus)
        with pytest.raises(StockInsuficienteError):
            await uc.execute(
                DescontarStockAtomicoCommand(
                    orden_trabajo_id="ot-003",
                    repuestos=[
                        ItemDescuento(repuesto_id="rp-002", cantidad=99),
                    ],
                    actor_id="user-1",
                )
            )
        s = await repo_con_stocks.obtener_por_repuesto_id("rp-002")
        assert s.cantidad_disponible >= 0

    async def test_falla_si_repuesto_no_existe(self, repo_con_stocks, event_bus):
        uc = DescontarStockAtomicoUseCase(repo_con_stocks, event_bus)
        with pytest.raises(StockNoEncontradoError):
            await uc.execute(
                DescontarStockAtomicoCommand(
                    orden_trabajo_id="ot-004",
                    repuestos=[
                        ItemDescuento(repuesto_id="rp-inexistente", cantidad=1),
                    ],
                    actor_id="user-1",
                )
            )

    async def test_publica_evento_consumo_registrado(self, repo_con_stocks, event_bus):
        uc = DescontarStockAtomicoUseCase(repo_con_stocks, event_bus)
        await uc.execute(
            DescontarStockAtomicoCommand(
                orden_trabajo_id="ot-005",
                repuestos=[
                    ItemDescuento(repuesto_id="rp-001", cantidad=1),
                ],
                actor_id="user-1",
            )
        )
        assert event_bus.fue_publicado("stock.consumo_registrado")

    async def test_publica_evento_agotado_al_agotar(self, repo_con_stocks, event_bus):
        uc = DescontarStockAtomicoUseCase(repo_con_stocks, event_bus)
        await uc.execute(
            DescontarStockAtomicoCommand(
                orden_trabajo_id="ot-006",
                repuestos=[
                    ItemDescuento(repuesto_id="rp-002", cantidad=5),
                ],
                actor_id="user-1",
            )
        )
        assert event_bus.fue_publicado("stock.agotado")

    async def test_publica_evento_bajo_umbral(self, repo_con_stocks, event_bus):
        """rp-001: disponible=10, umbral=3 → descontar 8 deja 2 → bajo umbral."""
        uc = DescontarStockAtomicoUseCase(repo_con_stocks, event_bus)
        await uc.execute(
            DescontarStockAtomicoCommand(
                orden_trabajo_id="ot-007",
                repuestos=[
                    ItemDescuento(repuesto_id="rp-001", cantidad=8),
                ],
                actor_id="user-1",
            )
        )
        assert event_bus.fue_publicado("stock.bajo_umbral")

    async def test_descuento_cero_no_genera_movimiento(self, repo_con_stocks, event_bus):
        uc = DescontarStockAtomicoUseCase(repo_con_stocks, event_bus)
        result = await uc.execute(
            DescontarStockAtomicoCommand(
                orden_trabajo_id="ot-008",
                repuestos=[
                    ItemDescuento(repuesto_id="rp-001", cantidad=0),
                ],
                actor_id="user-1",
            )
        )
        assert len(result.movimientos) == 0

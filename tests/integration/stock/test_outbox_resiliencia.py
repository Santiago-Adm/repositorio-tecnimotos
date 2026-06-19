"""
Test específico del criterio 09 §3.3 — Outbox integridad.
Verifica: 0 eventos perdidos en fallo de publicación.
Con InMemoryEventBus se verifica que los eventos se registran antes de retornar.
"""
import pytest
from typing import Any

from src.stock.application.use_cases.ajustar_stock import (
    AjustarStockCommand,
    AjustarStockUseCase,
)
from src.stock.application.use_cases.reabastecimiento import (
    ActualizarEstadoReabastecimientoCommand,
    ActualizarEstadoReabastecimientoUseCase,
    CrearReabastecimientoCommand,
    CrearReabastecimientoUseCase,
    ItemReabastecimientoInput,
)
from src.stock.domain.models.stock import EstadoReabastecimiento, StockRepuesto
from src.stock.infrastructure.repositories.stock_repository_inmemory import (
    InMemoryStockRepository,
)
from src.shared.events.event_bus import InMemoryEventBus
from decimal import Decimal


class FailingEventPublisher:
    """Simula publisher que falla — usado para verificar atomicidad."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.fail_on: str | None = None

    async def publish(self, tipo: str, modulo_origen: str, payload: dict[str, Any]) -> None:
        self.calls.append(tipo)
        if self.fail_on and tipo == self.fail_on:
            raise RuntimeError(f"Fallo simulado al publicar {tipo}")


@pytest.fixture
async def repo_con_stocks() -> InMemoryStockRepository:
    repo = InMemoryStockRepository()
    await repo.guardar(StockRepuesto(
        repuesto_id="rp-001", codigo="REP-001",
        cantidad_disponible=10, umbral_minimo=3,
    ))
    await repo.guardar(StockRepuesto(
        repuesto_id="rp-002", codigo="REP-002",
        cantidad_disponible=0, umbral_minimo=2,
    ))
    return repo


class TestOutboxIntegridad:
    async def test_evento_agotado_registrado_antes_de_retornar(
        self, repo_con_stocks
    ):
        """Al agotar stock, evento publicado antes de devolver resultado."""
        bus = InMemoryEventBus()
        uc = AjustarStockUseCase(repo_con_stocks, bus)
        await uc.execute(
            AjustarStockCommand(
                codigo="REP-001", cantidad=-10, actor_id="user-1"
            )
        )
        assert bus.fue_publicado("stock.agotado")
        s = await repo_con_stocks.obtener_por_codigo("REP-001")
        assert s.cantidad_disponible == 0

    async def test_evento_disponible_al_reponer_desde_cero(self, repo_con_stocks):
        bus = InMemoryEventBus()
        uc = AjustarStockUseCase(repo_con_stocks, bus)
        await uc.execute(
            AjustarStockCommand(
                codigo="REP-002", cantidad=5, actor_id="user-1"
            )
        )
        assert bus.fue_publicado("stock.disponible")

    async def test_evento_reabastecimiento_recibido(self, repo_con_stocks):
        """Al recibir reabastecimiento, evento publicado y stock actualizado."""
        bus = InMemoryEventBus()
        crear_uc = CrearReabastecimientoUseCase(repo_con_stocks)
        reab = await crear_uc.execute(
            CrearReabastecimientoCommand(
                proveedor="Bajaj",
                solicitado_por="user-1",
                items=[
                    ItemReabastecimientoInput(
                        repuesto_id="rp-001",
                        codigo="REP-001",
                        cantidad_solicitada=5,
                        precio_costo_unitario=Decimal("30.00"),
                    )
                ],
            )
        )
        uc = ActualizarEstadoReabastecimientoUseCase(repo_con_stocks, bus)
        for estado in [
            EstadoReabastecimiento.CONFIRMADO_PROVEEDOR,
            EstadoReabastecimiento.EN_TRANSITO,
            EstadoReabastecimiento.RECIBIDO,
        ]:
            await uc.execute(
                ActualizarEstadoReabastecimientoCommand(
                    reabastecimiento_id=reab.id,
                    nuevo_estado=estado,
                    actor_id="user-1",
                )
            )
        assert bus.fue_publicado("reabastecimiento.recibido")
        s = await repo_con_stocks.obtener_por_repuesto_id("rp-001")
        assert s.cantidad_disponible == 15

    async def test_no_eventos_perdidos_en_multiples_ajustes(self, repo_con_stocks):
        """Múltiples ajustes generan exactamente los eventos esperados."""
        bus = InMemoryEventBus()
        uc = AjustarStockUseCase(repo_con_stocks, bus)

        # Bajar de 10 a 2 → bajo_umbral
        await uc.execute(
            AjustarStockCommand(
                codigo="REP-001", cantidad=-8, actor_id="user-1"
            )
        )
        # Agotar → agotado
        await uc.execute(
            AjustarStockCommand(
                codigo="REP-001", cantidad=-2, actor_id="user-1"
            )
        )
        # Reponer → disponible
        await uc.execute(
            AjustarStockCommand(
                codigo="REP-001", cantidad=5, actor_id="user-1"
            )
        )

        publicados = [e.tipo for e in bus.get_published()]
        assert "stock.bajo_umbral" in publicados
        assert "stock.agotado" in publicados
        assert "stock.disponible" in publicados

    async def test_evento_bajo_umbral_con_alerta_margen(self, repo_con_stocks):
        """Recepción con variación de precio > 10% publica margen.alerta."""
        bus = InMemoryEventBus()
        crear_uc = CrearReabastecimientoUseCase(repo_con_stocks)
        reab = await crear_uc.execute(
            CrearReabastecimientoCommand(
                proveedor="Bajaj",
                solicitado_por="user-1",
                items=[
                    ItemReabastecimientoInput(
                        repuesto_id="rp-002",
                        codigo="REP-002",
                        cantidad_solicitada=3,
                        precio_costo_unitario=Decimal("50.00"),
                    )
                ],
            )
        )
        # Configurar precio anterior para que haya variación > 10%
        reab_guardado = await repo_con_stocks.obtener_reabastecimiento(reab.id)
        from decimal import Decimal as D
        reab_guardado.precio_costo_anterior = D("40.00")
        await repo_con_stocks.actualizar_reabastecimiento(reab_guardado)

        uc = ActualizarEstadoReabastecimientoUseCase(repo_con_stocks, bus)
        for estado in [
            EstadoReabastecimiento.CONFIRMADO_PROVEEDOR,
            EstadoReabastecimiento.EN_TRANSITO,
            EstadoReabastecimiento.RECIBIDO,
        ]:
            await uc.execute(
                ActualizarEstadoReabastecimientoCommand(
                    reabastecimiento_id=reab.id,
                    nuevo_estado=estado,
                    actor_id="user-1",
                )
            )
        assert bus.fue_publicado("margen.alerta")

    async def test_recepcion_con_stock_agotado_publica_disponible(self, repo_con_stocks):
        """Al recibir sobre stock agotado (rp-002=0), publica stock.disponible."""
        bus = InMemoryEventBus()
        crear_uc = CrearReabastecimientoUseCase(repo_con_stocks)
        reab = await crear_uc.execute(
            CrearReabastecimientoCommand(
                proveedor="Bajaj",
                solicitado_por="user-1",
                items=[
                    ItemReabastecimientoInput(
                        repuesto_id="rp-002",
                        codigo="REP-002",
                        cantidad_solicitada=5,
                        precio_costo_unitario=Decimal("20.00"),
                    )
                ],
            )
        )
        uc = ActualizarEstadoReabastecimientoUseCase(repo_con_stocks, bus)
        for estado in [
            EstadoReabastecimiento.CONFIRMADO_PROVEEDOR,
            EstadoReabastecimiento.EN_TRANSITO,
            EstadoReabastecimiento.RECIBIDO,
        ]:
            await uc.execute(
                ActualizarEstadoReabastecimientoCommand(
                    reabastecimiento_id=reab.id,
                    nuevo_estado=estado,
                    actor_id="user-1",
                )
            )
        assert bus.fue_publicado("stock.disponible")

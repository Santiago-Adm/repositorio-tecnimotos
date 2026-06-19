"""
Tests de integración de servicio — módulo stock.
Ejercita los use cases y el dominio directamente (sin HTTP) para completar
la cobertura de integración requerida en 09 §3.3: ≥ 85% line coverage.
Cubre: DescontarStockAtomicoUseCase, StockServiceImpl, paths de dominio
(apartar, liberar, descontar_apartado_taller, validaciones de Reabastecimiento).
"""
import pytest
from decimal import Decimal

from src.shared.events.event_bus import InMemoryEventBus
from src.stock.application.use_cases.descuento_atomico import (
    DescontarStockAtomicoCommand,
    DescontarStockAtomicoUseCase,
    ItemDescuento,
)
from src.stock.application.use_cases.reabastecimiento import (
    ActualizarEstadoReabastecimientoCommand,
    ActualizarEstadoReabastecimientoUseCase,
    CrearReabastecimientoCommand,
    CrearReabastecimientoUseCase,
    ItemReabastecimientoInput,
)
from src.stock.domain.models.stock import (
    DomainError,
    EstadoReabastecimiento,
    Reabastecimiento,
    ReabastecimientoItem,
    StockInsuficienteError,
    StockNoEncontradoError,
    StockRepuesto,
    TransicionEstadoInvalidaError,
)
from src.stock.infrastructure.adapters.stock_service_impl import StockServiceImpl
from src.stock.infrastructure.repositories.stock_repository_inmemory import (
    InMemoryStockRepository,
)


@pytest.fixture
async def repo() -> InMemoryStockRepository:
    r = InMemoryStockRepository()
    await r.guardar(StockRepuesto(
        repuesto_id="rp-001", codigo="REP-001",
        cantidad_disponible=10, umbral_minimo=3,
    ))
    await r.guardar(StockRepuesto(
        repuesto_id="rp-002", codigo="REP-002",
        cantidad_disponible=5, umbral_minimo=2,
    ))
    await r.guardar(StockRepuesto(
        repuesto_id="rp-003", codigo="REP-003",
        cantidad_disponible=0, umbral_minimo=1,
    ))
    return r


@pytest.fixture
def bus() -> InMemoryEventBus:
    return InMemoryEventBus()


# ── DescontarStockAtomicoUseCase — integración completa ──────────────────────

class TestDescontarStockAtomicoIntegracion:
    async def test_descuenta_multiples_repuestos(self, repo, bus):
        uc = DescontarStockAtomicoUseCase(repo, bus)
        result = await uc.execute(DescontarStockAtomicoCommand(
            orden_trabajo_id="ot-001",
            repuestos=[
                ItemDescuento(repuesto_id="rp-001", cantidad=3),
                ItemDescuento(repuesto_id="rp-002", cantidad=2),
            ],
            actor_id="user-1",
        ))
        assert len(result.movimientos) == 2
        s1 = await repo.obtener_por_repuesto_id("rp-001")
        s2 = await repo.obtener_por_repuesto_id("rp-002")
        assert s1.cantidad_disponible == 7
        assert s2.cantidad_disponible == 3

    async def test_falla_si_uno_sin_stock_suficiente(self, repo, bus):
        uc = DescontarStockAtomicoUseCase(repo, bus)
        with pytest.raises(StockInsuficienteError):
            await uc.execute(DescontarStockAtomicoCommand(
                orden_trabajo_id="ot-002",
                repuestos=[
                    ItemDescuento(repuesto_id="rp-001", cantidad=5),
                    ItemDescuento(repuesto_id="rp-003", cantidad=1),
                ],
                actor_id="user-1",
            ))
        s1 = await repo.obtener_por_repuesto_id("rp-001")
        assert s1.cantidad_disponible == 10

    async def test_falla_si_repuesto_no_existe(self, repo, bus):
        uc = DescontarStockAtomicoUseCase(repo, bus)
        with pytest.raises(StockNoEncontradoError):
            await uc.execute(DescontarStockAtomicoCommand(
                orden_trabajo_id="ot-003",
                repuestos=[ItemDescuento(repuesto_id="rp-999", cantidad=1)],
                actor_id="user-1",
            ))

    async def test_publica_evento_consumo(self, repo, bus):
        uc = DescontarStockAtomicoUseCase(repo, bus)
        await uc.execute(DescontarStockAtomicoCommand(
            orden_trabajo_id="ot-004",
            repuestos=[ItemDescuento(repuesto_id="rp-001", cantidad=1)],
            actor_id="user-1",
        ))
        assert bus.fue_publicado("stock.consumo_registrado")

    async def test_publica_evento_agotado(self, repo, bus):
        uc = DescontarStockAtomicoUseCase(repo, bus)
        await uc.execute(DescontarStockAtomicoCommand(
            orden_trabajo_id="ot-005",
            repuestos=[ItemDescuento(repuesto_id="rp-002", cantidad=5)],
            actor_id="user-1",
        ))
        assert bus.fue_publicado("stock.agotado")

    async def test_publica_evento_bajo_umbral(self, repo, bus):
        uc = DescontarStockAtomicoUseCase(repo, bus)
        await uc.execute(DescontarStockAtomicoCommand(
            orden_trabajo_id="ot-006",
            repuestos=[ItemDescuento(repuesto_id="rp-001", cantidad=8)],
            actor_id="user-1",
        ))
        assert bus.fue_publicado("stock.bajo_umbral")

    async def test_descuento_cero_sin_movimiento(self, repo, bus):
        uc = DescontarStockAtomicoUseCase(repo, bus)
        result = await uc.execute(DescontarStockAtomicoCommand(
            orden_trabajo_id="ot-007",
            repuestos=[ItemDescuento(repuesto_id="rp-001", cantidad=0)],
            actor_id="user-1",
        ))
        assert len(result.movimientos) == 0


# ── StockServiceImpl — apartar y liberar ─────────────────────────────────────

class TestStockServiceImplIntegracion:
    async def test_apartar_y_liberar_ciclo_completo(self, repo):
        svc = StockServiceImpl(repo)

        # apartar 5 de rp-001 (disponible=10)
        ok = await svc.apartar_stock("rp-001", 5, "user-1", "ped-001")
        assert ok is True
        s = await repo.obtener_por_repuesto_id("rp-001")
        assert s.cantidad_disponible == 5
        assert s.cantidad_apartada == 5

        # liberar 3
        ok = await svc.liberar_stock("rp-001", 3, "user-1", "ped-001")
        assert ok is True
        s = await repo.obtener_por_repuesto_id("rp-001")
        assert s.cantidad_disponible == 8
        assert s.cantidad_apartada == 2

    async def test_apartar_insuficiente_retorna_false(self, repo):
        svc = StockServiceImpl(repo)
        ok = await svc.apartar_stock("rp-001", 100, "user-1", "ped-002")
        assert ok is False
        s = await repo.obtener_por_repuesto_id("rp-001")
        assert s.cantidad_disponible == 10

    async def test_liberar_mas_de_lo_apartado_retorna_false(self, repo):
        svc = StockServiceImpl(repo)
        ok = await svc.liberar_stock("rp-001", 99, "user-1", "ped-002")
        assert ok is False


# ── Dominio: apartar / liberar_apartado / descontar_apartado_taller ──────────

class TestDominioPaths:
    def test_apartar_valido(self):
        s = StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_disponible=10)
        mov = s.apartar(4, actor_id="user-1", referencia_id="ped-1")
        assert s.cantidad_disponible == 6
        assert s.cantidad_apartada == 4

    def test_apartar_cero_raise(self):
        s = StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_disponible=10)
        with pytest.raises(DomainError):
            s.apartar(0, actor_id="user-1")

    def test_apartar_insuficiente_raise(self):
        s = StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_disponible=3)
        with pytest.raises(StockInsuficienteError):
            s.apartar(5, actor_id="user-1")

    def test_liberar_valido(self):
        s = StockRepuesto(
            repuesto_id="rp-x", codigo="X",
            cantidad_disponible=5, cantidad_apartada=5
        )
        mov = s.liberar_apartado(3, actor_id="user-1", referencia_id="lib-1")
        assert s.cantidad_disponible == 8
        assert s.cantidad_apartada == 2

    def test_liberar_cero_raise(self):
        s = StockRepuesto(
            repuesto_id="rp-x", codigo="X",
            cantidad_disponible=5, cantidad_apartada=5
        )
        with pytest.raises(DomainError):
            s.liberar_apartado(0, actor_id="user-1")

    def test_liberar_mas_de_apartado_raise(self):
        s = StockRepuesto(
            repuesto_id="rp-x", codigo="X",
            cantidad_disponible=5, cantidad_apartada=2
        )
        with pytest.raises(DomainError):
            s.liberar_apartado(5, actor_id="user-1")

    def test_descontar_apartado_taller_valido(self):
        s = StockRepuesto(
            repuesto_id="rp-x", codigo="X",
            cantidad_disponible=0, cantidad_apartada=5
        )
        mov = s.descontar_apartado_taller(3, actor_id="user-1", referencia_id="ot-1")
        assert s.cantidad_apartada == 2

    def test_descontar_apartado_taller_cero_raise(self):
        s = StockRepuesto(
            repuesto_id="rp-x", codigo="X",
            cantidad_disponible=0, cantidad_apartada=5
        )
        with pytest.raises(DomainError):
            s.descontar_apartado_taller(0, actor_id="user-1")

    def test_descontar_apartado_taller_insuficiente_raise(self):
        s = StockRepuesto(
            repuesto_id="rp-x", codigo="X",
            cantidad_disponible=0, cantidad_apartada=2
        )
        with pytest.raises(StockInsuficienteError):
            s.descontar_apartado_taller(5, actor_id="user-1")

    def test_stock_disponible_negativo_raise(self):
        with pytest.raises(DomainError):
            StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_disponible=-1)

    def test_stock_apartado_negativo_raise(self):
        with pytest.raises(DomainError):
            StockRepuesto(repuesto_id="rp-x", codigo="X", cantidad_apartada=-1)


# ── Reabastecimiento: paths de error del dominio ─────────────────────────────

class TestReabastecimientoDominioPaths:
    def test_proveedor_vacio_raise(self):
        with pytest.raises(DomainError):
            Reabastecimiento(proveedor="", solicitado_por="user-1")

    def test_proveedor_solo_espacios_raise(self):
        with pytest.raises(DomainError):
            Reabastecimiento(proveedor="   ", solicitado_por="user-1")

    def test_transicion_invalida_raise(self):
        reab = Reabastecimiento(proveedor="X", solicitado_por="user-1")
        with pytest.raises(TransicionEstadoInvalidaError):
            reab.avanzar_estado(EstadoReabastecimiento.RECIBIDO)

    def test_agregar_item_en_estado_no_solicitado_raise(self):
        reab = Reabastecimiento(proveedor="X", solicitado_por="user-1")
        reab.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)
        with pytest.raises(DomainError):
            reab.agregar_item(ReabastecimientoItem(
                repuesto_id="rp-1", codigo="R",
                cantidad_solicitada=5,
                precio_costo_unitario=Decimal("10.00"),
            ))

    def test_esta_recibido_true(self):
        reab = Reabastecimiento(proveedor="X", solicitado_por="user-1")
        reab.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)
        reab.avanzar_estado(EstadoReabastecimiento.EN_TRANSITO)
        reab.avanzar_estado(EstadoReabastecimiento.RECIBIDO)
        assert reab.esta_recibido() is True

    def test_esta_cancelado_true(self):
        reab = Reabastecimiento(proveedor="X", solicitado_por="user-1")
        reab.avanzar_estado(EstadoReabastecimiento.CANCELADO)
        assert reab.esta_cancelado() is True

    def test_reab_item_cantidad_cero_raise(self):
        with pytest.raises(DomainError):
            ReabastecimientoItem(
                repuesto_id="rp-1", codigo="R",
                cantidad_solicitada=0,
                precio_costo_unitario=Decimal("10.00"),
            )

    def test_reab_item_precio_negativo_raise(self):
        with pytest.raises(DomainError):
            ReabastecimientoItem(
                repuesto_id="rp-1", codigo="R",
                cantidad_solicitada=5,
                precio_costo_unitario=Decimal("-1.00"),
            )


# ── Reabastecimiento: flujo completo con recepción y eventos ─────────────────

class TestReabastecimientoFlujoIntegracion:
    async def test_flujo_hasta_recibido_con_stock_existente(self, repo, bus):
        crear_uc = CrearReabastecimientoUseCase(repo)
        reab = await crear_uc.execute(CrearReabastecimientoCommand(
            proveedor="Bajaj Perú",
            solicitado_por="user-1",
            items=[ItemReabastecimientoInput(
                repuesto_id="rp-001",
                codigo="REP-001",
                cantidad_solicitada=20,
                precio_costo_unitario=Decimal("25.00"),
            )],
        ))
        uc = ActualizarEstadoReabastecimientoUseCase(repo, bus)
        for estado in [
            EstadoReabastecimiento.CONFIRMADO_PROVEEDOR,
            EstadoReabastecimiento.EN_TRANSITO,
            EstadoReabastecimiento.RECIBIDO,
        ]:
            reab = await uc.execute(ActualizarEstadoReabastecimientoCommand(
                reabastecimiento_id=reab.id,
                nuevo_estado=estado,
                actor_id="user-1",
            ))
        assert reab.esta_recibido() is True
        s = await repo.obtener_por_repuesto_id("rp-001")
        assert s.cantidad_disponible == 30
        assert bus.fue_publicado("reabastecimiento.recibido")

    async def test_flujo_cancelado(self, repo, bus):
        crear_uc = CrearReabastecimientoUseCase(repo)
        reab = await crear_uc.execute(CrearReabastecimientoCommand(
            proveedor="Bajaj",
            solicitado_por="user-1",
            items=[ItemReabastecimientoInput(
                repuesto_id="rp-002",
                codigo="REP-002",
                cantidad_solicitada=5,
                precio_costo_unitario=Decimal("15.00"),
            )],
        ))
        uc = ActualizarEstadoReabastecimientoUseCase(repo, bus)
        reab = await uc.execute(ActualizarEstadoReabastecimientoCommand(
            reabastecimiento_id=reab.id,
            nuevo_estado=EstadoReabastecimiento.CANCELADO,
            actor_id="user-1",
        ))
        assert reab.esta_cancelado() is True

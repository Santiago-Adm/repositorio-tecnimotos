"""
Tests unitarios — infraestructura del módulo stock.
Cubre InMemoryStockRepository, StockServiceImpl, InMemoryStockService.
Meta: ≥ 70% line coverage (09 §3.3).
"""
import pytest
from decimal import Decimal

from src.stock.domain.models.stock import (
    EstadoReabastecimiento,
    Reabastecimiento,
    ReabastecimientoItem,
    StockInsuficienteError,
    StockNoEncontradoError,
    StockRepuesto,
)
from src.stock.infrastructure.adapters.stock_service_impl import (
    InMemoryStockService,
    StockServiceImpl,
)
from src.stock.infrastructure.repositories.stock_repository_inmemory import (
    InMemoryStockRepository,
)


# ── InMemoryStockRepository ───────────────────────────────────────────────────

class TestInMemoryStockRepository:
    async def test_guardar_y_obtener_por_repuesto_id(self):
        repo = InMemoryStockRepository()
        s = StockRepuesto(repuesto_id="rp-1", codigo="REP-001", cantidad_disponible=10)
        await repo.guardar(s)
        resultado = await repo.obtener_por_repuesto_id("rp-1")
        assert resultado is not None
        assert resultado.codigo == "REP-001"

    async def test_obtener_por_repuesto_id_inexistente(self):
        repo = InMemoryStockRepository()
        resultado = await repo.obtener_por_repuesto_id("rp-999")
        assert resultado is None

    async def test_obtener_por_codigo(self):
        repo = InMemoryStockRepository()
        s = StockRepuesto(repuesto_id="rp-1", codigo="REP-001", cantidad_disponible=5)
        await repo.guardar(s)
        resultado = await repo.obtener_por_codigo("REP-001")
        assert resultado is not None
        assert resultado.repuesto_id == "rp-1"

    async def test_obtener_por_codigo_inexistente(self):
        repo = InMemoryStockRepository()
        resultado = await repo.obtener_por_codigo("NINGUNO")
        assert resultado is None

    async def test_listar_todos(self):
        repo = InMemoryStockRepository()
        await repo.guardar(StockRepuesto(repuesto_id="rp-1", codigo="REP-001"))
        await repo.guardar(StockRepuesto(repuesto_id="rp-2", codigo="REP-002"))
        todos = await repo.listar_todos()
        assert len(todos) == 2

    async def test_actualizar_stock(self):
        repo = InMemoryStockRepository()
        s = StockRepuesto(repuesto_id="rp-1", codigo="REP-001", cantidad_disponible=5)
        await repo.guardar(s)
        s.registrar_entrada(10, actor_id="user-1")
        await repo.actualizar(s)
        resultado = await repo.obtener_por_repuesto_id("rp-1")
        assert resultado.cantidad_disponible == 15

    async def test_actualizar_registra_movimientos_nuevos(self):
        repo = InMemoryStockRepository()
        s = StockRepuesto(repuesto_id="rp-1", codigo="REP-001", cantidad_disponible=10)
        await repo.guardar(s)
        s.registrar_entrada(5, actor_id="user-1")
        await repo.actualizar(s)
        movs = await repo.obtener_movimientos("rp-1")
        assert len(movs) == 1

    async def test_actualizar_no_duplica_movimientos(self):
        repo = InMemoryStockRepository()
        s = StockRepuesto(repuesto_id="rp-1", codigo="REP-001", cantidad_disponible=10)
        await repo.guardar(s)
        s.registrar_entrada(5, actor_id="user-1")
        await repo.actualizar(s)
        await repo.actualizar(s)
        movs = await repo.obtener_movimientos("rp-1")
        assert len(movs) == 1

    async def test_actualizar_stock_inexistente_falla(self):
        repo = InMemoryStockRepository()
        s = StockRepuesto(repuesto_id="rp-999", codigo="X")
        with pytest.raises(ValueError):
            await repo.actualizar(s)

    async def test_obtener_movimientos_vacio(self):
        repo = InMemoryStockRepository()
        movs = await repo.obtener_movimientos("rp-inexistente")
        assert movs == []

    async def test_guardar_y_obtener_reabastecimiento(self):
        repo = InMemoryStockRepository()
        reab = Reabastecimiento(proveedor="Bajaj", solicitado_por="user-1")
        await repo.guardar_reabastecimiento(reab)
        resultado = await repo.obtener_reabastecimiento(reab.id)
        assert resultado is not None
        assert resultado.proveedor == "Bajaj"

    async def test_obtener_reabastecimiento_inexistente(self):
        repo = InMemoryStockRepository()
        resultado = await repo.obtener_reabastecimiento("id-999")
        assert resultado is None

    async def test_actualizar_reabastecimiento(self):
        repo = InMemoryStockRepository()
        reab = Reabastecimiento(proveedor="Bajaj", solicitado_por="user-1")
        await repo.guardar_reabastecimiento(reab)
        reab.avanzar_estado(EstadoReabastecimiento.CONFIRMADO_PROVEEDOR)
        await repo.actualizar_reabastecimiento(reab)
        resultado = await repo.obtener_reabastecimiento(reab.id)
        assert resultado.estado == EstadoReabastecimiento.CONFIRMADO_PROVEEDOR

    async def test_actualizar_reabastecimiento_inexistente_falla(self):
        repo = InMemoryStockRepository()
        reab = Reabastecimiento(proveedor="X", solicitado_por="y")
        with pytest.raises(ValueError):
            await repo.actualizar_reabastecimiento(reab)

    async def test_limpiar_borra_todo(self):
        repo = InMemoryStockRepository()
        await repo.guardar(StockRepuesto(repuesto_id="rp-1", codigo="REP-001"))
        reab = Reabastecimiento(proveedor="X", solicitado_por="y")
        await repo.guardar_reabastecimiento(reab)
        repo.limpiar()
        assert await repo.listar_todos() == []
        assert await repo.obtener_reabastecimiento(reab.id) is None

    async def test_guardar_stock_inicializa_movimientos(self):
        repo = InMemoryStockRepository()
        s = StockRepuesto(repuesto_id="rp-1", codigo="REP-001")
        await repo.guardar(s)
        movs = await repo.obtener_movimientos("rp-1")
        assert movs == []


# ── StockServiceImpl ──────────────────────────────────────────────────────────

class TestStockServiceImpl:
    @pytest.fixture
    async def repo_con_stock(self):
        repo = InMemoryStockRepository()
        await repo.guardar(StockRepuesto(
            repuesto_id="rp-001", codigo="REP-001",
            cantidad_disponible=10,
        ))
        return repo

    async def test_consultar_disponibilidad(self, repo_con_stock):
        svc = StockServiceImpl(repo_con_stock)
        resp = await svc.consultar_disponibilidad("rp-001")
        assert resp.cantidad_disponible == 10

    async def test_consultar_disponibilidad_no_encontrado(self, repo_con_stock):
        svc = StockServiceImpl(repo_con_stock)
        with pytest.raises(StockNoEncontradoError):
            await svc.consultar_disponibilidad("rp-999")

    async def test_apartar_stock_exito(self, repo_con_stock):
        svc = StockServiceImpl(repo_con_stock)
        resultado = await svc.apartar_stock("rp-001", 3, "user-1", "ped-1")
        assert resultado is True
        s = await repo_con_stock.obtener_por_repuesto_id("rp-001")
        assert s.cantidad_apartada == 3

    async def test_apartar_stock_insuficiente(self, repo_con_stock):
        svc = StockServiceImpl(repo_con_stock)
        resultado = await svc.apartar_stock("rp-001", 100, "user-1", "ped-1")
        assert resultado is False

    async def test_apartar_stock_no_encontrado(self, repo_con_stock):
        svc = StockServiceImpl(repo_con_stock)
        with pytest.raises(StockNoEncontradoError):
            await svc.apartar_stock("rp-999", 1, "user-1", "ped-1")

    async def test_liberar_stock_exito(self, repo_con_stock):
        svc = StockServiceImpl(repo_con_stock)
        await svc.apartar_stock("rp-001", 5, "user-1", "ped-1")
        resultado = await svc.liberar_stock("rp-001", 5, "user-1", "ped-1")
        assert resultado is True

    async def test_liberar_stock_no_encontrado(self, repo_con_stock):
        svc = StockServiceImpl(repo_con_stock)
        resultado = await svc.liberar_stock("rp-999", 1, "user-1", "ped-1")
        assert resultado is False

    async def test_liberar_stock_falla_por_cantidad(self, repo_con_stock):
        """Liberar más de lo apartado retorna False (excepción capturada)."""
        svc = StockServiceImpl(repo_con_stock)
        resultado = await svc.liberar_stock("rp-001", 99, "user-1", "ped-1")
        assert resultado is False


# ── InMemoryStockService ──────────────────────────────────────────────────────

class TestInMemoryStockService:
    def _svc(self) -> InMemoryStockService:
        svc = InMemoryStockService()
        svc.agregar_stock("rp-001", 10)
        return svc

    async def test_consultar_disponibilidad(self):
        svc = self._svc()
        resp = await svc.consultar_disponibilidad("rp-001")
        assert resp.cantidad_disponible == 10

    async def test_consultar_disponibilidad_no_encontrado(self):
        svc = self._svc()
        with pytest.raises(StockNoEncontradoError):
            await svc.consultar_disponibilidad("rp-999")

    async def test_apartar_stock_exito(self):
        svc = self._svc()
        resultado = await svc.apartar_stock("rp-001", 3, "user-1", "ped-1")
        assert resultado is True
        resp = await svc.consultar_disponibilidad("rp-001")
        assert resp.cantidad_disponible == 7

    async def test_apartar_stock_insuficiente(self):
        svc = self._svc()
        resultado = await svc.apartar_stock("rp-001", 100, "user-1", "ped-1")
        assert resultado is False

    async def test_liberar_stock(self):
        svc = self._svc()
        await svc.apartar_stock("rp-001", 5, "user-1", "ped-1")
        resultado = await svc.liberar_stock("rp-001", 5, "user-1", "lib-1")
        assert resultado is True
        resp = await svc.consultar_disponibilidad("rp-001")
        assert resp.cantidad_disponible == 10

"""
Tests unitarios — infraestructura del módulo pedidos.
Meta: ≥ 70% line coverage (09 §3.2).
"""
import pytest
from decimal import Decimal

from src.pedidos.domain.models.pedido import (
    Comprobante,
    DeudaActiva,
    Envio,
    EstadoComprobante,
    ListaReservaProg,
    ListaReservaProg_Item,
    Pedido,
    PedidoItem,
    Proforma,
    Reserva,
    SegmentoCliente,
    TipoComprobante,
)
from src.pedidos.infrastructure.repositories.pedido_repository_inmemory import (
    InMemoryPedidoRepository,
)
from src.pedidos.infrastructure.adapters.catalogo_adapter import (
    InMemoryCatalogoAdapter,
    InMemoryStockAdapter,
)
from src.pedidos.domain.ports.catalogo_pedidos_port import RepuestoInfo
from src.pedidos.domain.models.pedido import DomainError


class TestInMemoryPedidoRepository:
    async def test_guardar_y_obtener_pedido(self):
        repo = InMemoryPedidoRepository()
        pedido = Pedido(canal_origen="presencial", origen_actor="user-1")
        await repo.guardar(pedido)
        resultado = await repo.obtener_por_id(pedido.id)
        assert resultado is not None
        assert resultado.canal_origen == "presencial"

    async def test_obtener_pedido_inexistente(self):
        repo = InMemoryPedidoRepository()
        resultado = await repo.obtener_por_id("id-99")
        assert resultado is None

    async def test_listar_todos(self):
        repo = InMemoryPedidoRepository()
        await repo.guardar(Pedido(canal_origen="a", origen_actor="u"))
        await repo.guardar(Pedido(canal_origen="b", origen_actor="u"))
        todos = await repo.listar_todos()
        assert len(todos) == 2

    async def test_listar_por_cliente(self):
        repo = InMemoryPedidoRepository()
        p1 = Pedido(canal_origen="a", origen_actor="u", cliente_id="cli-1")
        p2 = Pedido(canal_origen="b", origen_actor="u", cliente_id="cli-2")
        await repo.guardar(p1)
        await repo.guardar(p2)
        resultado = await repo.listar_por_cliente("cli-1")
        assert len(resultado) == 1

    async def test_actualizar_pedido(self):
        repo = InMemoryPedidoRepository()
        pedido = Pedido(canal_origen="presencial", origen_actor="u")
        await repo.guardar(pedido)
        pedido.confirmar()
        await repo.actualizar(pedido)
        r = await repo.obtener_por_id(pedido.id)
        from src.pedidos.domain.models.pedido import EstadoPedido
        assert r.estado == EstadoPedido.CONFIRMADO

    async def test_actualizar_pedido_inexistente_falla(self):
        repo = InMemoryPedidoRepository()
        pedido = Pedido(canal_origen="a", origen_actor="u")
        with pytest.raises(ValueError):
            await repo.actualizar(pedido)

    async def test_guardar_y_obtener_reserva(self):
        repo = InMemoryPedidoRepository()
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        await repo.guardar_reserva(r)
        resultado = await repo.obtener_reserva(r.id)
        assert resultado is not None

    async def test_obtener_reserva_inexistente(self):
        repo = InMemoryPedidoRepository()
        assert await repo.obtener_reserva("id-99") is None

    async def test_listar_reservas_por_repuesto(self):
        repo = InMemoryPedidoRepository()
        r1 = Reserva(cliente_id="c1", repuesto_id="rp-1", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        r2 = Reserva(cliente_id="c2", repuesto_id="rp-2", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        await repo.guardar_reserva(r1)
        await repo.guardar_reserva(r2)
        resultado = await repo.listar_reservas_por_repuesto("rp-1")
        assert len(resultado) == 1

    async def test_actualizar_reserva(self):
        repo = InMemoryPedidoRepository()
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        await repo.guardar_reserva(r)
        r.confirmar()
        await repo.actualizar_reserva(r)
        r2 = await repo.obtener_reserva(r.id)
        assert r2.estado == EstadoReserva.CONFIRMADA

    async def test_actualizar_reserva_inexistente_falla(self):
        repo = InMemoryPedidoRepository()
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        with pytest.raises(ValueError):
            await repo.actualizar_reserva(r)

    async def test_guardar_proforma(self):
        repo = InMemoryPedidoRepository()
        p = Proforma(pedido_id="ped-1", numero_referencia="PRF-001", monto_total=Decimal("100"))
        await repo.guardar_proforma(p)
        r = await repo.obtener_proforma(p.id)
        assert r is not None

    async def test_obtener_proforma_inexistente(self):
        repo = InMemoryPedidoRepository()
        assert await repo.obtener_proforma("id-99") is None

    async def test_guardar_envio(self):
        repo = InMemoryPedidoRepository()
        e = Envio(pedido_id="ped-1", empresa_encomienda="Olva", direccion_destino="Huancayo")
        await repo.guardar_envio(e)
        r = await repo.obtener_envio_por_pedido("ped-1")
        assert r is not None

    async def test_obtener_envio_inexistente(self):
        repo = InMemoryPedidoRepository()
        assert await repo.obtener_envio_por_pedido("ped-99") is None

    async def test_guardar_y_actualizar_comprobante(self):
        repo = InMemoryPedidoRepository()
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        await repo.guardar_comprobante(c)
        c.aprobar()
        await repo.actualizar_comprobante(c)
        r = await repo.obtener_comprobante(c.id)
        assert r.estado == EstadoComprobante.EMITIDO

    async def test_obtener_comprobante_inexistente(self):
        repo = InMemoryPedidoRepository()
        assert await repo.obtener_comprobante("id-99") is None

    async def test_actualizar_comprobante_inexistente_falla(self):
        repo = InMemoryPedidoRepository()
        c = Comprobante(pedido_id="p", tipo=TipoComprobante.BOLETA, monto=Decimal("50"), emitido_por="v")
        with pytest.raises(ValueError):
            await repo.actualizar_comprobante(c)

    async def test_guardar_deuda(self):
        repo = InMemoryPedidoRepository()
        d = DeudaActiva(pedido_id="p", cliente_id="c", monto_deuda=Decimal("50"), plazo_dias=7)
        await repo.guardar_deuda(d)

    async def test_lista_reserva_ciclo_completo(self):
        repo = InMemoryPedidoRepository()
        lista = ListaReservaProg(cliente_id="cli-1")
        lista.agregar_item(ListaReservaProg_Item(
            lista_id=lista.id, repuesto_id="rp-1", codigo="R",
            cantidad=2, precio_referencia=Decimal("30.00"),
        ))
        await repo.guardar_lista_reserva(lista)
        r = await repo.obtener_lista_reserva(lista.id)
        assert r is not None
        lista.confirmar()
        await repo.actualizar_lista_reserva(lista)

    async def test_obtener_lista_inexistente(self):
        repo = InMemoryPedidoRepository()
        assert await repo.obtener_lista_reserva("id-99") is None

    async def test_actualizar_lista_inexistente_falla(self):
        repo = InMemoryPedidoRepository()
        lista = ListaReservaProg(cliente_id="c")
        with pytest.raises(ValueError):
            await repo.actualizar_lista_reserva(lista)

    def test_limpiar(self):
        import asyncio
        repo = InMemoryPedidoRepository()
        repo.limpiar()


class TestInMemoryCatalogoAdapter:
    async def test_obtener_precio_vigente(self):
        adapter = InMemoryCatalogoAdapter()
        adapter.agregar_repuesto(RepuestoInfo(
            repuesto_id="rp-1", codigo="REP-001",
            precio_venta=Decimal("45"), nombre="F", categoria="m",
            universo="mototaxi", activo=True,
        ))
        info = await adapter.obtener_precio_vigente("REP-001")
        assert info.precio_venta == Decimal("45")

    async def test_obtener_precio_inexistente_falla(self):
        adapter = InMemoryCatalogoAdapter()
        with pytest.raises(DomainError):
            await adapter.obtener_precio_vigente("NINGUNO")

    async def test_verificar_existencia(self):
        adapter = InMemoryCatalogoAdapter()
        adapter.agregar_repuesto(RepuestoInfo(
            repuesto_id="rp-1", codigo="REP-001",
            precio_venta=Decimal("45"), nombre="F", categoria="m",
            universo="mototaxi", activo=True,
        ))
        assert await adapter.verificar_existencia("REP-001") is True
        assert await adapter.verificar_existencia("NADA") is False


from src.pedidos.domain.models.pedido import EstadoReserva


class TestInMemoryStockAdapter:
    async def test_consultar_disponibilidad(self):
        adapter = InMemoryStockAdapter()
        adapter.establecer_stock("rp-1", 10)
        r = await adapter.consultar_disponibilidad("rp-1")
        assert r.cantidad_disponible == 10

    async def test_consultar_cero_si_no_existe(self):
        adapter = InMemoryStockAdapter()
        r = await adapter.consultar_disponibilidad("rp-99")
        assert r.cantidad_disponible == 0

    async def test_apartar_stock(self):
        adapter = InMemoryStockAdapter()
        adapter.establecer_stock("rp-1", 10)
        ok = await adapter.apartar_stock("rp-1", 3, "u", "ref")
        assert ok is True
        r = await adapter.consultar_disponibilidad("rp-1")
        assert r.cantidad_disponible == 7

    async def test_apartar_insuficiente(self):
        adapter = InMemoryStockAdapter()
        adapter.establecer_stock("rp-1", 2)
        ok = await adapter.apartar_stock("rp-1", 5, "u", "ref")
        assert ok is False

    async def test_liberar_stock(self):
        adapter = InMemoryStockAdapter()
        adapter.establecer_stock("rp-1", 10)
        await adapter.apartar_stock("rp-1", 5, "u", "ref")
        ok = await adapter.liberar_stock("rp-1", 3, "u", "ref")
        assert ok is True

    async def test_liberar_mas_de_apartado_falla(self):
        adapter = InMemoryStockAdapter()
        adapter.establecer_stock("rp-1", 10)
        await adapter.apartar_stock("rp-1", 2, "u", "ref")
        ok = await adapter.liberar_stock("rp-1", 10, "u", "ref")
        assert ok is False

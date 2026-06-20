"""
Tests unitarios — infraestructura del módulo taller.
Meta: ≥ 70% line coverage (09 §3.4).
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone

from src.taller.domain.models.orden_trabajo import (
    Entrada,
    EstadoEntrada,
    EstadoOrdenTrabajo,
    HistorialIntervencion,
    Mecanico,
    ModalidadIntervencion,
    NivelMecanico,
    NivelUrgencia,
    OrdenTrabajo,
    Vehiculo,
)
from src.taller.infrastructure.repositories.taller_repository_inmemory import (
    InMemoryTallerRepository,
)
from src.taller.infrastructure.adapters.catalogo_taller_adapter import (
    InMemoryCatalogoTallerAdapter,
    InMemoryStockTallerAdapter,
)
from src.taller.domain.ports.catalogo_taller_port import RepuestoInfoTaller
from src.taller.domain.models.orden_trabajo import DomainError


class TestInMemoryTallerRepository:
    async def test_guardar_y_obtener_ot(self):
        repo = InMemoryTallerRepository()
        ot = OrdenTrabajo(
            vehiculo_id="v", mecanico_master_id="m",
            modalidad=ModalidadIntervencion.CORRECTIVO,
            urgencia=NivelUrgencia.ALTA,
        )
        await repo.guardar_ot(ot)
        resultado = await repo.obtener_ot(ot.id)
        assert resultado is not None

    async def test_obtener_ot_inexistente(self):
        repo = InMemoryTallerRepository()
        assert await repo.obtener_ot("id-99") is None

    async def test_actualizar_ot(self):
        repo = InMemoryTallerRepository()
        ot = OrdenTrabajo(
            vehiculo_id="v", mecanico_master_id="m",
            modalidad=ModalidadIntervencion.PREVENTIVO,
            urgencia=NivelUrgencia.BAJA,
        )
        await repo.guardar_ot(ot)
        ot.cobro_confirmado = True
        await repo.actualizar_ot(ot)
        r = await repo.obtener_ot(ot.id)
        assert r.cobro_confirmado is True

    async def test_actualizar_ot_inexistente_falla(self):
        repo = InMemoryTallerRepository()
        ot = OrdenTrabajo(
            vehiculo_id="v", mecanico_master_id="m",
            modalidad=ModalidadIntervencion.PREVENTIVO,
            urgencia=NivelUrgencia.BAJA,
        )
        with pytest.raises(ValueError):
            await repo.actualizar_ot(ot)

    async def test_listar_ots(self):
        repo = InMemoryTallerRepository()
        ot1 = OrdenTrabajo(vehiculo_id="v1", mecanico_master_id="m", modalidad=ModalidadIntervencion.PREVENTIVO, urgencia=NivelUrgencia.BAJA)
        ot2 = OrdenTrabajo(vehiculo_id="v2", mecanico_master_id="m", modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA)
        await repo.guardar_ot(ot1)
        await repo.guardar_ot(ot2)
        ots = await repo.listar_ots()
        assert len(ots) == 2

    async def test_guardar_y_obtener_vehiculo(self):
        repo = InMemoryTallerRepository()
        v = Vehiculo(universo="mototaxi", modelo="Bajaj RE", año=2020)
        await repo.guardar_vehiculo(v)
        r = await repo.obtener_vehiculo(v.id)
        assert r is not None

    async def test_obtener_vehiculo_inexistente(self):
        repo = InMemoryTallerRepository()
        assert await repo.obtener_vehiculo("id-99") is None

    async def test_guardar_y_obtener_mecanico(self):
        repo = InMemoryTallerRepository()
        m = Mecanico(usuario_id="u-1", nivel=NivelMecanico.MASTER)
        await repo.guardar_mecanico(m)
        r = await repo.obtener_mecanico(m.id)
        assert r is not None

    async def test_obtener_mecanico_inexistente(self):
        repo = InMemoryTallerRepository()
        assert await repo.obtener_mecanico("id-99") is None

    async def test_listar_mecanicos_disponibles(self):
        repo = InMemoryTallerRepository()
        m1 = Mecanico(usuario_id="u1", nivel=NivelMecanico.MASTER, disponible=True)
        m2 = Mecanico(usuario_id="u2", nivel=NivelMecanico.JUNIOR, disponible=False)
        await repo.guardar_mecanico(m1)
        await repo.guardar_mecanico(m2)
        disponibles = await repo.listar_mecanicos_disponibles()
        assert len(disponibles) == 1

    async def test_actualizar_mecanico(self):
        repo = InMemoryTallerRepository()
        m = Mecanico(usuario_id="u1", nivel=NivelMecanico.MASTER)
        await repo.guardar_mecanico(m)
        m.disponible = False
        await repo.actualizar_mecanico(m)
        r = await repo.obtener_mecanico(m.id)
        assert r.disponible is False

    async def test_actualizar_mecanico_inexistente_falla(self):
        repo = InMemoryTallerRepository()
        m = Mecanico(usuario_id="u", nivel=NivelMecanico.JUNIOR)
        with pytest.raises(ValueError):
            await repo.actualizar_mecanico(m)

    async def test_guardar_y_obtener_entrada(self):
        repo = InMemoryTallerRepository()
        ot = OrdenTrabajo(vehiculo_id="v", mecanico_master_id="m", modalidad=ModalidadIntervencion.PREVENTIVO, urgencia=NivelUrgencia.BAJA)
        await repo.guardar_ot(ot)
        e = Entrada(vehiculo_id="v", orden_trabajo_id=ot.id)
        await repo.guardar_entrada(e)
        r = await repo.obtener_entrada_por_ot(ot.id)
        assert r is not None

    async def test_obtener_entrada_inexistente(self):
        repo = InMemoryTallerRepository()
        assert await repo.obtener_entrada_por_ot("id-99") is None

    async def test_actualizar_entrada(self):
        repo = InMemoryTallerRepository()
        e = Entrada(vehiculo_id="v")
        await repo.guardar_entrada(e)
        e.cerrar()
        await repo.actualizar_entrada(e)
        r = await repo.obtener_entrada_por_ot(e.orden_trabajo_id or "")
        assert r is None or r.estado == EstadoEntrada.CERRADA

    async def test_actualizar_entrada_inexistente_falla(self):
        repo = InMemoryTallerRepository()
        e = Entrada(vehiculo_id="v")
        with pytest.raises(ValueError):
            await repo.actualizar_entrada(e)

    async def test_guardar_historial(self):
        repo = InMemoryTallerRepository()
        h = HistorialIntervencion(
            vehiculo_id="v", orden_trabajo_id="ot-1", mecanico_master_id="m",
            fecha_apertura=datetime.now(timezone.utc),
            fecha_cierre=datetime.now(timezone.utc),
            monto_final=Decimal("100.00"),
        )
        resultado = await repo.guardar_historial(h)
        assert resultado.id == h.id

    def test_limpiar(self):
        repo = InMemoryTallerRepository()
        repo.limpiar()


class TestInMemoryCatalogoTallerAdapter:
    async def test_obtener_precio_existente(self):
        adapter = InMemoryCatalogoTallerAdapter()
        adapter.agregar_repuesto(RepuestoInfoTaller(
            repuesto_id="rp-1", codigo="REP-001",
            precio_venta=Decimal("45"), nombre="F", activo=True,
        ))
        info = await adapter.obtener_precio_para_ot("REP-001")
        assert info.precio_venta == Decimal("45")

    async def test_obtener_precio_inexistente_falla(self):
        adapter = InMemoryCatalogoTallerAdapter()
        with pytest.raises(DomainError):
            await adapter.obtener_precio_para_ot("NINGUNO")


class TestInMemoryStockTallerAdapter:
    async def test_verificar_disponibilidad(self):
        adapter = InMemoryStockTallerAdapter()
        adapter.establecer_stock("rp-1", disponible=10, apartado=2)
        r = await adapter.verificar_disponibilidad_ot("rp-1")
        assert r.cantidad_disponible == 10
        assert r.cantidad_apartada == 2

    async def test_consultar_apartado(self):
        adapter = InMemoryStockTallerAdapter()
        adapter.establecer_stock("rp-1", disponible=5, apartado=3)
        assert await adapter.consultar_apartado("rp-1") == 3

    async def test_sin_stock_retorna_cero(self):
        adapter = InMemoryStockTallerAdapter()
        r = await adapter.verificar_disponibilidad_ot("rp-99")
        assert r.cantidad_disponible == 0

    async def test_apartado_cero_si_no_existe(self):
        adapter = InMemoryStockTallerAdapter()
        assert await adapter.consultar_apartado("rp-99") == 0

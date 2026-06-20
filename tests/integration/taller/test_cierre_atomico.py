"""
Test específico del criterio 09 §3.4 — Descuento stock al cierre.
Verifica: stock descontado exactamente al cerrar OT (atomicidad).
"""
import pytest
from decimal import Decimal

from src.taller.application.use_cases.gestionar_ot import (
    AbrirOrdenTrabajoCommand,
    AbrirOrdenTrabajoUseCase,
    AgregarRepuestoCommand,
    AgregarRepuestoUseCase,
    AprobarListaCommand,
    AprobarListaUseCase,
    CerrarOTCommand,
    CerrarOrdenTrabajoUseCase,
    CobroParcialCommand,
    CobroParcialUseCase,
    RevisionFinalCommand,
    RevisionFinalUseCase,
)
from src.taller.domain.models.orden_trabajo import (
    CobroNoConfirmadoError,
    ListaNoConfirmadaError,
    ModalidadIntervencion,
    NivelUrgencia,
)
from src.taller.infrastructure.repositories.taller_repository_inmemory import (
    InMemoryTallerRepository,
)
from src.taller.infrastructure.adapters.catalogo_taller_adapter import (
    InMemoryCatalogoTallerAdapter,
)
from src.taller.domain.models.orden_trabajo import Mecanico, NivelMecanico, Vehiculo
from src.taller.domain.ports.catalogo_taller_port import RepuestoInfoTaller
from src.shared.events.event_bus import InMemoryEventBus


@pytest.fixture
async def setup_taller():
    repo = InMemoryTallerRepository()
    catalogo = InMemoryCatalogoTallerAdapter()
    bus = InMemoryEventBus()

    v = Vehiculo(universo="mototaxi", modelo="Bajaj RE", año=2020)
    m = Mecanico(usuario_id="u-1", nivel=NivelMecanico.MASTER)
    await repo.guardar_vehiculo(v)
    await repo.guardar_mecanico(m)

    catalogo.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-001", codigo="REP-001",
        precio_venta=Decimal("25.00"), nombre="Bujía", activo=True,
    ))
    catalogo.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-002", codigo="REP-002",
        precio_venta=Decimal("40.00"), nombre="Filtro", activo=True,
    ))

    return repo, catalogo, bus, v.id, m.id


async def _flujo_hasta_revision(repo, catalogo, bus, vehiculo_id, mecanico_id, codigos=None):
    """Flujo completo hasta REVISION_FINAL."""
    abrir = AbrirOrdenTrabajoUseCase(repo, bus)
    ot = await abrir.execute(AbrirOrdenTrabajoCommand(
        vehiculo_id=vehiculo_id, mecanico_master_id=mecanico_id,
        modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
        actor_id=mecanico_id,
    ))
    agregar = AgregarRepuestoUseCase(repo, catalogo, bus)
    for codigo in (codigos or ["REP-001"]):
        await agregar.execute(AgregarRepuestoCommand(ot_id=ot.id, codigo=codigo, cantidad=1, actor_id=mecanico_id))

    aprobar = AprobarListaUseCase(repo, bus)
    await aprobar.execute(AprobarListaCommand(ot_id=ot.id, actor_id=mecanico_id))

    revision = RevisionFinalUseCase(repo, bus)
    await revision.execute(RevisionFinalCommand(
        ot_id=ot.id, costo_mano_obra=Decimal("80.00"), actor_id=mecanico_id,
    ))
    return ot.id


class TestCierreAtomico:
    """
    Verifica que el cierre de OT publica el evento orden_trabajo.cerrada
    con la lista exacta de repuestos consumidos (09 §3.4).
    """

    async def test_cierre_publica_evento_con_repuestos(self, setup_taller):
        repo, catalogo, bus, vid, mid = setup_taller
        ot_id = await _flujo_hasta_revision(repo, catalogo, bus, vid, mid)

        cobro = CobroParcialUseCase(repo)
        await cobro.execute(CobroParcialCommand(
            ot_id=ot_id, monto_pagado=Decimal("105.00"), plazo_dias=1, actor_id=mid,
        ))

        cerrar = CerrarOrdenTrabajoUseCase(repo, bus)
        ot = await cerrar.execute(CerrarOTCommand(ot_id=ot_id, actor_id=mid))

        assert ot.estado.value == "CERRADA"
        assert bus.fue_publicado("orden_trabajo.cerrada")

        evento = next(e for e in bus.get_published() if e.tipo == "orden_trabajo.cerrada")
        payload = evento.payload
        assert "repuestos_consumidos" in payload
        assert len(payload["repuestos_consumidos"]) == 1
        assert payload["repuestos_consumidos"][0]["repuesto_id"] == "rp-001"

    async def test_cierre_sin_cobro_bloqueado(self, setup_taller):
        repo, catalogo, bus, vid, mid = setup_taller
        ot_id = await _flujo_hasta_revision(repo, catalogo, bus, vid, mid)

        cerrar = CerrarOrdenTrabajoUseCase(repo, bus)
        with pytest.raises(CobroNoConfirmadoError):
            await cerrar.execute(CerrarOTCommand(ot_id=ot_id, actor_id=mid))

        assert not bus.fue_publicado("orden_trabajo.cerrada")

    async def test_cierre_con_multiples_repuestos(self, setup_taller):
        repo, catalogo, bus, vid, mid = setup_taller
        ot_id = await _flujo_hasta_revision(
            repo, catalogo, bus, vid, mid, codigos=["REP-001", "REP-002"]
        )

        cobro = CobroParcialUseCase(repo)
        await cobro.execute(CobroParcialCommand(
            ot_id=ot_id, monto_pagado=Decimal("145.00"), plazo_dias=1, actor_id=mid,
        ))

        cerrar = CerrarOrdenTrabajoUseCase(repo, bus)
        ot = await cerrar.execute(CerrarOTCommand(ot_id=ot_id, actor_id=mid))

        evento = next(e for e in bus.get_published() if e.tipo == "orden_trabajo.cerrada")
        assert len(evento.payload["repuestos_consumidos"]) == 2

    async def test_historial_registrado_al_cerrar(self, setup_taller):
        repo, catalogo, bus, vid, mid = setup_taller
        ot_id = await _flujo_hasta_revision(repo, catalogo, bus, vid, mid)

        cobro = CobroParcialUseCase(repo)
        await cobro.execute(CobroParcialCommand(
            ot_id=ot_id, monto_pagado=Decimal("105.00"), plazo_dias=1, actor_id=mid,
        ))

        cerrar = CerrarOrdenTrabajoUseCase(repo, bus)
        await cerrar.execute(CerrarOTCommand(ot_id=ot_id, actor_id=mid))

        assert len(repo._historial) == 1

    async def test_cierre_sin_consumo_registrado_bloqueado(self, setup_taller):
        """OT no cierra si el servicio verifica que no hay consumo."""
        repo, catalogo, bus, vid, mid = setup_taller

        abrir = AbrirOrdenTrabajoUseCase(repo, bus)
        ot = await abrir.execute(AbrirOrdenTrabajoCommand(
            vehiculo_id=vid, mecanico_master_id=mid,
            modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
            actor_id=mid,
        ))
        ot.cobro_confirmado = True
        ot.cliente_aprobo_lista = True
        await repo.actualizar_ot(ot)

        cerrar = CerrarOrdenTrabajoUseCase(repo, bus)
        with pytest.raises(ListaNoConfirmadaError):
            await cerrar.execute(CerrarOTCommand(ot_id=ot.id, actor_id=mid))

    async def test_repuesto_adicional_tacito_incluido_en_cierre(self, setup_taller):
        """
        Ítem tácito aprobado es incluido en repuestos_consumidos al cerrar.
        """
        from datetime import datetime, timedelta, timezone
        repo, catalogo, bus, vid, mid = setup_taller

        catalogo.agregar_repuesto(RepuestoInfoTaller(
            repuesto_id="rp-medio", codigo="REP-MEDIO",
            precio_venta=Decimal("65.00"), nombre="Rodamiento", activo=True,
        ))

        abrir = AbrirOrdenTrabajoUseCase(repo, bus)
        ot = await abrir.execute(AbrirOrdenTrabajoCommand(
            vehiculo_id=vid, mecanico_master_id=mid,
            modalidad=ModalidadIntervencion.PREVENTIVO, urgencia=NivelUrgencia.BAJA,
            actor_id=mid,
        ))
        agregar = AgregarRepuestoUseCase(repo, catalogo, bus)
        await agregar.execute(AgregarRepuestoCommand(ot_id=ot.id, codigo="REP-001", cantidad=1, actor_id=mid))
        aprobar = AprobarListaUseCase(repo, bus)
        await aprobar.execute(AprobarListaCommand(ot_id=ot.id, actor_id=mid))

        await agregar.execute(AgregarRepuestoCommand(ot_id=ot.id, codigo="REP-MEDIO", cantidad=1, actor_id=mid))

        ot_actual = await repo.obtener_ot(ot.id)
        item_tacito = next(i for i in ot_actual.lista_repuestos if i.codigo == "REP-MEDIO")
        item_tacito.espera_hasta = datetime.now(timezone.utc) - timedelta(seconds=1)
        await repo.actualizar_ot(ot_actual)

        from src.taller.application.use_cases.gestionar_ot import AplicarAprobacionesTacitasUseCase
        aplicar = AplicarAprobacionesTacitasUseCase(repo)
        await aplicar.execute(ot.id)

        revision = RevisionFinalUseCase(repo, bus)
        await revision.execute(RevisionFinalCommand(ot_id=ot.id, costo_mano_obra=Decimal("50.00"), actor_id=mid))

        cobro = CobroParcialUseCase(repo)
        await cobro.execute(CobroParcialCommand(
            ot_id=ot.id, monto_pagado=Decimal("140.00"), plazo_dias=1, actor_id=mid,
        ))

        cerrar = CerrarOrdenTrabajoUseCase(repo, bus)
        await cerrar.execute(CerrarOTCommand(ot_id=ot.id, actor_id=mid))

        evento = next(e for e in bus.get_published() if e.tipo == "orden_trabajo.cerrada")
        repuesto_ids = [r["repuesto_id"] for r in evento.payload["repuestos_consumidos"]]
        assert "rp-001" in repuesto_ids
        assert "rp-medio" in repuesto_ids

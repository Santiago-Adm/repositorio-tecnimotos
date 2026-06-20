"""
Test específico del criterio 09 §3.2 — Reserva con TTL.
Verifica: TTL por segmento respetado.
"""
import pytest
from datetime import timedelta

from src.pedidos.domain.models.pedido import (
    DomainError,
    EstadoReserva,
    Reserva,
    SegmentoCliente,
    TransicionEstadoInvalidaError,
    ttl_para_segmento,
)
from src.pedidos.application.use_cases.gestionar_reserva import (
    CrearReservaCommand,
    CrearReservaUseCase,
)


class TestReservaTTL:
    """Verifica que el TTL es diferenciado por segmento (02 §2.2)."""

    def test_conductor_ttl_1_dia(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        assert (r.expira_en - r.created_at) == timedelta(days=1)

    def test_flota_dueno_ttl_1_dia(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.FLOTA_DUENO)
        assert (r.expira_en - r.created_at) == timedelta(days=1)

    def test_flota_conductor_ttl_1_dia(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.FLOTA_CONDUCTOR)
        assert (r.expira_en - r.created_at) == timedelta(days=1)

    def test_distrito_ttl_3_dias(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.DISTRITO)
        assert (r.expira_en - r.created_at) == timedelta(days=3)

    def test_rural_ttl_3_dias(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.RURAL)
        assert (r.expira_en - r.created_at) == timedelta(days=3)

    def test_motolineal_ttl_2_dias(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.MOTOLINEAL)
        assert (r.expira_en - r.created_at) == timedelta(days=2)

    def test_presencial_es_menor_que_remoto(self):
        presencial = ttl_para_segmento(SegmentoCliente.CONDUCTOR)
        remoto = ttl_para_segmento(SegmentoCliente.DISTRITO)
        assert presencial < remoto

    def test_reserva_vigente_al_crear(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        assert r.esta_vigente() is True

    def test_reserva_no_vigente_tras_expirar(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        r.expirar()
        assert r.esta_vigente() is False

    def test_no_liberar_reserva_ya_expirada(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        r.expirar()
        with pytest.raises(TransicionEstadoInvalidaError):
            r.liberar()

    def test_confirmada_sigue_vigente(self):
        r = Reserva(cliente_id="c", repuesto_id="r", cantidad=1, segmento=SegmentoCliente.CONDUCTOR)
        r.confirmar()
        assert r.esta_vigente() is True

    async def test_crear_reserva_publica_expira_en_correcto(self, repo, stock, event_bus):
        from src.pedidos.application.use_cases.gestionar_reserva import CrearReservaCommand, CrearReservaUseCase
        stock.establecer_stock("rp-001", 10)
        uc = CrearReservaUseCase(repo, stock, event_bus)
        reserva = await uc.execute(CrearReservaCommand(
            cliente_id="cli-1",
            repuesto_id="rp-001",
            cantidad=3,
            segmento=SegmentoCliente.DISTRITO,
            actor_id="cli-1",
        ))
        delta = reserva.expira_en - reserva.created_at
        assert delta == timedelta(days=3)
        # El evento publicado contiene expira_en
        assert event_bus.fue_publicado("reserva.creada")
        evento = next(e for e in event_bus.get_published() if e.tipo == "reserva.creada")
        assert "expira_en" in evento.payload

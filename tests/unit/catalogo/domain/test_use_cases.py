"""
Tests unitarios — casos de uso del módulo catalogo.
Usan InMemoryRepuestoRepository (Fake) e InMemoryEventBus.
"""
import pytest
from decimal import Decimal

from src.catalogo.application.use_cases.actualizar_precio import (
    ActualizarPrecioCommand,
    ActualizarPrecioVentaUseCase,
)
from src.catalogo.application.use_cases.buscar_repuestos import (
    BuscarRepuestosQuery,
    BuscarRepuestosUseCase,
    ObtenerRepuestoPorCodigoQuery,
    ObtenerRepuestoPorCodigoUseCase,
)
from src.catalogo.application.use_cases.consultar_precio import (
    ConsultarPrecioQuery,
    ConsultarPrecioUseCase,
)
from src.catalogo.application.use_cases.crear_repuesto import (
    CrearRepuestoCommand,
    CrearRepuestoUseCase,
)
from src.catalogo.application.use_cases.dar_de_baja_repuesto import (
    DarDeBajaRepuestoCommand,
    DarDeBajaRepuestoUseCase,
)
from src.catalogo.application.use_cases.obtener_historial_precio import (
    ObtenerHistorialPrecioQuery,
    ObtenerHistorialPrecioUseCase,
)
from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    DomainError,
    RepuestoDadoDeBajaError,
    RepuestoNoEncontradoError,
    UniversoRepuesto,
)


class TestCrearRepuesto:
    @pytest.mark.asyncio
    async def test_crea_repuesto_y_publica_evento(self, repo, event_bus):
        uc = CrearRepuestoUseCase(repo, event_bus)
        repuesto = await uc.execute(
            CrearRepuestoCommand(
                codigo="REP-001",
                nombre="Filtro",
                universo=UniversoRepuesto.MOTOTAXI,
                modelo="Bajaj RE",
                año=2019,
                categoria=CategoriaRepuesto.MOTOR,
                precio_venta=Decimal("45.00"),
            )
        )
        assert repuesto.codigo == "REP-001"
        assert event_bus.fue_publicado("repuesto.creado")
        assert event_bus.conteo_publicaciones("repuesto.creado") == 1

    @pytest.mark.asyncio
    async def test_evento_tiene_payload_correcto(self, repo, event_bus):
        uc = CrearRepuestoUseCase(repo, event_bus)
        await uc.execute(
            CrearRepuestoCommand(
                codigo="REP-002",
                nombre="Cadena",
                universo=UniversoRepuesto.MOTOTAXI,
                modelo="Bajaj RE",
                año=2020,
                categoria=CategoriaRepuesto.TRANSMISION,
                precio_venta=Decimal("30.00"),
            )
        )
        eventos = event_bus.get_published()
        assert len(eventos) == 1
        payload = eventos[0].payload
        assert payload["codigo"] == "REP-002"
        assert payload["universo"] == "mototaxi"


class TestBuscarRepuestos:
    @pytest.mark.asyncio
    async def test_busca_por_universo_y_modelo(self, repo, event_bus, repuesto_mototaxi, repuesto_motolineal):
        await repo.guardar(repuesto_mototaxi)
        await repo.guardar(repuesto_motolineal)

        uc = BuscarRepuestosUseCase(repo)
        result = await uc.execute(
            BuscarRepuestosQuery(universo=UniversoRepuesto.MOTOTAXI)
        )
        assert result.total == 1
        assert result.repuestos[0].codigo == "REP-001"

    @pytest.mark.asyncio
    async def test_no_mezcla_universos_rnn05(
        self, repo, repuesto_mototaxi, repuesto_motolineal
    ):
        """RNN-05: catálogos de mototaxi y motolineal son estructuralmente separados."""
        await repo.guardar(repuesto_mototaxi)
        await repo.guardar(repuesto_motolineal)

        uc = BuscarRepuestosUseCase(repo)
        result = await uc.execute(
            BuscarRepuestosQuery(universo=UniversoRepuesto.MOTOLINEAL)
        )
        codigos = [r.codigo for r in result.repuestos]
        assert "REP-001" not in codigos
        assert "REP-100" in codigos

    @pytest.mark.asyncio
    async def test_no_muestra_repuestos_dados_de_baja(self, repo, repuesto_mototaxi):
        repuesto_mototaxi.dar_de_baja("test")
        await repo.guardar(repuesto_mototaxi)

        uc = BuscarRepuestosUseCase(repo)
        result = await uc.execute(
            BuscarRepuestosQuery(universo=UniversoRepuesto.MOTOTAXI)
        )
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_busca_por_modelo_y_año(self, repo, repuesto_mototaxi):
        await repo.guardar(repuesto_mototaxi)

        uc = BuscarRepuestosUseCase(repo)
        result = await uc.execute(
            BuscarRepuestosQuery(
                universo=UniversoRepuesto.MOTOTAXI,
                modelo="Bajaj RE",
                año=2019,
            )
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_busca_año_incorrecto_retorna_vacio(self, repo, repuesto_mototaxi):
        await repo.guardar(repuesto_mototaxi)

        uc = BuscarRepuestosUseCase(repo)
        result = await uc.execute(
            BuscarRepuestosQuery(
                universo=UniversoRepuesto.MOTOTAXI,
                año=2025,
            )
        )
        assert result.total == 0


class TestObtenerPorCodigo:
    @pytest.mark.asyncio
    async def test_obtiene_por_codigo_existente(self, repo, repuesto_mototaxi):
        await repo.guardar(repuesto_mototaxi)
        uc = ObtenerRepuestoPorCodigoUseCase(repo)
        result = await uc.execute(ObtenerRepuestoPorCodigoQuery(codigo="REP-001"))
        assert result is not None
        assert result.codigo == "REP-001"

    @pytest.mark.asyncio
    async def test_codigo_inexistente_retorna_none(self, repo):
        uc = ObtenerRepuestoPorCodigoUseCase(repo)
        result = await uc.execute(ObtenerRepuestoPorCodigoQuery(codigo="REP-999"))
        assert result is None


class TestActualizarPrecio:
    @pytest.mark.asyncio
    async def test_actualiza_precio_y_publica_evento(
        self, repo, event_bus, repuesto_mototaxi
    ):
        await repo.guardar(repuesto_mototaxi)
        uc = ActualizarPrecioVentaUseCase(repo, event_bus)
        result = await uc.execute(
            ActualizarPrecioCommand(
                codigo="REP-001",
                precio_venta=Decimal("52.00"),
                modificado_por="admin-001",
            )
        )
        assert result.repuesto.precio_venta == Decimal("52.00")
        assert event_bus.fue_publicado("repuesto.precio_actualizado")

    @pytest.mark.asyncio
    async def test_codigo_inexistente_lanza_error(self, repo, event_bus):
        uc = ActualizarPrecioVentaUseCase(repo, event_bus)
        with pytest.raises(RepuestoNoEncontradoError):
            await uc.execute(
                ActualizarPrecioCommand(
                    codigo="REP-999",
                    precio_venta=Decimal("50.00"),
                    modificado_por="admin-001",
                )
            )

    @pytest.mark.asyncio
    async def test_dado_de_baja_lanza_error(
        self, repo, event_bus, repuesto_mototaxi
    ):
        repuesto_mototaxi.dar_de_baja("test")
        await repo.guardar(repuesto_mototaxi)
        uc = ActualizarPrecioVentaUseCase(repo, event_bus)
        with pytest.raises(RepuestoDadoDeBajaError):
            await uc.execute(
                ActualizarPrecioCommand(
                    codigo="REP-001",
                    precio_venta=Decimal("50.00"),
                    modificado_por="admin-001",
                )
            )

    @pytest.mark.asyncio
    async def test_evento_precio_actualizado_tiene_payload_correcto(
        self, repo, event_bus, repuesto_mototaxi
    ):
        """HU-INT-01 Escenario 1: evento publicado con payload completo."""
        await repo.guardar(repuesto_mototaxi)
        uc = ActualizarPrecioVentaUseCase(repo, event_bus)
        await uc.execute(
            ActualizarPrecioCommand(
                codigo="REP-001",
                precio_venta=Decimal("52.00"),
                modificado_por="admin-001",
            )
        )
        eventos = event_bus.get_published()
        payload = eventos[0].payload
        assert payload["precio_anterior"] == "45.00"
        assert payload["precio_nuevo"] == "52.00"
        assert "timestamp" in payload


class TestDarDeBaja:
    @pytest.mark.asyncio
    async def test_da_de_baja_y_publica_evento(
        self, repo, event_bus, repuesto_mototaxi
    ):
        await repo.guardar(repuesto_mototaxi)
        uc = DarDeBajaRepuestoUseCase(repo, event_bus)
        repuesto = await uc.execute(
            DarDeBajaRepuestoCommand(
                codigo="REP-001",
                motivo="Descontinuado",
                dado_de_baja_por="admin-001",
            )
        )
        assert repuesto.activo is False
        assert event_bus.fue_publicado("repuesto.dado_de_baja")

    @pytest.mark.asyncio
    async def test_codigo_inexistente_lanza_error(self, repo, event_bus):
        uc = DarDeBajaRepuestoUseCase(repo, event_bus)
        with pytest.raises(RepuestoNoEncontradoError):
            await uc.execute(
                DarDeBajaRepuestoCommand(
                    codigo="REP-999",
                    motivo="test",
                    dado_de_baja_por="admin-001",
                )
            )

    @pytest.mark.asyncio
    async def test_ya_dado_de_baja_lanza_error(
        self, repo, event_bus, repuesto_mototaxi
    ):
        repuesto_mototaxi.dar_de_baja("test")
        await repo.guardar(repuesto_mototaxi)
        uc = DarDeBajaRepuestoUseCase(repo, event_bus)
        with pytest.raises(DomainError):
            await uc.execute(
                DarDeBajaRepuestoCommand(
                    codigo="REP-001",
                    motivo="test2",
                    dado_de_baja_por="admin-001",
                )
            )


class TestConsultarPrecio:
    @pytest.mark.asyncio
    async def test_precio_visible_nivel_1(self, repo, repuesto_mototaxi):
        await repo.guardar(repuesto_mototaxi)
        uc = ConsultarPrecioUseCase(repo)
        result = await uc.execute(
            ConsultarPrecioQuery(
                codigo="REP-001",
                es_cliente=True,
                consultas_realizadas=0,
                nivel_visibilidad=1,
            )
        )
        assert result.precio_visible is True
        assert result.precio_venta == Decimal("45.00")

    @pytest.mark.asyncio
    async def test_precio_no_visible_visitante(self, repo, repuesto_mototaxi):
        """HU-S1-05 Escenario 2: visitante sin cuenta no ve precio."""
        await repo.guardar(repuesto_mototaxi)
        uc = ConsultarPrecioUseCase(repo)
        result = await uc.execute(
            ConsultarPrecioQuery(
                codigo="REP-001",
                es_cliente=False,
                consultas_realizadas=0,
                nivel_visibilidad=0,
            )
        )
        assert result.precio_visible is False
        assert result.precio_venta is None

    @pytest.mark.asyncio
    async def test_limite_consultas_alcanzado(self, repo, repuesto_mototaxi):
        """HU-S1-05 Escenario 4: límite de 3 consultas por sesión."""
        await repo.guardar(repuesto_mototaxi)
        uc = ConsultarPrecioUseCase(repo)
        result = await uc.execute(
            ConsultarPrecioQuery(
                codigo="REP-001",
                es_cliente=True,
                consultas_realizadas=3,
                max_consultas=3,
                nivel_visibilidad=1,
            )
        )
        assert result.precio_visible is False
        assert result.precio_limite_alcanzado is True
        assert result.mensaje is not None

    @pytest.mark.asyncio
    async def test_nivel_2_siempre_visible(self, repo, repuesto_mototaxi):
        await repo.guardar(repuesto_mototaxi)
        uc = ConsultarPrecioUseCase(repo)
        result = await uc.execute(
            ConsultarPrecioQuery(
                codigo="REP-001",
                es_cliente=True,
                consultas_realizadas=10,
                nivel_visibilidad=2,
            )
        )
        assert result.precio_visible is True

    @pytest.mark.asyncio
    async def test_codigo_inexistente_lanza_error(self, repo):
        uc = ConsultarPrecioUseCase(repo)
        with pytest.raises(RepuestoNoEncontradoError):
            await uc.execute(
                ConsultarPrecioQuery(
                    codigo="REP-999",
                    es_cliente=True,
                    consultas_realizadas=0,
                )
            )


class TestHistorialPrecio:
    @pytest.mark.asyncio
    async def test_historial_registra_cambios(
        self, repo, event_bus, repuesto_mototaxi
    ):
        await repo.guardar(repuesto_mototaxi)
        uc_actualizar = ActualizarPrecioVentaUseCase(repo, event_bus)
        await uc_actualizar.execute(
            ActualizarPrecioCommand(
                codigo="REP-001",
                precio_venta=Decimal("52.00"),
                modificado_por="admin-001",
            )
        )

        uc_hist = ObtenerHistorialPrecioUseCase(repo)
        historial = await uc_hist.execute(
            ObtenerHistorialPrecioQuery(codigo="REP-001")
        )
        assert len(historial) == 1
        assert historial[0].precio_anterior == Decimal("45.00")
        assert historial[0].precio_nuevo == Decimal("52.00")

    @pytest.mark.asyncio
    async def test_historial_codigo_inexistente_lanza_error(self, repo):
        uc = ObtenerHistorialPrecioUseCase(repo)
        with pytest.raises(RepuestoNoEncontradoError):
            await uc.execute(ObtenerHistorialPrecioQuery(codigo="REP-999"))

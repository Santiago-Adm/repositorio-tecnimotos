"""Fixtures compartidos para tests de integración del módulo taller."""
import pytest
from decimal import Decimal

from src.taller.domain.models.orden_trabajo import Mecanico, NivelMecanico, Vehiculo
from src.taller.domain.ports.catalogo_taller_port import RepuestoInfoTaller


@pytest.fixture
async def taller_client(app_client):
    """Cliente con vehículo y mecánico precargados."""
    repo = app_client.app.state.taller_repo
    catalogo = app_client.app.state.catalogo_taller_adapter

    v = Vehiculo(universo="mototaxi", modelo="Bajaj RE", año=2021)
    await repo.guardar_vehiculo(v)
    m = Mecanico(usuario_id="u-master", nivel=NivelMecanico.MASTER)
    await repo.guardar_mecanico(m)

    catalogo.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-001", codigo="REP-001",
        precio_venta=Decimal("25.00"), nombre="Bujía", activo=True,
    ))
    catalogo.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-medio", codigo="REP-MEDIO",
        precio_venta=Decimal("65.00"), nombre="Rodamiento", activo=True,
    ))
    catalogo.agregar_repuesto(RepuestoInfoTaller(
        repuesto_id="rp-caro", codigo="REP-CARO",
        precio_venta=Decimal("150.00"), nombre="Sensor ABS", activo=True,
    ))

    app_client._vehiculo_id = v.id
    app_client._mecanico_id = m.id
    return app_client

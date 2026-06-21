"""
Seed de datos de prueba por nivel y módulo.
Criterio 09 §4.1: seed nivel 1 ejecutable sin errores.

Uso: python scripts/seed.py --level=1 --module=catalogo --env=test
"""
import argparse
import asyncio
import sys
from decimal import Decimal


async def seed_catalogo_nivel1() -> None:
    from src.catalogo.domain.models.repuesto import (
        CategoriaRepuesto,
        Repuesto,
        UniversoRepuesto,
    )
    from src.catalogo.infrastructure.repositories.repuesto_repository_inmemory import (
        InMemoryRepuestoRepository,
    )

    repo = InMemoryRepuestoRepository()
    repuestos = [
        Repuesto(
            codigo="SEED-MT-001",
            nombre="Filtro de aceite Bajaj RE",
            universo=UniversoRepuesto.MOTOTAXI,
            modelo="Bajaj RE",
            año=2019,
            categoria=CategoriaRepuesto.MOTOR,
            precio_venta=Decimal("45.00"),
            descripcion="Filtro original Bajaj",
        ),
        Repuesto(
            codigo="SEED-MT-002",
            nombre="Bujia NGK estándar",
            universo=UniversoRepuesto.MOTOTAXI,
            modelo="Bajaj RE",
            año=2020,
            categoria=CategoriaRepuesto.ELECTRICO,
            precio_venta=Decimal("18.00"),
        ),
        Repuesto(
            codigo="SEED-ML-001",
            nombre="Cadena transmisión TVS",
            universo=UniversoRepuesto.MOTOLINEAL,
            modelo="TVS Apache",
            año=2022,
            categoria=CategoriaRepuesto.TRANSMISION,
            precio_venta=Decimal("85.00"),
        ),
    ]
    for r in repuestos:
        await repo.guardar(r)
    print(f"  catalogo nivel 1: {len(repuestos)} repuestos sembrados (en memoria)")


async def seed_pedidos_nivel1() -> None:
    from src.pedidos.domain.models.pedido import (
        EstadoPedido,
        Pedido,
        PedidoItem,
        SegmentoCliente,
    )
    from src.pedidos.infrastructure.repositories.pedido_repository_inmemory import (
        InMemoryPedidoRepository,
    )

    repo = InMemoryPedidoRepository()
    cliente_s1 = "SEED-CLI-001"
    cliente_s2 = "SEED-CLI-002"

    p1 = Pedido(canal_origen="mostrador", origen_actor="VENDEDOR", cliente_id=cliente_s1)
    p1.agregar_item(PedidoItem(
        pedido_id=p1.id, repuesto_id="SEED-REP-001", codigo="SEED-MT-001",
        cantidad=2, precio_unitario=Decimal("45.00"),
    ))
    await repo.guardar(p1)

    p2 = Pedido(canal_origen="whatsapp", origen_actor="CLIENTE_EXTERNO", cliente_id=cliente_s2)
    p2.agregar_item(PedidoItem(
        pedido_id=p2.id, repuesto_id="SEED-REP-002", codigo="SEED-MT-002",
        cantidad=1, precio_unitario=Decimal("18.00"),
    ))
    p2.confirmar()
    await repo.guardar(p2)

    p3 = Pedido(canal_origen="mostrador", origen_actor="VENDEDOR", cliente_id=cliente_s1)
    p3.agregar_item(PedidoItem(
        pedido_id=p3.id, repuesto_id="SEED-REP-003", codigo="SEED-ML-001",
        cantidad=1, precio_unitario=Decimal("85.00"),
    ))
    p3.cancelar("SIN_STOCK")
    await repo.guardar(p3)

    print(f"  pedidos nivel 1: 3 pedidos sembrados (2 clientes, estados: BORRADOR/CONFIRMADO/CANCELADO) (en memoria)")


async def seed_stock_nivel1() -> None:
    from src.stock.domain.models.stock import (
        Reabastecimiento,
        ReabastecimientoItem,
        StockRepuesto,
    )
    from src.stock.infrastructure.repositories.stock_repository_inmemory import (
        InMemoryStockRepository,
    )

    repo = InMemoryStockRepository()
    entradas = [
        ("SEED-REP-001", "SEED-MT-001", 20, 3),
        ("SEED-REP-002", "SEED-MT-002", 15, 2),
        ("SEED-REP-003", "SEED-ML-001", 8, 1),
        ("SEED-REP-004", "SEED-MT-003", 0, 5),
        ("SEED-REP-005", "SEED-ML-002", 12, 2),
    ]
    for rep_id, codigo, disponible, umbral in entradas:
        sr = StockRepuesto(
            repuesto_id=rep_id, codigo=codigo,
            cantidad_disponible=disponible, umbral_minimo=umbral,
        )
        await repo.guardar(sr)

    reab = Reabastecimiento(proveedor="Bajaj Perú SAC", solicitado_por="SEED-USR-001")
    reab.agregar_item(ReabastecimientoItem(
        repuesto_id="SEED-REP-004", codigo="SEED-MT-003",
        cantidad_solicitada=10, precio_costo_unitario=Decimal("28.00"),
    ))
    await repo.guardar_reabastecimiento(reab)

    print("  stock nivel 1: 5 stock_repuesto sembrados (1 agotado, 1 reabastecimiento pendiente) (en memoria)")


async def seed_taller_nivel1() -> None:
    from src.taller.domain.models.orden_trabajo import (
        EstadoOrdenTrabajo,
        ListaRepuestosOT,
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

    repo = InMemoryTallerRepository()

    mecanico = Mecanico(usuario_id="SEED-USR-MEC-001", nivel=NivelMecanico.MASTER)
    await repo.guardar_mecanico(mecanico)

    vehiculo = Vehiculo(universo="mototaxi", modelo="Bajaj RE", año=2020,
                        cliente_id="SEED-CLI-001", placa="AYA-001")
    await repo.guardar_vehiculo(vehiculo)

    ot1 = OrdenTrabajo(
        vehiculo_id=vehiculo.id, mecanico_master_id=mecanico.id,
        modalidad=ModalidadIntervencion.PREVENTIVO, urgencia=NivelUrgencia.MEDIA,
    )
    ot1.agregar_repuesto_inicial(ListaRepuestosOT(
        orden_trabajo_id=ot1.id, repuesto_id="SEED-REP-001", codigo="SEED-MT-001",
        cantidad=1, precio_unitario=Decimal("45.00"), momento_agregado="inicial",
    ))
    await repo.guardar_ot(ot1)

    vehiculo2 = Vehiculo(universo="motolineal", modelo="TVS Apache", año=2022,
                         cliente_id="SEED-CLI-002")
    await repo.guardar_vehiculo(vehiculo2)

    ot2 = OrdenTrabajo(
        vehiculo_id=vehiculo2.id, mecanico_master_id=mecanico.id,
        modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
    )
    await repo.guardar_ot(ot2)

    print("  taller nivel 1: 1 mecanico, 2 vehiculos, 2 ordenes_trabajo sembrados (estados: ABIERTA) (en memoria)")


async def run_seed(level: int, module: str, env: str) -> None:
    print(f"Seed nivel {level} — módulo {module} — entorno {env}")
    if module == "catalogo" and level == 1:
        await seed_catalogo_nivel1()
    elif module == "pedidos" and level == 1:
        await seed_pedidos_nivel1()
    elif module == "stock" and level == 1:
        await seed_stock_nivel1()
    elif module == "taller" and level == 1:
        await seed_taller_nivel1()
    else:
        print(f"  módulo {module} nivel {level}: aún no implementado")
    print("Seed completado sin errores.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed de datos de prueba")
    parser.add_argument("--level", type=int, required=True, choices=[1, 2])
    parser.add_argument("--module", required=True)
    parser.add_argument("--env", required=True, choices=["test", "staging", "dev"])
    args = parser.parse_args()
    asyncio.run(run_seed(args.level, args.module, args.env))
    return 0


if __name__ == "__main__":
    sys.exit(main())

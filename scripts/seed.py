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
            universo=UniversoRepuesto.MOTOTAXI_3R,
            modelo="Bajaj RE",
            año=2019,
            categoria=CategoriaRepuesto.MOTOR,
            precio_venta=Decimal("45.00"),
            descripcion="Filtro original Bajaj",
        ),
        Repuesto(
            codigo="SEED-MT-002",
            nombre="Bujia NGK estándar",
            universo=UniversoRepuesto.MOTOTAXI_3R,
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

    vehiculo = Vehiculo(universo="mototaxi_3r", modelo="Bajaj RE", año=2020,
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


async def seed_nivel2_postgres(database_url: str) -> None:
    """
    Seed nivel 2 — escribe datos reales a PostgreSQL via SQLAlchemy async.
    Cubre todos los conteos de 04 §5.1 y estados de 04 §5.2.
    FK order: usuario → cliente/mecanico → vehiculo → repuesto → stock_repuesto
              → orden_trabajo → pedido → reabastecimiento
    """
    import hashlib
    import os
    import uuid as _uuid

    from decimal import Decimal as D
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel
    from src.pedidos.infrastructure.repositories.models.pedido_models import (
        ClienteModel, PedidoModel,
    )
    from src.shared.infrastructure.models.usuario_model import UsuarioModel
    from src.stock.infrastructure.repositories.models.stock_model import (
        ReabastecimientoModel, StockRepuestoModel,
    )
    from src.taller.infrastructure.repositories.models.taller_models import (
        MecanicoModel, OrdenTrabajoModel, VehiculoModel,
    )

    def _phash(pw: str) -> str:
        salt = os.urandom(16)
        h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100_000)
        return salt.hex() + ":" + h.hex()

    def _uid() -> str:
        return str(_uuid.uuid4())

    engine = create_async_engine(database_url, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        async with session.begin():

            # ── 1. Usuarios ────────────────────────────────────────────────────
            admin_id = _uid()
            vendedor_id = _uid()
            mec_user_id = _uid()
            cli_ids: list[tuple[str, str]] = []  # (usuario_id, segmento)

            usuarios = [
                UsuarioModel(id=admin_id, email="admin@tecnimotos.test",
                             password_hash=_phash("admin123"), rol="ADMINISTRADOR"),
                UsuarioModel(id=vendedor_id, email="vendedor@tecnimotos.test",
                             password_hash=_phash("vend456"), rol="VENDEDOR"),
                UsuarioModel(id=mec_user_id, email="mecanico@tecnimotos.test",
                             password_hash=_phash("mec789"), rol="MECANICO_MASTER"),
            ]
            # 4 CLIENTE_CONDUCTOR (S1), 3 CLIENTE_DISTRITO (S2), 3 CLIENTE_FLOTA_DUENO (S4)
            seg_roles = [
                ("CLIENTE_CONDUCTOR", "S1"), ("CLIENTE_CONDUCTOR", "S1"),
                ("CLIENTE_CONDUCTOR", "S1"), ("CLIENTE_CONDUCTOR", "S1"),
                ("CLIENTE_DISTRITO",  "S2"), ("CLIENTE_DISTRITO",  "S2"),
                ("CLIENTE_DISTRITO",  "S2"),
                ("CLIENTE_FLOTA_DUENO", "S4"), ("CLIENTE_FLOTA_DUENO", "S4"),
                ("CLIENTE_FLOTA_DUENO", "S4"),
            ]
            for i, (rol, seg) in enumerate(seg_roles):
                uid = _uid()
                usuarios.append(UsuarioModel(
                    id=uid,
                    email=f"cliente{i:02d}@tecnimotos.test",
                    password_hash=_phash("cli000"),
                    rol=rol,
                ))
                cli_ids.append((uid, seg))

            session.add_all(usuarios)
            await session.flush()

            # ── 2. Clientes (FK → usuario) ─────────────────────────────────────
            clientes = []
            cli_model_ids: list[str] = []
            for uid, seg in cli_ids:
                cid = _uid()
                clientes.append(ClienteModel(id=cid, usuario_id=uid, segmento=seg))
                cli_model_ids.append(cid)
            session.add_all(clientes)
            await session.flush()

            # ── 3. Repuestos (25, activo True/False — no FK) ─────────────────
            categorias = ["motor", "transmision", "frenos", "electrico", "otro"]
            repuestos = []
            rep_ids: list[str] = []
            rep_codigos: list[str] = []
            for i in range(25):
                rid = _uid()
                codigo = f"SEED-{i:03d}"
                repuestos.append(RepuestoModel(
                    id=rid,
                    codigo=codigo,
                    nombre=f"Repuesto seed nivel2 {i:02d}",
                    universo="mototaxi_3r" if i % 2 == 0 else "motolineal",
                    modelo="Universal",
                    año=2018 + (i % 7),
                    categoria=categorias[i % len(categorias)],
                    precio_venta=D(str(10 + i * 4)),
                    activo=i < 20,   # 20 activos, 5 inactivos — §5.2 variedad
                ))
                rep_ids.append(rid)
                rep_codigos.append(codigo)
            session.add_all(repuestos)
            await session.flush()

            # ── 4. StockRepuesto (FK → repuesto) ─────────────────────────────
            stocks = [
                StockRepuestoModel(
                    repuesto_id=rid,
                    codigo=cod,
                    cantidad_disponible=max(0, 50 - i * 2),
                    umbral_minimo=5,
                )
                for i, (rid, cod) in enumerate(zip(rep_ids, rep_codigos))
            ]
            session.add_all(stocks)
            await session.flush()

            # ── 5. Vehículos (sin FK obligatoria) ────────────────────────────
            vehiculos = []
            veh_ids: list[str] = []
            for i in range(8):
                vid = _uid()
                vehiculos.append(VehiculoModel(
                    id=vid,
                    universo="mototaxi_3r" if i % 2 == 0 else "motolineal",
                    modelo=f"Modelo Seed {i}",
                    año=2017 + (i % 8),
                ))
                veh_ids.append(vid)
            session.add_all(vehiculos)
            await session.flush()

            # ── 6. Mecánico (FK → usuario) ────────────────────────────────────
            mec_id = _uid()
            session.add(MecanicoModel(id=mec_id, usuario_id=mec_user_id, nivel="MASTER"))
            await session.flush()

            # ── 7. OrdenTrabajo — 8 OTs, todos los estados (§5.2) ────────────
            estados_ot = [
                ("ABIERTA", False, False),
                ("LISTA_REPUESTOS", False, False),
                ("EN_EJECUCION", False, False),
                ("REVISION_FINAL", False, False),
                ("CERRADA", True, True),
                ("CANCELADA", False, False),
                ("ABIERTA", False, False),
                ("CERRADA", True, True),
            ]
            modalidades = ["preventivo", "correctivo", "diagnostico", "soldadura"]
            for i, (estado, cli_aprobo, cobro_ok) in enumerate(estados_ot):
                session.add(OrdenTrabajoModel(
                    vehiculo_id=veh_ids[i % len(veh_ids)],
                    mecanico_master_id=mec_id,
                    modalidad=modalidades[i % len(modalidades)],
                    urgencia=["alta", "media", "baja"][i % 3],
                    estado=estado,
                    cobro_confirmado=cobro_ok,
                    cliente_aprobo_lista=cli_aprobo,
                    monto_estimado=D(str(50 + i * 20)),
                ))
            await session.flush()

            # ── 8. Pedidos — 15 con todos los estados (§5.2) ─────────────────
            estados_ped = [
                "BORRADOR", "CONFIRMADO", "EN_PREPARACION",
                "DESPACHADO", "ENTREGADO", "INCIDENCIA", "CANCELADO",
            ]
            for i in range(15):
                session.add(PedidoModel(
                    cliente_id=cli_model_ids[i % len(cli_model_ids)],
                    canal_origen="presencial" if i % 2 == 0 else "S2",
                    origen_actor="VENDEDOR",
                    estado=estados_ped[i % len(estados_ped)],
                    monto_total=D(str(30 + i * 15)),
                ))
            await session.flush()

            # ── 9. Reabastecimientos (5, sin FK) ─────────────────────────────
            for i in range(5):
                session.add(ReabastecimientoModel(
                    proveedor=f"Proveedor Seed {i}",
                    solicitado_por=vendedor_id,
                    estado="SOLICITADO",
                ))
            await session.flush()

    await engine.dispose()
    print("  nivel 2 PostgreSQL: 13 usuarios · 10 clientes · 25 repuestos · 25 stocks"
          " · 8 vehículos · 1 mecánico · 8 OTs · 15 pedidos · 5 reabastecimientos")


async def seed_usuarios_reales_pg(database_url: str) -> None:
    """Pieza D (ADR-014) — siembra los 11 usuarios reales de desarrollo (uno
    por rol/sub-rol) directamente en PostgreSQL. Idempotente. Normalmente se
    ejecuta solo al boot de la API (api/main.py), pero puede invocarse a mano
    tras un `docker compose down -v` para no esperar al próximo arranque."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.shared.infrastructure.seed_usuarios import seed_usuarios_dev_pg

    engine = create_async_engine(database_url, echo=False)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await seed_usuarios_dev_pg(session_factory)
    await engine.dispose()
    print("  usuarios: 11 usuarios reales de desarrollo sembrados en PostgreSQL (ver levantar-sistema.md)")


async def run_seed(level, module: str, env: str) -> None:
    print(f"Seed nivel {level} — módulo {module} — entorno {env}")
    if level == "usuarios":
        import os
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://tecnimotos:tecnimotos_dev@localhost:5432/tecnimotos",
        )
        await seed_usuarios_reales_pg(database_url)
    elif level == 1:
        if module == "catalogo":
            await seed_catalogo_nivel1()
        elif module == "pedidos":
            await seed_pedidos_nivel1()
        elif module == "stock":
            await seed_stock_nivel1()
        elif module == "taller":
            await seed_taller_nivel1()
        else:
            print(f"  módulo {module} nivel 1: sin implementación específica, omitido")
    elif level == 2:
        import os
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://tecnimotos:tecnimotos_dev@localhost:5432/tecnimotos",
        )
        await seed_nivel2_postgres(database_url)
    else:
        print(f"  nivel {level}: no implementado")
    print("Seed completado sin errores.")


def _parse_level(value: str):
    if value == "usuarios":
        return value
    return int(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed de datos de prueba")
    parser.add_argument("--level", type=_parse_level, required=True, choices=[1, 2, "usuarios"])
    parser.add_argument("--module", default="all",
                        help="Módulo a sembrar (nivel 1) o 'all' para nivel 2")
    parser.add_argument("--env", required=True, choices=["test", "staging", "dev"])
    args = parser.parse_args()
    asyncio.run(run_seed(args.level, args.module, args.env))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Seed idempotente de los 11 usuarios reales de desarrollo — uno por rol/sub-rol
(ADR-014, Pieza D). Reemplaza los 7 usuarios que antes solo vivían en
InMemoryUserStore.__init__ y el hack src/shared/infrastructure/dev_seed.py
(que solo sincronizaba 3 CLIENTE_* con segmento incorrecto "S1"/"S2"/"S4" en
vez de los valores reales de SegmentoCliente).

Se ejecuta en cada boot de la API cuando hay PostgreSQL disponible
(api/main.py::_lifespan) — idempotente por email, no duplica filas ni
sobrescribe contraseñas de usuarios ya creados. También invocable a mano vía
`python scripts/seed.py --level=usuarios`.

Tabla completa de credenciales: ver levantar-sistema.md.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _UsuarioSeed:
    email: str
    nombre: str
    rol: str
    password: str
    segmento: str | None = None   # SegmentoCliente — solo CLIENTE_*
    nivel_mecanico: str | None = None  # "MASTER" | "JUNIOR" — solo MECANICO_*


# (rol, email, password) — debe coincidir exactamente con levantar-sistema.md.
USUARIOS_DEV: list[_UsuarioSeed] = [
    _UsuarioSeed("admin@tecnimotos.test", "Admin Seed", "ADMINISTRADOR", "admin123"),
    _UsuarioSeed("venta@tecnimotos.test", "Vendedor Seed", "VENDEDOR", "vendedor123"),
    _UsuarioSeed("mecanico.master@tecnimotos.test", "Mecanico Master Seed", "MECANICO_MASTER", "mecmaster123", nivel_mecanico="MASTER"),
    _UsuarioSeed("mecanico.junior@tecnimotos.test", "Mecanico Junior Seed", "MECANICO_JUNIOR", "mecjunior123", nivel_mecanico="JUNIOR"),
    _UsuarioSeed("conductor@tecnimotos.test", "Conductor Seed", "CLIENTE_CONDUCTOR", "conductor123", segmento="CLIENTE_CONDUCTOR"),
    _UsuarioSeed("distrito@tecnimotos.test", "Distrito Seed", "CLIENTE_DISTRITO", "distrito123", segmento="CLIENTE_DISTRITO"),
    _UsuarioSeed("rural@tecnimotos.test", "Rural Seed", "CLIENTE_RURAL", "rural123", segmento="CLIENTE_RURAL"),
    _UsuarioSeed("flota.dueno@tecnimotos.test", "Flota Dueno Seed", "CLIENTE_FLOTA_DUENO", "flotadueno123", segmento="CLIENTE_FLOTA_DUENO"),
    _UsuarioSeed("flota.conductor@tecnimotos.test", "Flota Conductor Seed", "CLIENTE_FLOTA_CONDUCTOR", "flotaconductor123", segmento="CLIENTE_FLOTA_CONDUCTOR"),
    _UsuarioSeed("motolineal@tecnimotos.test", "Motolineal Seed", "CLIENTE_MOTOLINEAL", "motolineal123", segmento="CLIENTE_MOTOLINEAL"),
]

# SUPERADMIN aparte: no se crea vía crear_usuario (reservado para el flujo de
# bootstrap, EP-AUTH-06), pero para Pieza D (verificación visual de los 11
# roles) sí se siembra directamente con crear_superadmin_bootstrap — esta
# función NO pasa por el endpoint HTTP, así que no interfiere con la garantía
# "bootstrap-superadmin solo funciona una vez" que el endpoint sigue cumpliendo.
SUPERADMIN_SEED = _UsuarioSeed("superadmin@tecnimotos.test", "Superadmin Seed", "SUPERADMIN", "superadmin123")


async def seed_usuarios_dev_pg(session_factory: async_sessionmaker) -> None:
    from src.pedidos.infrastructure.repositories.models.pedido_models import ClienteModel
    from src.taller.infrastructure.repositories.models.taller_models import MecanicoModel
    from src.shared.infrastructure.repositories.usuario_repository_pg import UsuarioRepositoryPG

    creados = 0
    async with session_factory() as session:
        async with session.begin():
            repo = UsuarioRepositoryPG(session)

            if not await repo.existe_superadmin():
                user = await repo.crear_superadmin_bootstrap(
                    email=SUPERADMIN_SEED.email, nombre=SUPERADMIN_SEED.nombre,
                    password=SUPERADMIN_SEED.password,
                )
                creados += 1

            for seed in USUARIOS_DEV:
                existente = await repo.buscar_por_email(seed.email)
                if existente is not None:
                    continue
                user = await repo.crear_usuario(
                    email=seed.email, nombre=seed.nombre, rol=seed.rol, password=seed.password,
                )
                if seed.segmento:
                    session.add(ClienteModel(usuario_id=user.usuario_id, segmento=seed.segmento))
                if seed.nivel_mecanico:
                    session.add(MecanicoModel(usuario_id=user.usuario_id, nivel=seed.nivel_mecanico))
                creados += 1
            await session.flush()

    if creados:
        logger.info("seed_usuarios_dev: %d usuarios PG creados (11 roles de desarrollo)", creados)
    else:
        logger.info("seed_usuarios_dev: usuarios PG de desarrollo ya existían — sin cambios")

"""
Semilla idempotente de `parametros_sistema` (ADR-015). La tabla existía
migrada desde el inicio del proyecto pero nunca se sembró ni se conectó —
esta función la puebla con los 5 parámetros que antes solo vivían en
`InMemoryParametrosService._DEFAULTS` (código Python) más los 2 nuevos de
"OT activa". Se ejecuta en cada boot con PostgreSQL disponible, igual que
`seed_usuarios_dev_pg`/`seed_clientes_dev_pg` — nunca pisa un valor que
Elena/Sant ya haya cambiado desde el panel.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.shared.infrastructure.models.sistema_model import ParametrosSistemaModel
from src.shared.infrastructure.repositories.parametros_repository_pg import _serializar

logger = logging.getLogger(__name__)

# (clave, modulo, valor, descripcion, modificable_por)
PARAMETROS_SEED: list[tuple[str, str, object, str, str]] = [
    ("max_consultas_precio_sesion", "shared", 3,
     "Consultas de precio permitidas por sesión antes de exigir login (CLIENTE_*)", "ADMINISTRADOR"),
    ("reintentos_notificacion", "shared", 3,
     "Reintentos máximos al notificar repuesto disponible", "ADMINISTRADOR"),
    ("intervalo_reintento_notif_min", "shared", 10,
     "Minutos entre reintentos de notificación", "ADMINISTRADOR"),
    ("ttl_cache_parametros_segundos", "shared", 300,
     "TTL del caché Redis DB-1 de parámetros", "SUPERADMIN"),
    ("umbral_margen_alerta", "catalogo", 0.10,
     "Margen mínimo antes de alertar (10% = 0.10)", "ADMINISTRADOR"),
    ("taller.ot_activa.estados", "taller", "ABIERTA,LISTA_REPUESTOS,EN_EJECUCION,REVISION_FINAL",
     "Estados de OT que cuentan como activa en el panel BI (ADR-015)", "ADMINISTRADOR"),
    ("taller.ot_activa.dias_maximo", "taller", 7,
     "Días máximos abierta para seguir contando como OT activa (ADR-015)", "ADMINISTRADOR"),
]


async def seed_parametros_pg(session_factory: async_sessionmaker) -> None:
    creados = 0
    async with session_factory() as session:
        async with session.begin():
            for clave, modulo, valor, descripcion, modificable_por in PARAMETROS_SEED:
                stmt = select(ParametrosSistemaModel).where(ParametrosSistemaModel.clave == clave)
                existente = (await session.execute(stmt)).scalar_one_or_none()
                if existente is not None:
                    continue
                valor_str, tipo_valor = _serializar(valor)
                session.add(ParametrosSistemaModel(
                    clave=clave, modulo=modulo, valor=valor_str, tipo_valor=tipo_valor,
                    valor_defecto=valor_str, descripcion=descripcion, modificable_por=modificable_por,
                ))
                creados += 1
    if creados:
        logger.info("seed_parametros: %d parámetros creados en parametros_sistema", creados)
    else:
        logger.info("seed_parametros: parametros_sistema ya poblada — sin cambios")

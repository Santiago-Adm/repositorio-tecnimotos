#!/usr/bin/env python3
"""
Verificación de integridad del seed por nivel (04 §5.1, §5.2).
Uso: python scripts/verify_seed.py --level=2 --env=dev

Verifica TANTO el conteo de 04 §5.1 COMO las reglas de contenido de 04 §5.2
para el nivel especificado. Reporta PASS/FAIL por tabla.
Logging JSON estructurado según 02 §1.6. Nunca print(), nunca exit() silencioso.

Implementación: SQLAlchemy async + asyncpg (ya en pyproject.toml — sin psycopg2).
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from dataclasses import dataclass
from typing import Any

# ── Logging JSON — 02 §1.6 ───────────────────────────────────────────────────

sys.path.insert(0, str(__file__).replace("/scripts/verify_seed.py", ""))
try:
    from src.shared.infrastructure.logging import configure_logging
    configure_logging(service="verify-seed", version="1.0.0", environment="staging")
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

logger = logging.getLogger(__name__)


# ── Conteos por nivel — 04 §5.1 ───────────────────────────────────────────────

CONTEOS_MINIMOS: dict[int, dict[str, int]] = {
    1: {
        "repuesto": 5,
        "pedido": 3,
        "cliente": 2,
        "orden_trabajo": 2,
        "reabastecimiento": 1,
    },
    2: {
        "repuesto": 25,
        "pedido": 15,
        "cliente": 10,
        "orden_trabajo": 8,
        "reabastecimiento": 5,
    },
    3: {
        "repuesto": 55,
        "pedido": 50,
        "cliente": 30,
        "orden_trabajo": 20,
        "reabastecimiento": 10,
    },
}

# ── Contenido obligatorio para nivel ≥ 2 — 04 §5.2 ───────────────────────────
# Nota: repuesto no tiene columna estado_disponibilidad (es un estado
# calculado desde stock). Se verifica repuesto.activo para garantizar
# variedad (activos + inactivos) — equivalente funcional.
#
# Alias de compatibilidad con tests existentes:
# ESTADOS_REPUESTO representa los valores del campo activo (true/false)
ESTADOS_REPUESTO = ["true", "false"]   # repuesto.activo values

ESTADOS_ORDEN_TRABAJO = [
    "ABIERTA", "LISTA_REPUESTOS", "EN_EJECUCION",
    "REVISION_FINAL", "CERRADA", "CANCELADA",
]

SEGMENTOS_CLIENTE = ["S1", "S2", "S4"]

ESTADOS_PEDIDO = [
    "BORRADOR", "CONFIRMADO", "EN_PREPARACION",
    "DESPACHADO", "ENTREGADO", "INCIDENCIA", "CANCELADO",
]


# ── Resultado de verificación ─────────────────────────────────────────────────

@dataclass
class ResultadoVerificacion:
    tabla: str
    criterio: str
    esperado: Any
    obtenido: Any
    pasa: bool

    def log(self) -> None:
        estado = "PASS" if self.pasa else "FAIL"
        nivel = logging.INFO if self.pasa else logging.ERROR
        logger.log(
            nivel,
            "%s — %s — %s: esperado=%s obtenido=%s",
            estado, self.tabla, self.criterio, self.esperado, self.obtenido,
            extra={
                "tabla": self.tabla,
                "criterio": self.criterio,
                "esperado": str(self.esperado),
                "obtenido": str(self.obtenido),
                "resultado": estado,
            },
        )


# ── Fake en memoria para tests unitarios ──────────────────────────────────────

class InMemorySeedQuery:
    """Implementación fake de AsyncPgQuery para tests unitarios — sin BD real."""

    def __init__(self, datos: dict) -> None:
        self._datos = datos

    async def count(self, tabla: str) -> int:
        return self._datos.get(f"count_{tabla}", 0)

    async def distinct_values(self, tabla: str, columna: str) -> list[str]:
        return self._datos.get(f"values_{tabla}_{columna}", [])

    async def close(self) -> None:
        pass


# ── Implementación async vía SQLAlchemy+asyncpg ────────────────────────────────

class AsyncPgQuery:
    """
    Consulta real a PostgreSQL via SQLAlchemy async.
    Requiere asyncpg (ya en pyproject.toml — sin dependencias adicionales).
    """

    def __init__(self, engine) -> None:
        self._engine = engine

    async def count(self, tabla: str) -> int:
        from sqlalchemy import text
        async with self._engine.connect() as conn:
            # tabla es una constante del código (04 §5.1), no input del usuario
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {tabla}"))  # nosec B608
            row = result.fetchone()
            return int(row[0]) if row else 0

    async def distinct_values(self, tabla: str, columna: str) -> list[str]:
        from sqlalchemy import text
        async with self._engine.connect() as conn:
            # tabla y columna son constantes del código (04 §5.2), no input del usuario
            result = await conn.execute(
                text(f"SELECT DISTINCT {columna}::text FROM {tabla}")  # nosec B608
            )
            return [str(r[0]) for r in result.fetchall() if r[0] is not None]

    async def close(self) -> None:
        await self._engine.dispose()


# ── Motor de verificación (async) ─────────────────────────────────────────────

async def verificar_seed(nivel: int, query: AsyncPgQuery) -> list[ResultadoVerificacion]:
    """
    Verifica conteos (04 §5.1) y reglas de contenido (04 §5.2).
    """
    resultados: list[ResultadoVerificacion] = []
    conteos = CONTEOS_MINIMOS[nivel]

    # §5.1 — Conteos mínimos por entidad
    for tabla, minimo in conteos.items():
        obtenido = await query.count(tabla)
        resultados.append(ResultadoVerificacion(
            tabla=tabla,
            criterio="conteo_minimo",
            esperado=f">= {minimo}",
            obtenido=obtenido,
            pasa=obtenido >= minimo,
        ))

    if nivel < 2:
        return resultados

    # §5.2 — Reglas de contenido obligatorio (nivel 2 y 3)

    # Repuesto: presencia de activos y de inactivos (variedad de disponibilidad)
    # Nota: la disponibilidad es un estado calculado desde stock — se verifica
    # repuesto.activo como proxy (activos=disponibles, inactivos=de baja).
    for activo_val in ["true", "false"]:
        valores = await query.distinct_values("repuesto", "activo")
        resultados.append(ResultadoVerificacion(
            tabla="repuesto",
            criterio=f"activo={activo_val}",
            esperado="presente",
            obtenido="presente" if activo_val in valores else "ausente",
            pasa=activo_val in valores,
        ))

    # OrdenTrabajo: al menos una por cada estado del ciclo de vida
    for estado in ESTADOS_ORDEN_TRABAJO:
        valores = await query.distinct_values("orden_trabajo", "estado")
        resultados.append(ResultadoVerificacion(
            tabla="orden_trabajo",
            criterio=f"estado={estado}",
            esperado="presente",
            obtenido="presente" if estado in valores else "ausente",
            pasa=estado in valores,
        ))

    # Cliente: representación de S1, S2, S4
    for segmento in SEGMENTOS_CLIENTE:
        valores = await query.distinct_values("cliente", "segmento")
        resultados.append(ResultadoVerificacion(
            tabla="cliente",
            criterio=f"segmento={segmento}",
            esperado="presente",
            obtenido="presente" if segmento in valores else "ausente",
            pasa=segmento in valores,
        ))

    # Pedido: al menos uno por cada estado
    for estado in ESTADOS_PEDIDO:
        valores = await query.distinct_values("pedido", "estado")
        resultados.append(ResultadoVerificacion(
            tabla="pedido",
            criterio=f"estado={estado}",
            esperado="presente",
            obtenido="presente" if estado in valores else "ausente",
            pasa=estado in valores,
        ))

    return resultados


# ── CLI async ─────────────────────────────────────────────────────────────────

async def main_async(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verifica integridad del seed según 04 §5.1/§5.2."
    )
    parser.add_argument(
        "--level", type=int, choices=[1, 2, 3], required=True,
        help="Nivel de seed a verificar (1=mínimo, 2=estándar, 3=completo)."
    )
    parser.add_argument(
        "--env", choices=["test", "staging", "dev"], required=True,
        help="Entorno a verificar."
    )
    args = parser.parse_args(argv)

    import os
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        logger.error(
            "DATABASE_URL no configurada — requerida para entornos reales",
            extra={"env": args.env},
        )
        return 1

    logger.info(
        "Iniciando verificación de seed",
        extra={"level": args.level, "env": args.env},
    )

    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(database_url, echo=False)
    query = AsyncPgQuery(engine)

    try:
        resultados = await verificar_seed(args.level, query)
    except Exception as exc:
        logger.error("Error durante verificación: %s", exc, exc_info=exc)
        await query.close()
        return 1
    finally:
        await query.close()

    for r in resultados:
        r.log()

    fallos = [r for r in resultados if not r.pasa]
    total = len(resultados)
    pasaron = total - len(fallos)

    if fallos:
        logger.error(
            "FAIL — %d/%d criterios fallaron",
            len(fallos), total,
            extra={"pasaron": pasaron, "fallaron": len(fallos), "total": total},
        )
        return 1

    logger.info(
        "PASS — todos los criterios verificados",
        extra={"pasaron": pasaron, "total": total},
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(main_async(argv))


if __name__ == "__main__":
    sys.exit(main())

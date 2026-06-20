#!/usr/bin/env python3
"""
Verificación de integridad del seed por nivel (04 §5.1, §5.2).
Uso: python scripts/verify_seed.py --level=2 --env=staging

Verifica TANTO el conteo de 04 §5.1 COMO las reglas de contenido de 04 §5.2
para el nivel especificado. Reporta PASS/FAIL por tabla.
Logging JSON estructurado según 02 §1.6. Nunca print(), nunca exit() silencioso.
"""
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol

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

ESTADOS_REPUESTO = ["disponible", "no_disponible", "bajo_pedido"]

ESTADOS_ORDEN_TRABAJO = [
    "ABIERTA", "LISTA_REPUESTOS", "EN_EJECUCION",
    "REVISION_FINAL", "CERRADA", "CANCELADA",
]

SEGMENTOS_CLIENTE = ["S1", "S2", "S4"]

ESTADOS_PEDIDO = [
    "BORRADOR", "CONFIRMADO", "EN_PREPARACION",
    "DESPACHADO", "ENTREGADO", "INCIDENCIA", "CANCELADO",
]


# ── Puerto de consulta — inyectable para tests ────────────────────────────────

class SeedQueryPort(Protocol):
    """Abstracción de consulta de BD — se inyecta según entorno."""

    def count(self, tabla: str) -> int: ...
    def distinct_values(self, tabla: str, columna: str) -> list[str]: ...


# ── Fake en memoria para tests ────────────────────────────────────────────────

class InMemorySeedQuery:
    """Implementación fake de SeedQueryPort para tests unitarios."""

    def __init__(self, datos: dict[str, Any]) -> None:
        self._datos = datos

    def count(self, tabla: str) -> int:
        return self._datos.get(f"count_{tabla}", 0)

    def distinct_values(self, tabla: str, columna: str) -> list[str]:
        return self._datos.get(f"values_{tabla}_{columna}", [])


# ── Implementación real — PostgreSQL ──────────────────────────────────────────

class PostgresSeedQuery:
    """Implementación real para staging/producción. Requiere psycopg2."""

    def __init__(self, database_url: str) -> None:
        try:
            import psycopg2
            self._conn = psycopg2.connect(database_url)
        except ImportError as exc:
            raise RuntimeError(
                "psycopg2 requerido para consultas reales. "
                "Instalar: pip install psycopg2-binary"
            ) from exc

    def count(self, tabla: str) -> int:
        with self._conn.cursor() as cur:
            # tabla y columna son constantes del código (04 §5.1), no input del usuario
            cur.execute(f"SELECT COUNT(*) FROM {tabla}")  # nosec B608
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def distinct_values(self, tabla: str, columna: str) -> list[str]:
        with self._conn.cursor() as cur:
            # tabla y columna son constantes del código (04 §5.2), no input del usuario
            cur.execute(
                f"SELECT DISTINCT {columna}::text FROM {tabla}"  # nosec B608
            )
            return [str(r[0]) for r in cur.fetchall() if r[0] is not None]

    def close(self) -> None:
        self._conn.close()


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
            estado,
            self.tabla,
            self.criterio,
            self.esperado,
            self.obtenido,
            extra={
                "tabla": self.tabla,
                "criterio": self.criterio,
                "esperado": str(self.esperado),
                "obtenido": str(self.obtenido),
                "resultado": estado,
            },
        )


# ── Motor de verificación ─────────────────────────────────────────────────────

def verificar_seed(nivel: int, query: SeedQueryPort) -> list[ResultadoVerificacion]:
    """
    Verifica conteos (04 §5.1) y reglas de contenido (04 §5.2).
    Retorna lista de ResultadoVerificacion — uno por criterio.
    """
    resultados: list[ResultadoVerificacion] = []
    conteos = CONTEOS_MINIMOS[nivel]

    # §5.1 — Conteos mínimos por entidad
    for tabla, minimo in conteos.items():
        obtenido = query.count(tabla)
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

    # Repuesto: al menos uno por estado de disponibilidad
    for estado in ESTADOS_REPUESTO:
        valores = query.distinct_values("repuesto", "estado_disponibilidad")
        resultados.append(ResultadoVerificacion(
            tabla="repuesto",
            criterio=f"estado_disponibilidad={estado}",
            esperado="presente",
            obtenido="presente" if estado in valores else "ausente",
            pasa=estado in valores,
        ))

    # OrdenTrabajo: al menos una por cada estado del ciclo de vida
    for estado in ESTADOS_ORDEN_TRABAJO:
        valores = query.distinct_values("orden_trabajo", "estado")
        resultados.append(ResultadoVerificacion(
            tabla="orden_trabajo",
            criterio=f"estado={estado}",
            esperado="presente",
            obtenido="presente" if estado in valores else "ausente",
            pasa=estado in valores,
        ))

    # Cliente: representación de S1, S2, S4
    for segmento in SEGMENTOS_CLIENTE:
        valores = query.distinct_values("cliente", "segmento")
        resultados.append(ResultadoVerificacion(
            tabla="cliente",
            criterio=f"segmento={segmento}",
            esperado="presente",
            obtenido="presente" if segmento in valores else "ausente",
            pasa=segmento in valores,
        ))

    # Pedido: al menos uno por cada estado
    for estado in ESTADOS_PEDIDO:
        valores = query.distinct_values("pedido", "estado")
        resultados.append(ResultadoVerificacion(
            tabla="pedido",
            criterio=f"estado={estado}",
            esperado="presente",
            obtenido="presente" if estado in valores else "ausente",
            pasa=estado in valores,
        ))

    return resultados


# ── CLI ───────────────────────────────────────────────────────────────────────

def _build_query(env: str) -> tuple[SeedQueryPort, Optional[Any]]:
    """Construye el query adapter según el entorno."""
    import os
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError(
            "Variable DATABASE_URL no configurada. "
            "Requerida para entornos reales (staging, dev)."
        )
    query = PostgresSeedQuery(database_url)
    return query, query


def main(argv: list[str] | None = None) -> int:
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

    logger.info(
        "Iniciando verificación de seed",
        extra={"level": args.level, "env": args.env},
    )

    try:
        query_obj, closeable = _build_query(args.env)
    except RuntimeError as exc:
        logger.error("Error al conectar con la BD: %s", exc)
        return 1

    try:
        resultados = verificar_seed(args.level, query_obj)
    except Exception as exc:
        logger.error("Error durante verificación: %s", exc, exc_info=exc)
        return 1
    finally:
        if closeable and hasattr(closeable, "close"):
            closeable.close()

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


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Re-cifrado de campos Fernet (07 §5.4, 08 §7.1, 03 §5.7).
Uso:
  python scripts/reencrypt_fernet.py --old-key KEY --new-key KEY [--dry-run]

Opera EXACTAMENTE sobre los campos de la lista cerrada de 03 §5.7.
Ningún campo adicional sin parche formal sobre 03-diseno-sistema §5.7.
Transacción por tabla — si falla una tabla, las anteriores quedan commiteadas
y las siguientes se omiten con log de error (no se hace rollback global).
--dry-run reporta qué haría sin ejecutar cambios reales.
Logging JSON estructurado según 02 §1.6. Nunca print(), nunca exit() silencioso.
"""
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Any, Optional, Protocol

sys.path.insert(0, str(__file__).replace("/scripts/reencrypt_fernet.py", ""))
try:
    from src.shared.infrastructure.logging import configure_logging
    configure_logging(service="reencrypt-fernet", version="1.0.0", environment="staging")
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

logger = logging.getLogger(__name__)


# ── Lista cerrada de campos Fernet — 03 §5.7 ─────────────────────────────────
# NUNCA modificar sin parche formal sobre 03-diseno-sistema §5.7.

CAMPOS_FERNET: list[tuple[str, str, str]] = [
    # (tabla, pk_columna, campo_cifrado)
    ("usuario",              "id",  "email"),
    ("usuario",              "id",  "mfa_secret"),
    ("usuario_perfil",       "usuario_id", "nombres"),
    ("usuario_perfil",       "usuario_id", "apellidos"),
    ("usuario_perfil",       "usuario_id", "dni"),
    ("usuario_perfil",       "usuario_id", "telefono_principal"),
    ("usuario_perfil",       "usuario_id", "telefono_secundario"),
    ("usuario_perfil",       "usuario_id", "direccion"),
    ("mecanico_perfil",      "mecanico_id", "dni"),
    ("mecanico_perfil",      "mecanico_id", "nombres"),
    ("mecanico_perfil",      "mecanico_id", "apellidos"),
    ("mecanico_perfil",      "mecanico_id", "telefono"),
    ("mecanico_perfil",      "mecanico_id", "direccion"),
    ("mecanico_perfil",      "mecanico_id", "fecha_nacimiento"),
    ("repuesto",             "id",  "precio_costo"),
    ("reabastecimiento_item","id",  "precio_costo_unitario"),
    ("pedido",               "id",  "descuento_aplicado"),
    ("pedido",               "id",  "notas_internas"),
    ("vehiculo",             "id",  "placa"),
    ("vehiculo",             "id",  "tarjeta_propiedad"),
    ("envio",                "id",  "direccion_destino"),
]


# ── Resultado por campo ───────────────────────────────────────────────────────

@dataclass
class ResultadoRecifrado:
    tabla: str
    campo: str
    filas_procesadas: int
    filas_omitidas: int
    error: Optional[str] = None
    dry_run: bool = False

    @property
    def exitoso(self) -> bool:
        return self.error is None

    def log(self) -> None:
        nivel = logging.INFO if self.exitoso else logging.ERROR
        prefijo = "[dry-run] " if self.dry_run else ""
        logger.log(
            nivel,
            "%s%s.%s — procesadas=%d omitidas=%d %s",
            prefijo,
            self.tabla,
            self.campo,
            self.filas_procesadas,
            self.filas_omitidas,
            f"ERROR: {self.error}" if self.error else "OK",
            extra={
                "tabla": self.tabla,
                "campo": self.campo,
                "filas_procesadas": self.filas_procesadas,
                "filas_omitidas": self.filas_omitidas,
                "dry_run": self.dry_run,
                "error": self.error,
            },
        )


# ── Puerto de base de datos — inyectable para tests ───────────────────────────

class FernetDBPort(Protocol):
    """Abstracción de acceso a BD para re-cifrado."""

    def fetch_cifrados(self, tabla: str, pk: str, campo: str) -> list[tuple[str, bytes]]: ...
    def update_cifrado(
        self, tabla: str, pk: str, campo: str, pk_valor: str, nuevo_valor: bytes
    ) -> None: ...
    def begin(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


# ── Fake en memoria para tests ────────────────────────────────────────────────

class InMemoryFernetDB:
    """Implementación fake para tests unitarios de reencrypt_fernet."""

    def __init__(self, datos: dict[str, list[tuple[str, bytes]]]) -> None:
        self._datos = datos
        self._actualizados: dict[tuple[str, str, str], bytes] = {}
        self._en_transaccion = False

    def fetch_cifrados(self, tabla: str, pk: str, campo: str) -> list[tuple[str, bytes]]:
        return self._datos.get(f"{tabla}.{campo}", [])

    def update_cifrado(
        self, tabla: str, pk: str, campo: str, pk_valor: str, nuevo_valor: bytes
    ) -> None:
        self._actualizados[(tabla, campo, pk_valor)] = nuevo_valor

    def begin(self) -> None:
        self._en_transaccion = True

    def commit(self) -> None:
        self._en_transaccion = False

    def rollback(self) -> None:
        self._en_transaccion = False

    def close(self) -> None:
        pass

    def get_actualizado(self, tabla: str, campo: str, pk_valor: str) -> Optional[bytes]:
        return self._actualizados.get((tabla, campo, pk_valor))


# ── Implementación real — PostgreSQL ──────────────────────────────────────────

class PostgresFernetDB:
    """Implementación real para staging/producción. Requiere psycopg2."""

    def __init__(self, database_url: str) -> None:
        try:
            import psycopg2
            self._conn = psycopg2.connect(database_url)
            self._conn.autocommit = False
        except ImportError as exc:
            raise RuntimeError(
                "psycopg2 requerido para operaciones reales. "
                "Instalar: pip install psycopg2-binary"
            ) from exc

    def fetch_cifrados(self, tabla: str, pk: str, campo: str) -> list[tuple[str, bytes]]:
        with self._conn.cursor() as cur:
            # tabla, pk y campo son de CAMPOS_FERNET — lista cerrada de 03 §5.7, no input del usuario
            cur.execute(
                f"SELECT {pk}, {campo} FROM {tabla} WHERE {campo} IS NOT NULL"  # nosec B608
            )
            return [(str(r[0]), bytes(r[1]) if r[1] else b"") for r in cur.fetchall()]

    def update_cifrado(
        self, tabla: str, pk: str, campo: str, pk_valor: str, nuevo_valor: bytes
    ) -> None:
        with self._conn.cursor() as cur:
            # tabla, pk y campo son de CAMPOS_FERNET — lista cerrada de 03 §5.7, no input del usuario
            cur.execute(
                f"UPDATE {tabla} SET {campo} = %s WHERE {pk} = %s",  # nosec B608
                (nuevo_valor, pk_valor),
            )

    def begin(self) -> None:
        pass  # psycopg2 ya está en transacción

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        self._conn.close()


# ── Motor de re-cifrado ───────────────────────────────────────────────────────

def _descifrar(valor: bytes, fernet_old: Any) -> Optional[bytes]:
    """Descifra un valor con la clave anterior. Retorna None si falla."""
    try:
        return fernet_old.decrypt(valor)
    except Exception:
        return None


def recifrar_campo(
    tabla: str,
    pk: str,
    campo: str,
    db: FernetDBPort,
    fernet_old: Any,
    fernet_new: Any,
    dry_run: bool,
) -> ResultadoRecifrado:
    """Re-cifra un campo de una tabla. Operación en transacción."""
    procesadas = 0
    omitidas = 0

    try:
        filas = db.fetch_cifrados(tabla, pk, campo)
        if not filas:
            return ResultadoRecifrado(
                tabla=tabla, campo=campo,
                filas_procesadas=0, filas_omitidas=0,
                dry_run=dry_run,
            )

        db.begin()
        for pk_valor, valor_cifrado in filas:
            if not valor_cifrado:
                omitidas += 1
                continue

            texto_plano = _descifrar(valor_cifrado, fernet_old)
            if texto_plano is None:
                logger.warning(
                    "No se pudo descifrar fila — omitida",
                    extra={"tabla": tabla, "campo": campo, "pk": pk_valor},
                )
                omitidas += 1
                continue

            nuevo_valor = fernet_new.encrypt(texto_plano)

            if not dry_run:
                db.update_cifrado(tabla, pk, campo, pk_valor, nuevo_valor)
            procesadas += 1

        if not dry_run:
            db.commit()

    except Exception as exc:
        if not dry_run:
            db.rollback()
        return ResultadoRecifrado(
            tabla=tabla, campo=campo,
            filas_procesadas=procesadas, filas_omitidas=omitidas,
            error=str(exc), dry_run=dry_run,
        )

    return ResultadoRecifrado(
        tabla=tabla, campo=campo,
        filas_procesadas=procesadas, filas_omitidas=omitidas,
        dry_run=dry_run,
    )


def recifrar_todos(
    db: FernetDBPort,
    old_key: str,
    new_key: str,
    dry_run: bool,
) -> list[ResultadoRecifrado]:
    """
    Re-cifra todos los campos de la lista cerrada de 03 §5.7.
    Opera campo por campo con transacción por tabla.
    """
    from cryptography.fernet import Fernet

    try:
        fernet_old = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
        fernet_new = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)
    except Exception as exc:
        raise ValueError(f"Clave Fernet inválida: {exc}") from exc

    resultados: list[ResultadoRecifrado] = []
    for tabla, pk, campo in CAMPOS_FERNET:
        logger.info(
            "Procesando campo",
            extra={"tabla": tabla, "campo": campo, "dry_run": dry_run},
        )
        resultado = recifrar_campo(tabla, pk, campo, db, fernet_old, fernet_new, dry_run)
        resultado.log()
        resultados.append(resultado)

    return resultados


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-cifra campos Fernet según 03 §5.7, 07 §5.4, 08 §7.1."
    )
    parser.add_argument(
        "--old-key", required=True,
        help="Clave Fernet anterior (base64 URL-safe).",
    )
    parser.add_argument(
        "--new-key", required=True,
        help="Clave Fernet nueva (base64 URL-safe).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Reporta qué haría sin ejecutar cambios reales.",
    )
    args = parser.parse_args(argv)

    if args.old_key == args.new_key:
        logger.error(
            "old-key y new-key son idénticas — operación sin efecto",
            extra={"dry_run": args.dry_run},
        )
        return 1

    modo = "dry-run" if args.dry_run else "ejecución real"
    logger.info(
        "Iniciando re-cifrado Fernet",
        extra={
            "modo": modo,
            "total_campos": len(CAMPOS_FERNET),
            "tablas": list({t for t, _, _ in CAMPOS_FERNET}),
        },
    )

    import os
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        logger.error("Variable DATABASE_URL no configurada")
        return 1

    try:
        db = PostgresFernetDB(database_url)
    except RuntimeError as exc:
        logger.error("Error al conectar con la BD: %s", exc)
        return 1

    try:
        resultados = recifrar_todos(db, args.old_key, args.new_key, args.dry_run)
    except ValueError as exc:
        logger.error("Error de configuración: %s", exc)
        return 1
    finally:
        db.close()

    errores = [r for r in resultados if not r.exitoso]
    total_procesadas = sum(r.filas_procesadas for r in resultados)
    total_omitidas = sum(r.filas_omitidas for r in resultados)

    if errores:
        logger.error(
            "Re-cifrado completado con errores",
            extra={
                "errores": len(errores),
                "total_procesadas": total_procesadas,
                "total_omitidas": total_omitidas,
                "dry_run": args.dry_run,
            },
        )
        return 1

    nivel = logging.WARNING if args.dry_run else logging.INFO
    logger.log(
        nivel,
        "Re-cifrado %s completado",
        "simulado (dry-run)" if args.dry_run else "real",
        extra={
            "total_procesadas": total_procesadas,
            "total_omitidas": total_omitidas,
            "dry_run": args.dry_run,
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

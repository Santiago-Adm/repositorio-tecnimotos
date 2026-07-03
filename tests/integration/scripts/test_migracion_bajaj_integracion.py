"""
Tests de integración — migrar_bajaj.py contra PostgreSQL real.
Se salta automáticamente si la BD no está disponible (mismo patrón que
tests/integration/conftest_pg.py). Usa códigos con prefijo único por test
run para no colisionar con datos reales, y limpia sus propias filas al final.
"""
from __future__ import annotations

import uuid

import openpyxl
import pytest
from sqlalchemy import text

from scripts.migracion.migrar_bajaj import migrar
from src.shared.infrastructure.database import create_engine, create_session_factory


def _crear_xlsx(tmp_path, prefijo: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["CÓDIGO", "DESCRIPCIÓN", "R", "MODELO", "PVP"])
    ws.append([f"{prefijo}-001", "TORNILLO TEST", "2R", "SUNNY ZIP", 0.5])
    ws.append([f"{prefijo}-002", "ARANDELA TEST", "3R", "TORITO 2T", 1.2])
    ws.append([f"{prefijo}-003", "PIN TEST", "4R", "RE 4S", 3.0])
    ws.append([f"{prefijo}-004", "RECHAZADA PVP", "2R", "MODELO X", "no-numero"])
    ws.append([None, None, None, None, None])  # fila vacía
    path = tmp_path / "bajaj_test.xlsx"
    wb.save(path)
    return path


@pytest.fixture
async def db_disponible():
    engine = create_engine()
    try:
        async with engine.connect() as probe:
            await probe.execute(text("SELECT 1"))
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"PostgreSQL no disponible — skipping: {exc}")
    await engine.dispose()


async def _contar_repuestos_prefijo(prefijo: str) -> int:
    engine = create_engine()
    factory = create_session_factory(engine)
    async with factory() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM repuesto WHERE codigo LIKE :p"),
            {"p": f"{prefijo}-%"},
        )
        count = result.scalar_one()
    await engine.dispose()
    return count


async def _contar_stock_prefijo(prefijo: str) -> int:
    engine = create_engine()
    factory = create_session_factory(engine)
    async with factory() as session:
        result = await session.execute(
            text(
                "SELECT COUNT(*) FROM stock_repuesto sr "
                "JOIN repuesto r ON r.id = sr.repuesto_id "
                "WHERE r.codigo LIKE :p"
            ),
            {"p": f"{prefijo}-%"},
        )
        count = result.scalar_one()
    await engine.dispose()
    return count


async def _limpiar_prefijo(prefijo: str) -> None:
    engine = create_engine()
    factory = create_session_factory(engine)
    async with factory() as session:
        await session.execute(
            text(
                "DELETE FROM stock_repuesto WHERE repuesto_id IN "
                "(SELECT id FROM repuesto WHERE codigo LIKE :p)"
            ),
            {"p": f"{prefijo}-%"},
        )
        await session.execute(
            text("DELETE FROM repuesto WHERE codigo LIKE :p"), {"p": f"{prefijo}-%"}
        )
        await session.commit()
    await engine.dispose()


class TestMigracionBajajIntegracion:
    async def test_conteo_antes_despues_y_stock_creado(self, db_disponible, tmp_path):
        prefijo = f"TESTMIG{uuid.uuid4().hex[:8].upper()}"
        xlsx = _crear_xlsx(tmp_path, prefijo)
        try:
            antes = await _contar_repuestos_prefijo(prefijo)
            assert antes == 0

            resumen = await migrar(xlsx, dry_run=False, sample_size=100, batch_size=500, database_url=None)

            despues = await _contar_repuestos_prefijo(prefijo)
            assert despues == 3  # 4 filas válidas de código único - 1 rechazada por PVP + 1 fila vacía rechazada
            assert resumen["filas_procesadas"] == 5
            assert resumen["filas_insertadas_o_actualizadas"] == 3
            assert resumen["filas_rechazadas"] == 2

            stock_creado = await _contar_stock_prefijo(prefijo)
            assert stock_creado == 3
        finally:
            await _limpiar_prefijo(prefijo)

    async def test_idempotente_segunda_corrida_no_duplica(self, db_disponible, tmp_path):
        prefijo = f"TESTMIG{uuid.uuid4().hex[:8].upper()}"
        xlsx = _crear_xlsx(tmp_path, prefijo)
        try:
            await migrar(xlsx, dry_run=False, sample_size=100, batch_size=500, database_url=None)
            primera = await _contar_repuestos_prefijo(prefijo)

            await migrar(xlsx, dry_run=False, sample_size=100, batch_size=500, database_url=None)
            segunda = await _contar_repuestos_prefijo(prefijo)

            assert primera == segunda == 3
        finally:
            await _limpiar_prefijo(prefijo)

    async def test_curacion_manual_no_se_pisa_en_rerun(self, db_disponible, tmp_path):
        prefijo = f"TESTMIG{uuid.uuid4().hex[:8].upper()}"
        xlsx = _crear_xlsx(tmp_path, prefijo)
        try:
            await migrar(xlsx, dry_run=False, sample_size=100, batch_size=500, database_url=None)

            engine = create_engine()
            factory = create_session_factory(engine)
            async with factory() as session:
                await session.execute(
                    text(
                        "UPDATE repuesto SET categoria='motor', año=2020, "
                        "descripcion='curado' WHERE codigo=:c"
                    ),
                    {"c": f"{prefijo}-001"},
                )
                await session.commit()
            await engine.dispose()

            await migrar(xlsx, dry_run=False, sample_size=100, batch_size=500, database_url=None)

            engine = create_engine()
            factory = create_session_factory(engine)
            async with factory() as session:
                result = await session.execute(
                    text(
                        "SELECT categoria, año, descripcion FROM repuesto WHERE codigo=:c"
                    ),
                    {"c": f"{prefijo}-001"},
                )
                categoria, año, descripcion = result.one()
            await engine.dispose()

            assert categoria == "motor"
            assert año == 2020
            assert descripcion == "curado"
        finally:
            await _limpiar_prefijo(prefijo)

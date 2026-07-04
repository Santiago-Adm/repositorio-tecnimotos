"""
Tests de integración — CategoriaRepositoryPG contra PostgreSQL real.
Verifica la FK real repuesto.categoria -> categoria.nombre (ON UPDATE CASCADE,
migración 593686985730). Se salta si PostgreSQL no está disponible.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from src.catalogo.domain.models.categoria import Categoria
from src.catalogo.infrastructure.repositories.categoria_repository_pg import CategoriaRepositoryPG
from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel
from tests.integration.conftest_pg import pg_session


class TestCategoriaRepositoryPG:

    async def test_crear_y_listar(self, pg_session):
        repo = CategoriaRepositoryPG(pg_session)
        nombre = f"test-{uuid.uuid4().hex[:8]}"
        await repo.guardar(Categoria(nombre=nombre, orden=99))

        categorias = await repo.listar()
        assert any(c.nombre == nombre for c in categorias)

    async def test_contar_repuestos_usando_cero_si_no_hay(self, pg_session):
        repo = CategoriaRepositoryPG(pg_session)
        assert await repo.contar_repuestos_usando("motor") == 0

    async def test_contar_repuestos_usando_refleja_uso_real(self, pg_session):
        repo = CategoriaRepositoryPG(pg_session)
        nombre = f"test-{uuid.uuid4().hex[:8]}"
        await repo.guardar(Categoria(nombre=nombre))

        pg_session.add(RepuestoModel(
            id=str(uuid.uuid4()), codigo=f"PGCAT-{uuid.uuid4().hex[:8]}",
            nombre="Repuesto test", universo="motolineal", modelo="X",
            categoria=nombre, precio_venta=Decimal("5.00"), activo=True,
        ))
        await pg_session.flush()

        assert await repo.contar_repuestos_usando(nombre) == 1

    async def test_renombrar_categoria_propaga_por_fk_cascade(self, pg_session):
        """ON UPDATE CASCADE: renombrar la categoria actualiza repuesto.categoria solo."""
        repo = CategoriaRepositoryPG(pg_session)
        nombre_viejo = f"viejo-{uuid.uuid4().hex[:8]}"
        nombre_nuevo = f"nuevo-{uuid.uuid4().hex[:8]}"
        categoria = await repo.guardar(Categoria(nombre=nombre_viejo))

        codigo = f"PGCAT-{uuid.uuid4().hex[:8]}"
        pg_session.add(RepuestoModel(
            id=str(uuid.uuid4()), codigo=codigo, nombre="Repuesto test",
            universo="motolineal", modelo="X", categoria=nombre_viejo,
            precio_venta=Decimal("5.00"), activo=True,
        ))
        await pg_session.flush()

        categoria.renombrar(nombre_nuevo)
        await repo.actualizar(categoria)
        await pg_session.flush()
        pg_session.expire_all()

        from sqlalchemy import select
        stmt = select(RepuestoModel).where(RepuestoModel.codigo == codigo)
        result = await pg_session.execute(stmt)
        repuesto = result.scalar_one()
        assert repuesto.categoria == nombre_nuevo

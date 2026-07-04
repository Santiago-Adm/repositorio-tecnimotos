"""Casos de uso: CRUD de categorías (Pieza C, sesión 2026-07-03).
Solo ADMINISTRADOR/SUPERADMIN crean/editan/eliminan — el resto de roles
consume únicamente ListarCategoriasUseCase (GET público, sin auth).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.catalogo.domain.models.categoria import (
    Categoria,
    CategoriaDuplicadaError,
    CategoriaEnUsoError,
    CategoriaNoEncontradaError,
)
from src.catalogo.domain.ports.categoria_repository import CategoriaRepository


class ListarCategoriasUseCase:
    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Categoria]:
        return await self._repo.listar()


@dataclass
class CrearCategoriaCommand:
    nombre: str
    orden: int = 0


class CrearCategoriaUseCase:
    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    async def execute(self, command: CrearCategoriaCommand) -> Categoria:
        existente = await self._repo.obtener_por_nombre(command.nombre)
        if existente is not None:
            raise CategoriaDuplicadaError(f"Ya existe una categoría llamada {command.nombre!r}")
        categoria = Categoria(nombre=command.nombre, orden=command.orden)
        return await self._repo.guardar(categoria)


@dataclass
class ActualizarCategoriaCommand:
    categoria_id: str
    nombre: Optional[str] = None
    orden: Optional[int] = None


class ActualizarCategoriaUseCase:
    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    async def execute(self, command: ActualizarCategoriaCommand) -> Categoria:
        categoria = await self._repo.obtener_por_id(command.categoria_id)
        if categoria is None:
            raise CategoriaNoEncontradaError(f"Categoria {command.categoria_id!r} no encontrada")

        if command.nombre is not None:
            nombre_norm = command.nombre.strip().lower()
            if nombre_norm != categoria.nombre:
                duplicada = await self._repo.obtener_por_nombre(nombre_norm)
                if duplicada is not None:
                    raise CategoriaDuplicadaError(f"Ya existe una categoría llamada {nombre_norm!r}")
            categoria.renombrar(command.nombre)
        if command.orden is not None:
            categoria.reordenar(command.orden)

        return await self._repo.actualizar(categoria)


@dataclass
class EliminarCategoriaCommand:
    categoria_id: str


class EliminarCategoriaUseCase:
    """Bloquea el borrado si hay repuestos usando la categoría (decisión Sant,
    sesión 2026-07-03) — devuelve el conteo para que la ruta arme un 409 claro."""

    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    async def execute(self, command: EliminarCategoriaCommand) -> None:
        categoria = await self._repo.obtener_por_id(command.categoria_id)
        if categoria is None:
            raise CategoriaNoEncontradaError(f"Categoria {command.categoria_id!r} no encontrada")

        en_uso = await self._repo.contar_repuestos_usando(categoria.nombre)
        if en_uso > 0:
            raise CategoriaEnUsoError(
                f"{en_uso} repuesto(s) usan la categoría {categoria.nombre!r} — reasígnalos antes de eliminarla"
            )

        await self._repo.eliminar(command.categoria_id)

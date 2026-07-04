"""Fake InMemoryCategoriaRepository para tests unitarios/integración sin BD real."""
from __future__ import annotations

from typing import Optional

from src.catalogo.domain.models.categoria import Categoria


class InMemoryCategoriaRepository:
    def __init__(self) -> None:
        self._store: dict[str, Categoria] = {}
        # Puente con InMemoryRepuestoRepository para contar uso — inyectado por main.py
        self._repuesto_repo = None

    def vincular_repuesto_repo(self, repuesto_repo) -> None:
        self._repuesto_repo = repuesto_repo

    async def guardar(self, categoria: Categoria) -> Categoria:
        self._store[categoria.id] = categoria
        return categoria

    async def obtener_por_id(self, categoria_id: str) -> Optional[Categoria]:
        return self._store.get(categoria_id)

    async def obtener_por_nombre(self, nombre: str) -> Optional[Categoria]:
        nombre_norm = nombre.strip().lower()
        return next((c for c in self._store.values() if c.nombre == nombre_norm), None)

    async def listar(self) -> list[Categoria]:
        return sorted(self._store.values(), key=lambda c: (c.orden, c.nombre))

    async def actualizar(self, categoria: Categoria) -> Categoria:
        if categoria.id not in self._store:
            raise ValueError(f"Categoria {categoria.id} no encontrada")
        self._store[categoria.id] = categoria
        return categoria

    async def eliminar(self, categoria_id: str) -> None:
        self._store.pop(categoria_id, None)

    async def contar_repuestos_usando(self, nombre: str) -> int:
        if self._repuesto_repo is None:
            return 0
        nombre_norm = nombre.strip().lower()
        return sum(
            1 for r in self._repuesto_repo._store.values()  # noqa: SLF001 — fake-a-fake, solo tests
            if r.categoria == nombre_norm
        )

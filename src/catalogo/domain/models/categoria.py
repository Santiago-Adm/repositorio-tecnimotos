"""Entidad Categoria — catálogo dinámico administrado por ADMINISTRADOR/SUPERADMIN."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


class DomainError(Exception):
    pass


class CategoriaNoEncontradaError(DomainError):
    pass


class CategoriaEnUsoError(DomainError):
    pass


class CategoriaDuplicadaError(DomainError):
    pass


@dataclass
class Categoria:
    nombre: str
    orden: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.nombre or not self.nombre.strip():
            raise DomainError("nombre no puede estar vacío")
        self.nombre = self.nombre.strip().lower()

    def renombrar(self, nuevo_nombre: str) -> None:
        if not nuevo_nombre or not nuevo_nombre.strip():
            raise DomainError("nombre no puede estar vacío")
        self.nombre = nuevo_nombre.strip().lower()
        self.updated_at = datetime.now(timezone.utc)

    def reordenar(self, nuevo_orden: int) -> None:
        self.orden = nuevo_orden
        self.updated_at = datetime.now(timezone.utc)

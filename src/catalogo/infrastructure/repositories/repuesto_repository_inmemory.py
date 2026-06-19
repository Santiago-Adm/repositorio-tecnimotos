"""
Fake InMemoryRepuestoRepository para pruebas unitarias (04 §4.2).
Debe pasar la misma suite de contrato LSP que RepuestoRepositoryPG.
"""
from __future__ import annotations

from typing import Optional

from src.catalogo.domain.models.repuesto import (
    HistorialPrecio,
    Repuesto,
    UniversoRepuesto,
)


class InMemoryRepuestoRepository:
    """Implementación en memoria del Protocol RepuestoRepository."""

    def __init__(self) -> None:
        self._store: dict[str, Repuesto] = {}
        self._historial: dict[str, list[HistorialPrecio]] = {}

    async def guardar(self, repuesto: Repuesto) -> Repuesto:
        self._store[repuesto.id] = repuesto
        if repuesto.id not in self._historial:
            self._historial[repuesto.id] = []
        return repuesto

    async def obtener_por_codigo(self, codigo: str) -> Optional[Repuesto]:
        return next(
            (r for r in self._store.values() if r.codigo == codigo), None
        )

    async def obtener_por_id(self, repuesto_id: str) -> Optional[Repuesto]:
        return self._store.get(repuesto_id)

    async def buscar(
        self,
        universo: UniversoRepuesto,
        modelo: Optional[str] = None,
        año: Optional[int] = None,
        solo_disponibles: bool = True,
    ) -> list[Repuesto]:
        results = []
        for r in self._store.values():
            if r.universo != universo:
                continue
            if solo_disponibles and not r.activo:
                continue
            if modelo and modelo.lower() not in r.modelo.lower():
                continue
            if año and r.año != año:
                continue
            results.append(r)
        return results

    async def buscar_por_lista_codigos(
        self,
        codigos: list[str],
        universo: Optional[UniversoRepuesto] = None,
    ) -> list[Repuesto]:
        results = []
        for r in self._store.values():
            if r.codigo not in codigos:
                continue
            if universo and r.universo != universo:
                continue
            results.append(r)
        return results

    async def obtener_historial_precio(self, repuesto_id: str) -> list[HistorialPrecio]:
        return list(self._historial.get(repuesto_id, []))

    async def actualizar(self, repuesto: Repuesto) -> Repuesto:
        if repuesto.id not in self._store:
            raise ValueError(f"Repuesto {repuesto.id} no encontrado")
        self._store[repuesto.id] = repuesto
        # Agregar historial nuevo
        hist = self._historial.setdefault(repuesto.id, [])
        for entrada in repuesto.historial_precio:
            if not any(h.id == entrada.id for h in hist):
                hist.append(entrada)
        return repuesto

    async def contar_disponibles(self, repuesto_id: str) -> int:
        repuesto = self._store.get(repuesto_id)
        if repuesto is None:
            return 0
        return 1 if repuesto.activo else 0

    def limpiar(self) -> None:
        self._store.clear()
        self._historial.clear()

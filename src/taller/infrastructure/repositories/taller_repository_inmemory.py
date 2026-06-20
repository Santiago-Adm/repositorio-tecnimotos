"""InMemoryTallerRepository — Fake para tests (04 §4.2)."""
from __future__ import annotations

from typing import Optional

from src.taller.domain.models.orden_trabajo import (
    Entrada,
    HistorialIntervencion,
    Mecanico,
    OrdenTrabajo,
    Vehiculo,
)


class InMemoryTallerRepository:
    """Implementación en memoria del Protocol TallerRepository."""

    def __init__(self) -> None:
        self._ots: dict[str, OrdenTrabajo] = {}
        self._vehiculos: dict[str, Vehiculo] = {}
        self._mecanicos: dict[str, Mecanico] = {}
        self._entradas: dict[str, Entrada] = {}
        self._historial: dict[str, HistorialIntervencion] = {}

    async def guardar_ot(self, ot: OrdenTrabajo) -> OrdenTrabajo:
        self._ots[ot.id] = ot
        return ot

    async def obtener_ot(self, ot_id: str) -> Optional[OrdenTrabajo]:
        return self._ots.get(ot_id)

    async def actualizar_ot(self, ot: OrdenTrabajo) -> OrdenTrabajo:
        if ot.id not in self._ots:
            raise ValueError(f"OT {ot.id} no encontrada")
        self._ots[ot.id] = ot
        return ot

    async def listar_ots(self) -> list[OrdenTrabajo]:
        return list(self._ots.values())

    async def guardar_vehiculo(self, v: Vehiculo) -> Vehiculo:
        self._vehiculos[v.id] = v
        return v

    async def obtener_vehiculo(self, v_id: str) -> Optional[Vehiculo]:
        return self._vehiculos.get(v_id)

    async def guardar_mecanico(self, m: Mecanico) -> Mecanico:
        self._mecanicos[m.id] = m
        return m

    async def obtener_mecanico(self, m_id: str) -> Optional[Mecanico]:
        return self._mecanicos.get(m_id)

    async def listar_mecanicos_disponibles(self) -> list[Mecanico]:
        return [m for m in self._mecanicos.values() if m.disponible]

    async def actualizar_mecanico(self, m: Mecanico) -> Mecanico:
        if m.id not in self._mecanicos:
            raise ValueError(f"Mecanico {m.id} no encontrado")
        self._mecanicos[m.id] = m
        return m

    async def guardar_entrada(self, e: Entrada) -> Entrada:
        self._entradas[e.id] = e
        return e

    async def obtener_entrada_por_ot(self, ot_id: str) -> Optional[Entrada]:
        return next(
            (e for e in self._entradas.values() if e.orden_trabajo_id == ot_id),
            None,
        )

    async def actualizar_entrada(self, e: Entrada) -> Entrada:
        if e.id not in self._entradas:
            raise ValueError(f"Entrada {e.id} no encontrada")
        self._entradas[e.id] = e
        return e

    async def guardar_historial(self, h: HistorialIntervencion) -> HistorialIntervencion:
        self._historial[h.id] = h
        return h

    def limpiar(self) -> None:
        self._ots.clear()
        self._vehiculos.clear()
        self._mecanicos.clear()
        self._entradas.clear()
        self._historial.clear()

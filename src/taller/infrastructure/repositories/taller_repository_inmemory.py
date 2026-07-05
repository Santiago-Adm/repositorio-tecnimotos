"""InMemoryTallerRepository — Fake para tests (04 §4.2)."""
from __future__ import annotations

from typing import Optional

from src.taller.domain.models.orden_trabajo import (
    Entrada,
    HistorialIntervencion,
    Mecanico,
    OrdenTrabajo,
    OrdenTrabajoEvento,
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
        self._eventos_ot: list[OrdenTrabajoEvento] = []

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

    async def actualizar_vehiculo(self, v: Vehiculo) -> Vehiculo:
        self._vehiculos[v.id] = v
        return v

    async def listar_vehiculos_por_cliente(self, cliente_id: str) -> list[Vehiculo]:
        return [v for v in self._vehiculos.values() if v.cliente_id == cliente_id]

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

    async def listar_historial(self) -> list[HistorialIntervencion]:
        return list(self._historial.values())

    # ── Historial de negocio (ADR-016) ──────────────────────────────────────────

    async def obtener_mecanico_id_por_usuario(self, usuario_id: str) -> Optional[str]:
        m = next((m for m in self._mecanicos.values() if m.usuario_id == usuario_id), None)
        return m.id if m else None

    async def tiene_actividad_cliente(self, cliente_id: str) -> bool:
        """True si el cliente tiene vehículo/OT/entrada real — bloquea el DELETE
        físico de usuario (ADR-016)."""
        if any(v.cliente_id == cliente_id for v in self._vehiculos.values()):
            return True
        if any(ot.cliente_id == cliente_id for ot in self._ots.values()):
            return True
        if any(e.cliente_id == cliente_id for e in self._entradas.values()):
            return True
        return False

    async def tiene_actividad_mecanico(self, mecanico_id: str) -> bool:
        """True si el mecánico tiene OT asignada o es supervisor de otro
        mecánico — bloquea el DELETE físico de usuario (ADR-016)."""
        if any(
            ot.mecanico_master_id == mecanico_id or ot.mecanico_junior_id == mecanico_id
            for ot in self._ots.values()
        ):
            return True
        if any(m.supervisor_id == mecanico_id for m in self._mecanicos.values()):
            return True
        return False

    # ── Auditoría transversal (R29) ──────────────────────────────────────────

    async def registrar_evento_ot(self, evento: OrdenTrabajoEvento) -> OrdenTrabajoEvento:
        self._eventos_ot.append(evento)
        return evento

    async def listar_eventos_ot(self, ot_id: str) -> list[OrdenTrabajoEvento]:
        return [e for e in self._eventos_ot if e.ot_id == ot_id]

    def limpiar(self) -> None:
        self._ots.clear()
        self._vehiculos.clear()
        self._mecanicos.clear()
        self._entradas.clear()
        self._historial.clear()
        self._eventos_ot.clear()

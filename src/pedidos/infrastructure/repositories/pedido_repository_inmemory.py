"""InMemoryPedidoRepository — Fake para tests (04 §4.2)."""
from __future__ import annotations

from typing import Optional

from src.pedidos.domain.models.pedido import (
    Comprobante,
    DeudaActiva,
    Envio,
    ListaReservaProg,
    Pedido,
    PedidoNoEncontradoError,
    PlanMantenimiento,
    EstadoPlanMantenimiento,
    Proforma,
    Reserva,
)


class InMemoryPedidoRepository:
    """Implementación en memoria del Protocol PedidoRepository."""

    def __init__(self) -> None:
        self._pedidos: dict[str, Pedido] = {}
        self._reservas: dict[str, Reserva] = {}
        self._proformas: dict[str, Proforma] = {}
        self._envios: dict[str, Envio] = {}
        self._comprobantes: dict[str, Comprobante] = {}
        self._deudas: dict[str, DeudaActiva] = {}
        self._listas: dict[str, ListaReservaProg] = {}
        self._planes: dict[str, PlanMantenimiento] = {}

    # ── Pedidos ───────────────────────────────────────────────────────────────

    async def guardar(self, pedido: Pedido) -> Pedido:
        self._pedidos[pedido.id] = pedido
        return pedido

    async def obtener_por_id(self, pedido_id: str) -> Optional[Pedido]:
        return self._pedidos.get(pedido_id)

    async def listar_todos(self) -> list[Pedido]:
        return list(self._pedidos.values())

    async def listar_por_cliente(self, cliente_id: str) -> list[Pedido]:
        return [p for p in self._pedidos.values() if p.cliente_id == cliente_id]

    async def actualizar(self, pedido: Pedido) -> Pedido:
        if pedido.id not in self._pedidos:
            raise ValueError(f"Pedido {pedido.id} no encontrado")
        self._pedidos[pedido.id] = pedido
        return pedido

    # ── Reservas ──────────────────────────────────────────────────────────────

    async def guardar_reserva(self, reserva: Reserva) -> Reserva:
        self._reservas[reserva.id] = reserva
        return reserva

    async def obtener_reserva(self, reserva_id: str) -> Optional[Reserva]:
        return self._reservas.get(reserva_id)

    async def listar_reservas_por_repuesto(self, repuesto_id: str) -> list[Reserva]:
        return [r for r in self._reservas.values() if r.repuesto_id == repuesto_id]

    async def actualizar_reserva(self, reserva: Reserva) -> Reserva:
        if reserva.id not in self._reservas:
            raise ValueError(f"Reserva {reserva.id} no encontrada")
        self._reservas[reserva.id] = reserva
        return reserva

    # ── Proformas ─────────────────────────────────────────────────────────────

    async def guardar_proforma(self, proforma: Proforma) -> Proforma:
        self._proformas[proforma.id] = proforma
        return proforma

    async def obtener_proforma(self, proforma_id: str) -> Optional[Proforma]:
        return self._proformas.get(proforma_id)

    # ── Envíos ────────────────────────────────────────────────────────────────

    async def guardar_envio(self, envio: Envio) -> Envio:
        self._envios[envio.id] = envio
        return envio

    async def obtener_envio_por_pedido(self, pedido_id: str) -> Optional[Envio]:
        return next((e for e in self._envios.values() if e.pedido_id == pedido_id), None)

    # ── Comprobantes ──────────────────────────────────────────────────────────

    async def guardar_comprobante(self, comp: Comprobante) -> Comprobante:
        self._comprobantes[comp.id] = comp
        return comp

    async def obtener_comprobante(self, comp_id: str) -> Optional[Comprobante]:
        return self._comprobantes.get(comp_id)

    async def actualizar_comprobante(self, comp: Comprobante) -> Comprobante:
        if comp.id not in self._comprobantes:
            raise ValueError(f"Comprobante {comp.id} no encontrado")
        self._comprobantes[comp.id] = comp
        return comp

    async def listar_comprobantes(self) -> list[Comprobante]:
        return list(self._comprobantes.values())

    # ── Deudas ────────────────────────────────────────────────────────────────

    async def guardar_deuda(self, deuda: DeudaActiva) -> DeudaActiva:
        self._deudas[deuda.id] = deuda
        return deuda

    # ── Listas de reserva progresiva ──────────────────────────────────────────

    async def guardar_lista_reserva(self, lista: ListaReservaProg) -> ListaReservaProg:
        self._listas[lista.id] = lista
        return lista

    async def obtener_lista_reserva(self, lista_id: str) -> Optional[ListaReservaProg]:
        return self._listas.get(lista_id)

    async def actualizar_lista_reserva(self, lista: ListaReservaProg) -> ListaReservaProg:
        if lista.id not in self._listas:
            raise ValueError(f"Lista {lista.id} no encontrada")
        self._listas[lista.id] = lista
        return lista

    # ── Planes de mantenimiento ───────────────────────────────────────────────

    async def guardar_plan_mantenimiento(self, plan: PlanMantenimiento) -> PlanMantenimiento:
        self._planes[plan.id] = plan
        return plan

    async def obtener_plan_mantenimiento(self, plan_id: str) -> Optional[PlanMantenimiento]:
        return self._planes.get(plan_id)

    async def obtener_plan_activo_por_cliente(
        self, cliente_id: str, vehiculo_id: str
    ) -> Optional[PlanMantenimiento]:
        return next(
            (
                p for p in self._planes.values()
                if p.cliente_id == cliente_id
                and p.vehiculo_id == vehiculo_id
                and p.estado == EstadoPlanMantenimiento.ACTIVO
            ),
            None,
        )

    async def listar_planes_activos(self) -> list[PlanMantenimiento]:
        return [p for p in self._planes.values() if p.estado == EstadoPlanMantenimiento.ACTIVO]

    async def actualizar_plan_mantenimiento(self, plan: PlanMantenimiento) -> PlanMantenimiento:
        self._planes[plan.id] = plan
        return plan

    def limpiar(self) -> None:
        self._pedidos.clear()
        self._reservas.clear()
        self._proformas.clear()
        self._envios.clear()
        self._comprobantes.clear()
        self._deudas.clear()
        self._listas.clear()
        self._planes.clear()

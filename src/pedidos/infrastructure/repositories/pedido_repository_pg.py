"""
Repositorio PostgreSQL para Pedidos — implementa PedidoRepository Protocol.
Patrón idéntico a RepuestoRepositoryPG (catalogo).

Notas de FK:
- ReservaModel.cliente_id → cliente.id (NOT usuario.id)
- PedidoItemModel.repuesto_id → repuesto.id
- DeudaActivaModel.cliente_id → cliente.id
La aplicación garantiza que los IDs pasen FK antes de llegar aquí.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pedidos.domain.models.pedido import (
    Comprobante,
    DeudaActiva,
    Envio,
    EstadoComprobante,
    EstadoEnvio,
    EstadoListaReserva,
    EstadoPedido,
    EstadoProforma,
    EstadoReserva,
    ListaReservaProg,
    ListaReservaProg_Item,
    Pedido,
    PedidoItem,
    Proforma,
    Reserva,
    SegmentoCliente,
    TipoComprobante,
)
from src.pedidos.infrastructure.repositories.models.pedido_models import (
    ComprobanteModel,
    DeudaActivaModel,
    EnvioModel,
    ListaReservaProgresivaItemModel,
    ListaReservaProgresivaModel,
    PedidoItemModel,
    PedidoModel,
    ProformaModel,
    ReservaModel,
)


def _dt(value) -> datetime:
    """Normaliza a datetime con timezone. Soporta str ISO y datetime naive/aware."""
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(value))


class PedidoRepositoryPG:
    """Implementación SQLAlchemy del Protocol PedidoRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Pedidos ───────────────────────────────────────────────────────────────

    async def guardar(self, pedido: Pedido) -> Pedido:
        model = self._pedido_to_model(pedido)
        self._session.add(model)
        for item in pedido.items:
            self._session.add(self._item_to_model(item))
        await self._session.flush()
        return pedido

    async def obtener_por_id(self, pedido_id: str) -> Optional[Pedido]:
        stmt = select(PedidoModel).where(PedidoModel.id == pedido_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        items = await self._obtener_items(pedido_id)
        return self._pedido_to_domain(model, items)

    async def listar_todos(self) -> list[Pedido]:
        stmt = select(PedidoModel)
        result = await self._session.execute(stmt)
        pedidos = []
        for model in result.scalars().all():
            items = await self._obtener_items(model.id)
            pedidos.append(self._pedido_to_domain(model, items))
        return pedidos

    async def listar_por_cliente(self, cliente_id: str) -> list[Pedido]:
        stmt = select(PedidoModel).where(PedidoModel.cliente_id == cliente_id)
        result = await self._session.execute(stmt)
        pedidos = []
        for model in result.scalars().all():
            items = await self._obtener_items(model.id)
            pedidos.append(self._pedido_to_domain(model, items))
        return pedidos

    async def actualizar(self, pedido: Pedido) -> Pedido:
        stmt = select(PedidoModel).where(PedidoModel.id == pedido.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Pedido {pedido.id} no encontrado")
        model.estado = pedido.estado.value
        model.monto_total = pedido.monto_total
        model.descuento_aplicado = str(pedido.descuento_aplicado) if pedido.descuento_aplicado else None
        model.precio_ajustado = pedido.precio_ajustado
        model.motivo_cancelacion = pedido.motivo_cancelacion
        model.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return pedido

    # ── Reservas ──────────────────────────────────────────────────────────────

    async def guardar_reserva(self, reserva: Reserva) -> Reserva:
        self._session.add(ReservaModel(
            id=reserva.id,
            cliente_id=reserva.cliente_id,
            repuesto_id=reserva.repuesto_id,
            pedido_id=reserva.pedido_id,
            cantidad=reserva.cantidad,
            segmento=reserva.segmento.value,
            estado=reserva.estado.value,
            expira_en=reserva.expira_en,
            pago_registrado=reserva.pago_registrado,
            notificaciones_enviadas=reserva.notificaciones_enviadas,
        ))
        await self._session.flush()
        return reserva

    async def obtener_reserva(self, reserva_id: str) -> Optional[Reserva]:
        stmt = select(ReservaModel).where(ReservaModel.id == reserva_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._reserva_to_domain(model) if model else None

    async def listar_reservas_por_repuesto(self, repuesto_id: str) -> list[Reserva]:
        stmt = select(ReservaModel).where(ReservaModel.repuesto_id == repuesto_id)
        result = await self._session.execute(stmt)
        return [self._reserva_to_domain(m) for m in result.scalars().all()]

    async def actualizar_reserva(self, reserva: Reserva) -> Reserva:
        stmt = select(ReservaModel).where(ReservaModel.id == reserva.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Reserva {reserva.id} no encontrada")
        model.estado = reserva.estado.value
        model.pedido_id = reserva.pedido_id
        model.pago_registrado = reserva.pago_registrado
        model.notificaciones_enviadas = reserva.notificaciones_enviadas
        await self._session.flush()
        return reserva

    # ── Proformas ─────────────────────────────────────────────────────────────

    async def guardar_proforma(self, proforma: Proforma) -> Proforma:
        self._session.add(ProformaModel(
            id=proforma.id,
            pedido_id=proforma.pedido_id,
            numero_referencia=proforma.numero_referencia,
            estado=proforma.estado.value,
            monto_total=proforma.monto_total,
        ))
        await self._session.flush()
        return proforma

    async def obtener_proforma(self, proforma_id: str) -> Optional[Proforma]:
        stmt = select(ProformaModel).where(ProformaModel.id == proforma_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Proforma(
            id=model.id,
            pedido_id=model.pedido_id,
            numero_referencia=model.numero_referencia,
            estado=EstadoProforma(model.estado),
            monto_total=Decimal(str(model.monto_total)),
            created_at=_dt(model.created_at),
        )

    # ── Envíos ────────────────────────────────────────────────────────────────

    async def guardar_envio(self, envio: Envio) -> Envio:
        self._session.add(EnvioModel(
            id=envio.id,
            pedido_id=envio.pedido_id,
            empresa_encomienda=envio.empresa_encomienda,
            direccion_destino=envio.direccion_destino,
            estado=envio.estado.value,
        ))
        await self._session.flush()
        return envio

    async def obtener_envio_por_pedido(self, pedido_id: str) -> Optional[Envio]:
        stmt = select(EnvioModel).where(EnvioModel.pedido_id == pedido_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Envio(
            id=model.id,
            pedido_id=model.pedido_id,
            empresa_encomienda=model.empresa_encomienda,
            direccion_destino=model.direccion_destino,
            estado=EstadoEnvio(model.estado),
            created_at=_dt(model.created_at),
        )

    # ── Comprobantes ──────────────────────────────────────────────────────────

    async def guardar_comprobante(self, comp: Comprobante) -> Comprobante:
        self._session.add(ComprobanteModel(
            id=comp.id,
            pedido_id=comp.pedido_id,
            tipo=comp.tipo.value,
            estado=comp.estado.value,
            monto=comp.monto,
            emitido_por=comp.emitido_por,
            ruc_cliente=comp.ruc_cliente,
            nota_credito_id=comp.nota_credito_id,
        ))
        await self._session.flush()
        return comp

    async def obtener_comprobante(self, comp_id: str) -> Optional[Comprobante]:
        stmt = select(ComprobanteModel).where(ComprobanteModel.id == comp_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Comprobante(
            id=model.id,
            pedido_id=model.pedido_id,
            tipo=TipoComprobante(model.tipo),
            monto=Decimal(str(model.monto)),
            emitido_por=model.emitido_por,
            estado=EstadoComprobante(model.estado),
            ruc_cliente=model.ruc_cliente,
            nota_credito_id=model.nota_credito_id,
            created_at=_dt(model.created_at),
        )

    async def actualizar_comprobante(self, comp: Comprobante) -> Comprobante:
        stmt = select(ComprobanteModel).where(ComprobanteModel.id == comp.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Comprobante {comp.id} no encontrado")
        model.estado = comp.estado.value
        model.nota_credito_id = comp.nota_credito_id
        await self._session.flush()
        return comp

    # ── Deudas ────────────────────────────────────────────────────────────────

    async def guardar_deuda(self, deuda: DeudaActiva) -> DeudaActiva:
        self._session.add(DeudaActivaModel(
            id=deuda.id,
            pedido_id=deuda.pedido_id,
            cliente_id=deuda.cliente_id,
            monto_deuda=deuda.monto_deuda,
            plazo_dias=deuda.plazo_dias,
            alerta_50_en=deuda.alerta_50_en,
            alerta_vencimiento_en=deuda.alerta_vencimiento_en,
            vence_en=deuda.vence_en,
        ))
        await self._session.flush()
        return deuda

    # ── Listas de reserva progresiva ──────────────────────────────────────────

    async def guardar_lista_reserva(self, lista: ListaReservaProg) -> ListaReservaProg:
        self._session.add(ListaReservaProgresivaModel(
            id=lista.id,
            cliente_id=lista.cliente_id,
            nombre=lista.nombre,
            estado=lista.estado.value,
            ultima_actividad=lista.ultima_actividad,
        ))
        for item in lista.items:
            self._session.add(ListaReservaProgresivaItemModel(
                id=item.id,
                lista_id=lista.id,
                repuesto_id=item.repuesto_id,
                codigo=item.codigo,
                cantidad=item.cantidad,
                precio_referencia=item.precio_referencia,
            ))
        await self._session.flush()
        return lista

    async def obtener_lista_reserva(self, lista_id: str) -> Optional[ListaReservaProg]:
        stmt = select(ListaReservaProgresivaModel).where(
            ListaReservaProgresivaModel.id == lista_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        items_stmt = select(ListaReservaProgresivaItemModel).where(
            ListaReservaProgresivaItemModel.lista_id == lista_id
        )
        items_result = await self._session.execute(items_stmt)
        items = [
            ListaReservaProg_Item(
                id=m.id,
                lista_id=lista_id,
                repuesto_id=m.repuesto_id,
                codigo=m.codigo,
                cantidad=m.cantidad,
                precio_referencia=Decimal(str(m.precio_referencia)),
            )
            for m in items_result.scalars().all()
        ]
        lista = ListaReservaProg(
            id=model.id,
            cliente_id=model.cliente_id,
            nombre=model.nombre,
            estado=EstadoListaReserva(model.estado),
            items=items,
            ultima_actividad=_dt(model.ultima_actividad),
        )
        return lista

    async def actualizar_lista_reserva(self, lista: ListaReservaProg) -> ListaReservaProg:
        stmt = select(ListaReservaProgresivaModel).where(
            ListaReservaProgresivaModel.id == lista.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"ListaReserva {lista.id} no encontrada")
        model.estado = lista.estado.value
        model.ultima_actividad = lista.ultima_actividad
        # Nuevos ítems
        existentes = {
            r[0] for r in (await self._session.execute(
                select(ListaReservaProgresivaItemModel.id).where(
                    ListaReservaProgresivaItemModel.lista_id == lista.id
                )
            )).all()
        }
        for item in lista.items:
            if item.id not in existentes:
                self._session.add(ListaReservaProgresivaItemModel(
                    id=item.id,
                    lista_id=lista.id,
                    repuesto_id=item.repuesto_id,
                    codigo=item.codigo,
                    cantidad=item.cantidad,
                    precio_referencia=item.precio_referencia,
                ))
        await self._session.flush()
        return lista

    # ── Helpers privados ──────────────────────────────────────────────────────

    async def _obtener_items(self, pedido_id: str) -> list[PedidoItem]:
        stmt = select(PedidoItemModel).where(PedidoItemModel.pedido_id == pedido_id)
        result = await self._session.execute(stmt)
        return [
            PedidoItem(
                id=m.id,
                pedido_id=m.pedido_id,
                repuesto_id=m.repuesto_id,
                codigo=m.codigo,
                cantidad=m.cantidad,
                precio_unitario=Decimal(str(m.precio_unitario)),
                precio_ajustado_unit=(
                    Decimal(str(m.precio_ajustado_unit)) if m.precio_ajustado_unit else None
                ),
            )
            for m in result.scalars().all()
        ]

    def _pedido_to_model(self, pedido: Pedido) -> PedidoModel:
        return PedidoModel(
            id=pedido.id,
            cliente_id=pedido.cliente_id,
            canal_origen=pedido.canal_origen,
            origen_actor=pedido.origen_actor,
            estado=pedido.estado.value,
            monto_total=pedido.monto_total,
            descuento_aplicado=(
                str(pedido.descuento_aplicado) if pedido.descuento_aplicado else None
            ),
            precio_ajustado=pedido.precio_ajustado,
            motivo_cancelacion=pedido.motivo_cancelacion,
            orden_trabajo_id=pedido.ot_id,
        )

    def _pedido_to_domain(self, model: PedidoModel, items: list[PedidoItem]) -> Pedido:
        pedido = Pedido(
            id=model.id,
            canal_origen=model.canal_origen,
            origen_actor=model.origen_actor,
            cliente_id=model.cliente_id,
            ot_id=model.orden_trabajo_id,
            estado=EstadoPedido(model.estado),
            items=items,
            monto_total=Decimal(str(model.monto_total)) if model.monto_total else Decimal("0"),
            descuento_aplicado=(
                Decimal(model.descuento_aplicado) if model.descuento_aplicado else None
            ),
            precio_ajustado=(
                Decimal(str(model.precio_ajustado)) if model.precio_ajustado else None
            ),
            motivo_cancelacion=model.motivo_cancelacion,
            created_at=_dt(model.created_at),
            updated_at=_dt(model.updated_at),
        )
        return pedido

    def _item_to_model(self, item: PedidoItem) -> PedidoItemModel:
        return PedidoItemModel(
            id=item.id,
            pedido_id=item.pedido_id,
            repuesto_id=item.repuesto_id,
            codigo=item.codigo,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            precio_ajustado_unit=item.precio_ajustado_unit,
        )

    def _reserva_to_domain(self, model: ReservaModel) -> Reserva:
        reserva = object.__new__(Reserva)
        reserva.id = model.id
        reserva.cliente_id = model.cliente_id
        reserva.repuesto_id = model.repuesto_id
        reserva.pedido_id = model.pedido_id
        reserva.cantidad = model.cantidad
        reserva.segmento = SegmentoCliente(model.segmento)
        reserva.estado = EstadoReserva(model.estado)
        reserva.expira_en = _dt(model.expira_en)
        reserva.pago_registrado = model.pago_registrado
        reserva.notificaciones_enviadas = model.notificaciones_enviadas
        reserva.created_at = _dt(model.created_at)
        # _TRANSICIONES_VALIDAS es un field con default_factory — se inicializa via __post_init__
        # Usar object.__new__ evita re-calcular expira_en, pero necesita _TRANSICIONES_VALIDAS
        from src.pedidos.domain.models.pedido import EstadoReserva as EstadoReservaEnum
        reserva._TRANSICIONES_VALIDAS = {
            EstadoReservaEnum.ACTIVA:    [EstadoReservaEnum.CONFIRMADA, EstadoReservaEnum.EXPIRADA, EstadoReservaEnum.LIBERADA],
            EstadoReservaEnum.CONFIRMADA: [EstadoReservaEnum.LIBERADA, EstadoReservaEnum.EXPIRADA],
            EstadoReservaEnum.EXPIRADA:  [],
            EstadoReservaEnum.LIBERADA:  [],
        }
        return reserva

"""
Repositorio PostgreSQL para Stock — implementa StockRepository Protocol.
Patrón idéntico a RepuestoRepositoryPG (catalogo).
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.stock.domain.models.stock import (
    EstadoReabastecimiento,
    MovimientoStock,
    Reabastecimiento,
    ReabastecimientoItem,
    StockRepuesto,
    TipoMovimiento,
)
from src.stock.infrastructure.repositories.models.stock_model import (
    MovimientoStockModel,
    ReabastecimientoItemModel,
    ReabastecimientoModel,
    StockRepuestoModel,
)


class StockRepositoryPG:
    """Implementación SQLAlchemy del Protocol StockRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── StockRepuesto ─────────────────────────────────────────────────────────

    async def guardar(self, stock: StockRepuesto) -> StockRepuesto:
        model = StockRepuestoModel(
            id=stock.id,
            repuesto_id=stock.repuesto_id,
            codigo=stock.codigo,
            cantidad_disponible=stock.cantidad_disponible,
            cantidad_apartada=stock.cantidad_apartada,
            cantidad_en_transito=stock.cantidad_en_transito,
            umbral_minimo=stock.umbral_minimo,
        )
        self._session.add(model)
        for mov in stock.movimientos:
            self._session.add(self._movimiento_to_model(mov))
        await self._session.flush()
        return stock

    async def obtener_por_repuesto_id(self, repuesto_id: str) -> Optional[StockRepuesto]:
        stmt = select(StockRepuestoModel).where(
            StockRepuestoModel.repuesto_id == repuesto_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        movimientos = await self._obtener_movimientos_por_repuesto_id(repuesto_id)
        return self._to_domain(model, movimientos)

    async def obtener_por_codigo(self, codigo: str) -> Optional[StockRepuesto]:
        stmt = select(StockRepuestoModel).where(
            StockRepuestoModel.codigo == codigo
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        movimientos = await self._obtener_movimientos_por_repuesto_id(model.repuesto_id)
        return self._to_domain(model, movimientos)

    async def listar_todos(self) -> list[StockRepuesto]:
        stmt = select(StockRepuestoModel)
        result = await self._session.execute(stmt)
        modelos = result.scalars().all()
        stocks = []
        for modelo in modelos:
            movimientos = await self._obtener_movimientos_por_repuesto_id(modelo.repuesto_id)
            stocks.append(self._to_domain(modelo, movimientos))
        return stocks

    async def actualizar(self, stock: StockRepuesto) -> StockRepuesto:
        stmt = select(StockRepuestoModel).where(
            StockRepuestoModel.repuesto_id == stock.repuesto_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"StockRepuesto {stock.repuesto_id} no encontrado")

        model.cantidad_disponible = stock.cantidad_disponible
        model.cantidad_apartada = stock.cantidad_apartada
        model.cantidad_en_transito = stock.cantidad_en_transito
        model.umbral_minimo = stock.umbral_minimo

        # Persistir movimientos nuevos (los que no están en BD todavía)
        existentes_ids = await self._ids_movimientos_existentes(stock.repuesto_id)
        for mov in stock.movimientos:
            if mov.id not in existentes_ids:
                self._session.add(self._movimiento_to_model(mov))

        await self._session.flush()
        return stock

    async def obtener_movimientos(self, repuesto_id: str) -> list[MovimientoStock]:
        return await self._obtener_movimientos_por_repuesto_id(repuesto_id)

    # ── Reabastecimiento ──────────────────────────────────────────────────────

    async def guardar_reabastecimiento(self, reab: Reabastecimiento) -> Reabastecimiento:
        model = ReabastecimientoModel(
            id=reab.id,
            proveedor=reab.proveedor,
            solicitado_por=reab.solicitado_por,
            estado=reab.estado.value,
            notas=reab.notas,
        )
        self._session.add(model)
        for item in reab.items:
            self._session.add(self._item_to_model(reab.id, item))
        await self._session.flush()
        return reab

    async def obtener_reabastecimiento(self, reab_id: str) -> Optional[Reabastecimiento]:
        stmt = select(ReabastecimientoModel).where(ReabastecimientoModel.id == reab_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        items = await self._obtener_items_reabastecimiento(reab_id)
        return self._reab_to_domain(model, items)

    async def actualizar_reabastecimiento(self, reab: Reabastecimiento) -> Reabastecimiento:
        stmt = select(ReabastecimientoModel).where(ReabastecimientoModel.id == reab.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Reabastecimiento {reab.id} no encontrado")

        model.estado = reab.estado.value
        model.notas = reab.notas

        existentes = {
            r[0] for r in (await self._session.execute(
                select(ReabastecimientoItemModel.id).where(
                    ReabastecimientoItemModel.reabastecimiento_id == reab.id
                )
            )).all()
        }
        for item in reab.items:
            if item.id not in existentes:
                self._session.add(self._item_to_model(reab.id, item))

        await self._session.flush()
        return reab

    # ── Helpers privados ──────────────────────────────────────────────────────

    async def _obtener_movimientos_por_repuesto_id(
        self, repuesto_id: str
    ) -> list[MovimientoStock]:
        stmt = select(MovimientoStockModel).where(
            MovimientoStockModel.repuesto_id == repuesto_id
        )
        result = await self._session.execute(stmt)
        return [self._movimiento_to_domain(m) for m in result.scalars().all()]

    async def _ids_movimientos_existentes(self, repuesto_id: str) -> set[str]:
        stmt = select(MovimientoStockModel.id).where(
            MovimientoStockModel.repuesto_id == repuesto_id
        )
        result = await self._session.execute(stmt)
        return {row[0] for row in result.all()}

    async def _obtener_items_reabastecimiento(
        self, reab_id: str
    ) -> list[ReabastecimientoItem]:
        stmt = select(ReabastecimientoItemModel).where(
            ReabastecimientoItemModel.reabastecimiento_id == reab_id
        )
        result = await self._session.execute(stmt)
        return [
            ReabastecimientoItem(
                id=m.id,
                repuesto_id=m.repuesto_id,
                codigo=m.codigo,
                cantidad_solicitada=m.cantidad_solicitada,
                precio_costo_unitario=Decimal(str(m.precio_costo_unitario)),
                cantidad_recibida=m.cantidad_recibida,
            )
            for m in result.scalars().all()
        ]

    def _to_domain(
        self, model: StockRepuestoModel, movimientos: list[MovimientoStock]
    ) -> StockRepuesto:
        return StockRepuesto(
            id=model.id,
            repuesto_id=model.repuesto_id,
            codigo=model.codigo,
            cantidad_disponible=model.cantidad_disponible,
            cantidad_apartada=model.cantidad_apartada,
            cantidad_en_transito=model.cantidad_en_transito,
            umbral_minimo=model.umbral_minimo,
            movimientos=movimientos,
        )

    def _movimiento_to_model(self, mov: MovimientoStock) -> MovimientoStockModel:
        return MovimientoStockModel(
            id=mov.id,
            repuesto_id=mov.repuesto_id,
            tipo_movimiento=mov.tipo_movimiento.value,
            cantidad=mov.cantidad,
            estado_origen=mov.estado_origen,
            estado_destino=mov.estado_destino,
            actor_id=mov.actor_id,
            referencia_id=mov.referencia_id,
        )

    def _movimiento_to_domain(self, model: MovimientoStockModel) -> MovimientoStock:
        ts = model.timestamp
        if not isinstance(ts, datetime):
            ts = datetime.fromisoformat(str(ts)) if ts else datetime.now(timezone.utc)
        return MovimientoStock(
            id=model.id,
            repuesto_id=model.repuesto_id,
            tipo_movimiento=TipoMovimiento(model.tipo_movimiento),
            cantidad=model.cantidad,
            estado_origen=model.estado_origen,
            estado_destino=model.estado_destino,
            actor_id=model.actor_id,
            referencia_id=model.referencia_id or "",
            timestamp=ts,
        )

    def _reab_to_domain(
        self, model: ReabastecimientoModel, items: list[ReabastecimientoItem]
    ) -> Reabastecimiento:
        return Reabastecimiento(
            id=model.id,
            proveedor=model.proveedor,
            solicitado_por=model.solicitado_por,
            estado=EstadoReabastecimiento(model.estado),
            notas=model.notas or "",
            items=items,
        )

    def _item_to_model(
        self, reab_id: str, item: ReabastecimientoItem
    ) -> ReabastecimientoItemModel:
        return ReabastecimientoItemModel(
            id=item.id,
            reabastecimiento_id=reab_id,
            repuesto_id=item.repuesto_id,
            codigo=item.codigo,
            cantidad_solicitada=item.cantidad_solicitada,
            precio_costo_unitario=str(item.precio_costo_unitario),
            cantidad_recibida=item.cantidad_recibida,
        )

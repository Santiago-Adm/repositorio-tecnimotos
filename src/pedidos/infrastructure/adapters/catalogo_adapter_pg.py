"""
CatalogoAdapterPG / StockAdapterPG — implementaciones reales contra PostgreSQL
de CatalogoPedidosPort / StockPedidosPort (03 §8.2, Contratos 1 y 3).

Hasta esta sesión, `_get_catalogo`/`_get_stock` en api/routes/pedidos.py
devolvían siempre InMemoryCatalogoAdapter/InMemoryStockAdapter — adaptadores
"para tests" (ver su docstring), nunca poblados en el arranque real. El
resultado: POST /v1/pedidos rechazaba con 422 "no encontrado en catálogo"
cualquier repuesto real de PostgreSQL, para cualquier usuario, siempre que
la BD estuviera disponible. Confirmado con curl real contra el contenedor
(sesión 2026-07-03, ver 05-trazabilidad-ligera.md).
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel
from src.pedidos.domain.models.pedido import DomainError
from src.pedidos.domain.ports.catalogo_pedidos_port import RepuestoInfo
from src.pedidos.domain.ports.stock_pedidos_port import DisponibilidadResponse
from src.stock.infrastructure.repositories.models.stock_model import StockRepuestoModel


class CatalogoAdapterPG:
    """Implementación real de CatalogoPedidosPort contra la tabla `repuesto`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obtener_precio_vigente(self, codigo: str) -> RepuestoInfo:
        stmt = select(RepuestoModel).where(RepuestoModel.codigo == codigo)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise DomainError(f"Repuesto {codigo!r} no encontrado en catálogo")
        return RepuestoInfo(
            repuesto_id=model.id,
            codigo=model.codigo,
            precio_venta=Decimal(str(model.precio_venta)),
            nombre=model.nombre,
            categoria=model.categoria,
            universo=model.universo,
            activo=model.activo,
        )

    async def verificar_existencia(self, codigo: str) -> bool:
        stmt = select(RepuestoModel.id).where(RepuestoModel.codigo == codigo)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None


class StockAdapterPG:
    """Implementación real de StockPedidosPort contra la tabla `stock_repuesto`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def consultar_disponibilidad(self, repuesto_id: str) -> DisponibilidadResponse:
        model = await self._obtener(repuesto_id)
        return DisponibilidadResponse(
            repuesto_id=repuesto_id,
            cantidad_disponible=model.cantidad_disponible if model else 0,
        )

    async def apartar_stock(
        self, repuesto_id: str, cantidad: int, actor_id: str, referencia_id: str
    ) -> bool:
        model = await self._obtener(repuesto_id)
        if model is None or model.cantidad_disponible < cantidad:
            return False
        model.cantidad_disponible -= cantidad
        model.cantidad_apartada += cantidad
        await self._session.flush()
        return True

    async def liberar_stock(
        self, repuesto_id: str, cantidad: int, actor_id: str, referencia_id: str
    ) -> bool:
        model = await self._obtener(repuesto_id)
        if model is None or model.cantidad_apartada < cantidad:
            return False
        model.cantidad_apartada -= cantidad
        model.cantidad_disponible += cantidad
        await self._session.flush()
        return True

    async def _obtener(self, repuesto_id: str) -> StockRepuestoModel | None:
        stmt = select(StockRepuestoModel).where(StockRepuestoModel.repuesto_id == repuesto_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

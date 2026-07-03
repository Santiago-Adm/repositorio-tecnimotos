"""
CatalogoTallerAdapterPG — implementación real de CatalogoTallerPort (Contrato 2)
contra la tabla `repuesto`. Mismo motivo que catalogo_adapter_pg.py en pedidos:
_get_catalogo() en api/routes/taller.py devolvía siempre InMemoryCatalogoTallerAdapter
("para tests"), nunca poblado en el arranque real — agregar repuestos a una
orden de trabajo fallaba contra el catálogo real de PostgreSQL.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel
from src.taller.domain.models.orden_trabajo import DomainError
from src.taller.domain.ports.catalogo_taller_port import RepuestoInfoTaller


class CatalogoTallerAdapterPG:
    """Implementación real de CatalogoTallerPort contra la tabla `repuesto`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def obtener_precio_para_ot(self, codigo: str) -> RepuestoInfoTaller:
        stmt = select(RepuestoModel).where(RepuestoModel.codigo == codigo)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise DomainError(f"Repuesto {codigo!r} no encontrado en catálogo")
        return RepuestoInfoTaller(
            repuesto_id=model.id,
            codigo=model.codigo,
            precio_venta=Decimal(str(model.precio_venta)),
            nombre=model.nombre,
            activo=model.activo,
        )

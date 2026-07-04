"""
Implementación de CatalogoPedidosPort y CatalogoTallerPort (03 §8.2).
Consumidos por pedidos y taller vía inyección de dependencias.
"""
from __future__ import annotations

from src.catalogo.domain.models.repuesto import RepuestoDadoDeBajaError, RepuestoNoEncontradoError
from src.catalogo.domain.ports.catalogo_pedidos_port import PrecioVigenteResponse
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository


class CatalogoServiceImpl:
    """
    Implementa CatalogoPedidosPort y CatalogoTallerPort.
    Expuesta vía infrastructure/factories.py sin import directo entre módulos.
    """

    def __init__(self, repo: RepuestoRepository) -> None:
        self._repo = repo

    async def obtener_precio_vigente(self, codigo: str) -> PrecioVigenteResponse:
        """Contrato 1: pedidos consulta precio (02 §2.2)."""
        repuesto = await self._repo.obtener_por_codigo(codigo)
        if repuesto is None:
            raise RepuestoNoEncontradoError(
                f"Repuesto con código {codigo} no encontrado"
            )
        return PrecioVigenteResponse(
            repuesto_id=repuesto.id,
            codigo=repuesto.codigo,
            precio_venta=repuesto.precio_venta,
            nombre=repuesto.nombre,
            categoria=repuesto.categoria,
            universo=repuesto.universo.value,
            activo=repuesto.activo,
        )

    async def verificar_existencia(self, codigo: str) -> bool:
        repuesto = await self._repo.obtener_por_codigo(codigo)
        return repuesto is not None and repuesto.activo

    async def obtener_precio_para_ot(self, codigo: str) -> PrecioVigenteResponse:
        """Contrato 2: taller consulta precio (02 §2.2)."""
        return await self.obtener_precio_vigente(codigo)


class InMemoryCatalogoService:
    """
    Implementación en memoria para tests de contrato LSP (04 §6.2).
    Implementa CatalogoPedidosPort y CatalogoTallerPort.
    """

    def __init__(self) -> None:
        self._repuestos: dict[str, PrecioVigenteResponse] = {}

    def agregar_repuesto(self, repuesto: PrecioVigenteResponse) -> None:
        self._repuestos[repuesto.codigo] = repuesto

    async def obtener_precio_vigente(self, codigo: str) -> PrecioVigenteResponse:
        repuesto = self._repuestos.get(codigo)
        if repuesto is None:
            raise RepuestoNoEncontradoError(
                f"Repuesto con código {codigo} no encontrado"
            )
        return repuesto

    async def verificar_existencia(self, codigo: str) -> bool:
        repuesto = self._repuestos.get(codigo)
        return repuesto is not None and repuesto.activo

    async def obtener_precio_para_ot(self, codigo: str) -> PrecioVigenteResponse:
        return await self.obtener_precio_vigente(codigo)

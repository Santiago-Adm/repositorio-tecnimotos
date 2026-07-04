"""
Caso de uso: buscar repuestos del catálogo (HU-S1-01, EP-CAT-01, EP-CAT-02).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from src.catalogo.domain.models.repuesto import Repuesto, UniversoRepuesto
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository


@dataclass
class BuscarRepuestosQuery:
    universo: UniversoRepuesto
    modelo: Optional[str] = None
    año: Optional[int] = None
    solo_disponibles: bool = True
    destacado: Optional[bool] = None


@dataclass
class BuscarRepuestosResult:
    repuestos: list[Repuesto]
    total: int


class BuscarRepuestosUseCase:
    """
    EP-CAT-01: GET /v1/repuestos — búsqueda por universo, modelo, año.
    Filtro de universo aplicado en query de base de datos (02 §2.1, RNN-05).
    """

    def __init__(self, repo: RepuestoRepository) -> None:
        self._repo = repo

    async def execute(self, query: BuscarRepuestosQuery) -> BuscarRepuestosResult:
        repuestos = await self._repo.buscar(
            universo=query.universo,
            modelo=query.modelo,
            año=query.año,
            solo_disponibles=query.solo_disponibles,
            destacado=query.destacado,
        )
        return BuscarRepuestosResult(repuestos=repuestos, total=len(repuestos))


@dataclass
class ObtenerRepuestoPorCodigoQuery:
    codigo: str


class ObtenerRepuestoPorCodigoUseCase:
    """
    EP-CAT-02: GET /v1/repuestos/{codigo} — búsqueda por código exacto.
    NUNCA devuelve precio_venta — eso es EP-CAT-02-B (03 §6.2).
    """

    def __init__(self, repo: RepuestoRepository) -> None:
        self._repo = repo

    async def execute(self, query: ObtenerRepuestoPorCodigoQuery) -> Optional[Repuesto]:
        return await self._repo.obtener_por_codigo(query.codigo)


@dataclass
class ConsultarListaCodigosQuery:
    codigos: list[str]
    universo: Optional[UniversoRepuesto] = None


@dataclass
class ResultadoConsultaItem:
    codigo: str
    nombre: str
    universo: str
    modelo: str
    año: int
    categoria: str
    activo: bool
    advertencia_instalacion: bool
    stock_disponible: int = 0
    estado: str = "disponible"
    precio_venta: Optional[Decimal] = None
    opcion_notificacion: bool = False
    opcion_incluir_en_pedido: bool = False
    tiempo_estimado: Optional[str] = None


@dataclass
class ConsultarListaCodigosResult:
    disponibles: list[ResultadoConsultaItem]
    sin_stock: list[ResultadoConsultaItem]
    bajo_pedido: list[ResultadoConsultaItem]
    accion_pedido: bool = True


class ConsultarListaCodigosUseCase:
    """
    HU-S2-01: POST /v1/catalogo/repuestos/consulta-lista — consulta múltiple para S2.
    """

    def __init__(self, repo: RepuestoRepository) -> None:
        self._repo = repo

    async def execute(self, query: ConsultarListaCodigosQuery) -> ConsultarListaCodigosResult:
        repuestos = await self._repo.buscar_por_lista_codigos(
            codigos=query.codigos,
            universo=query.universo,
        )
        repuesto_map = {r.codigo: r for r in repuestos}

        disponibles: list[ResultadoConsultaItem] = []
        sin_stock: list[ResultadoConsultaItem] = []
        bajo_pedido: list[ResultadoConsultaItem] = []

        for codigo in query.codigos:
            repuesto = repuesto_map.get(codigo)
            if repuesto is None:
                sin_stock.append(
                    ResultadoConsultaItem(
                        codigo=codigo,
                        nombre="",
                        universo="",
                        modelo="",
                        año=0,
                        categoria="",
                        activo=False,
                        advertencia_instalacion=False,
                        stock_disponible=0,
                        estado="no_encontrado",
                        opcion_notificacion=True,
                    )
                )
                continue

            stock_count = await self._repo.contar_disponibles(repuesto.id)
            item = ResultadoConsultaItem(
                codigo=repuesto.codigo,
                nombre=repuesto.nombre,
                universo=repuesto.universo.value,
                modelo=repuesto.modelo,
                año=repuesto.año,
                categoria=repuesto.categoria,
                activo=repuesto.activo,
                advertencia_instalacion=repuesto.requiere_advertencia_instalacion(),
                stock_disponible=stock_count,
                precio_venta=repuesto.precio_venta,
            )

            if not repuesto.activo:
                sin_stock.append(item)
            elif stock_count > 0:
                item.estado = "disponible"
                disponibles.append(item)
            else:
                item.estado = "sin_stock"
                item.opcion_notificacion = True
                sin_stock.append(item)

        return ConsultarListaCodigosResult(
            disponibles=disponibles,
            sin_stock=sin_stock,
            bajo_pedido=bajo_pedido,
        )

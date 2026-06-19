"""
Caso de uso: consultar precio de un repuesto con lógica de visibilidad (EP-CAT-02-B).
HU-S1-05: niveles de visibilidad de precio.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from src.catalogo.domain.models.repuesto import Repuesto, RepuestoNoEncontradoError
from src.catalogo.domain.ports.repuesto_repository import RepuestoRepository
from src.catalogo.domain.services.repuesto_service import RepuestoService

logger = logging.getLogger(__name__)

MAX_CONSULTAS_PRECIO_DEFAULT = 3


@dataclass
class ConsultarPrecioQuery:
    codigo: str
    es_cliente: bool
    consultas_realizadas: int
    max_consultas: int = MAX_CONSULTAS_PRECIO_DEFAULT
    nivel_visibilidad: int = 0


@dataclass
class ConsultarPrecioResult:
    repuesto_id: str
    codigo: str
    precio_venta: Optional[Decimal]
    precio_visible: bool
    precio_limite_alcanzado: bool
    mensaje: Optional[str]
    disponible: bool
    opcion_notificacion: bool


class ConsultarPrecioUseCase:
    """
    EP-CAT-02-B: GET /v1/repuestos/{codigo}/precio
    Decrementa consultas_precio en sesion si rol CLIENTE_* (03 §6.2).
    Regla crítica: EP-CAT-01 y EP-CAT-02 NUNCA devuelven precio_venta.
    """

    def __init__(self, repo: RepuestoRepository) -> None:
        self._repo = repo

    async def execute(self, query: ConsultarPrecioQuery) -> ConsultarPrecioResult:
        repuesto = await self._repo.obtener_por_codigo(query.codigo)
        if repuesto is None:
            raise RepuestoNoEncontradoError(
                f"Repuesto con código {query.codigo} no encontrado"
            )

        stock_count = await self._repo.contar_disponibles(repuesto.id)
        disponible = repuesto.activo and stock_count > 0

        precio_visible, mensaje = RepuestoService.calcular_visibilidad_precio(
            consultas_realizadas=query.consultas_realizadas,
            max_consultas=query.max_consultas,
            es_cliente=query.es_cliente,
            nivel_visibilidad=query.nivel_visibilidad,
        )

        limite_alcanzado = (
            query.es_cliente
            and query.nivel_visibilidad == 1
            and query.consultas_realizadas >= query.max_consultas
        )

        logger.info(
            "Consulta de precio",
            extra={
                "codigo": query.codigo,
                "precio_visible": precio_visible,
                "es_cliente": query.es_cliente,
            },
        )

        return ConsultarPrecioResult(
            repuesto_id=repuesto.id,
            codigo=repuesto.codigo,
            precio_venta=repuesto.precio_venta if precio_visible else None,
            precio_visible=precio_visible,
            precio_limite_alcanzado=limite_alcanzado,
            mensaje=mensaje,
            disponible=disponible,
            opcion_notificacion=not disponible,
        )

"""
Router FastAPI para el módulo stock — 8 endpoints EP-STK-01 a EP-STK-08 (03 §6.4).
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, HTTPException, status
from api.auth import ADMIN_ROLES, INTERNO_ROLES, VENDEDOR_ROLES, require_roles
from pydantic import BaseModel, Field

from api.dependencies import error_response, get_request_id, success_response
from src.stock.application.use_cases.ajustar_stock import (
    ActualizarUmbralCommand,
    ActualizarUmbralUseCase,
    AjustarStockCommand,
    AjustarStockUseCase,
)
from src.stock.application.use_cases.consultar_stock import (
    ConsultarStockQuery,
    ConsultarStockUseCase,
    ListarMovimientosQuery,
    ListarMovimientosUseCase,
    ListarStockUseCase,
)
from src.stock.application.use_cases.reabastecimiento import (
    ActualizarEstadoReabastecimientoCommand,
    ActualizarEstadoReabastecimientoUseCase,
    CrearReabastecimientoCommand,
    CrearReabastecimientoUseCase,
    ItemReabastecimientoInput,
    ObtenerReabastecimientoUseCase,
)
from src.stock.domain.models.stock import (
    DomainError,
    EstadoReabastecimiento,
    ReabastecimientoNoEncontradoError,
    StockInsuficienteError,
    StockNoEncontradoError,
)

router = APIRouter(prefix="/v1", tags=["stock"])
logger = logging.getLogger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────────

class StockItem(BaseModel):
    repuesto_id: str
    codigo: str
    cantidad_disponible: int
    cantidad_apartada: int
    cantidad_en_transito: int
    umbral_minimo: int
    esta_agotado: bool
    esta_bajo_umbral: bool


class MovimientoItem(BaseModel):
    id: str
    tipo_movimiento: str
    cantidad: int
    estado_origen: str
    estado_destino: str
    actor_id: str
    referencia_id: str
    timestamp: str


class AjusteRequest(BaseModel):
    cantidad: int
    actor_id: str
    motivo: str = ""


class UmbralRequest(BaseModel):
    umbral_minimo: int = Field(ge=0)
    actor_id: str


class ItemReabRequest(BaseModel):
    repuesto_id: str
    codigo: str
    cantidad_solicitada: int = Field(gt=0)
    precio_costo_unitario: Decimal = Field(gt=0)


class CrearReabastecimientoRequest(BaseModel):
    proveedor: str = Field(min_length=1)
    items: list[ItemReabRequest] = Field(min_length=1)
    notas: str = ""


class ActualizarEstadoRequest(BaseModel):
    estado: EstadoReabastecimiento
    actor_id: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.stock.infrastructure.repositories.stock_repository_pg import StockRepositoryPG
        return StockRepositoryPG(db)
    return request.app.state.stock_repo


def _get_event_publisher(request: Request):
    return request.app.state.event_bus


def _stock_to_dict(s) -> dict:
    return StockItem(
        repuesto_id=s.repuesto_id,
        codigo=s.codigo,
        cantidad_disponible=s.cantidad_disponible,
        cantidad_apartada=s.cantidad_apartada,
        cantidad_en_transito=s.cantidad_en_transito,
        umbral_minimo=s.umbral_minimo,
        esta_agotado=s.esta_agotado(),
        esta_bajo_umbral=s.esta_bajo_umbral(),
    ).model_dump()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/stock/{codigo}", summary="EP-STK-01: Consultar stock por código")
async def consultar_stock(
    request: Request, codigo: str,
    _auth: dict = Depends(require_roles(*INTERNO_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ConsultarStockUseCase(repo)
    try:
        stock = await uc.execute(ConsultarStockQuery(codigo=codigo))
    except StockNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "STOCK_NO_ENCONTRADO",
                f"Stock para {codigo!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    return success_response(_stock_to_dict(stock), request_id=get_request_id(request))


@router.get("/stock", summary="EP-STK-02: Listar todo el stock")
async def listar_stock(
    request: Request,
    _auth: dict = Depends(require_roles(*VENDEDOR_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ListarStockUseCase(repo)
    stocks = await uc.execute()
    return success_response(
        {"stocks": [_stock_to_dict(s) for s in stocks], "total": len(stocks)},
        request_id=get_request_id(request),
    )


@router.get(
    "/stock/{codigo}/movimientos",
    summary="EP-STK-03: Historial de movimientos",
)
async def listar_movimientos(
    request: Request, codigo: str,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ListarMovimientosUseCase(repo)
    try:
        movimientos = await uc.execute(ListarMovimientosQuery(codigo=codigo))
    except StockNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "STOCK_NO_ENCONTRADO",
                f"Stock para {codigo!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    items = [
        MovimientoItem(
            id=m.id,
            tipo_movimiento=m.tipo_movimiento.value,
            cantidad=m.cantidad,
            estado_origen=m.estado_origen,
            estado_destino=m.estado_destino,
            actor_id=m.actor_id,
            referencia_id=m.referencia_id,
            timestamp=m.timestamp.isoformat(),
        ).model_dump()
        for m in movimientos
    ]
    return success_response(
        {"movimientos": items, "total": len(items)},
        request_id=get_request_id(request),
    )


@router.post("/stock/{codigo}/ajuste", summary="EP-STK-04: Ajuste manual de stock")
async def ajustar_stock(
    request: Request, codigo: str, body: AjusteRequest,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    repo = _get_repo(request)
    event_publisher = _get_event_publisher(request)
    uc = AjustarStockUseCase(repo, event_publisher)
    try:
        result = await uc.execute(
            AjustarStockCommand(
                codigo=codigo,
                cantidad=body.cantidad,
                actor_id=body.actor_id,
                motivo=body.motivo,
            )
        )
    except StockNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "STOCK_NO_ENCONTRADO",
                f"Stock para {codigo!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    except (StockInsuficienteError, DomainError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "AJUSTE_INVALIDO", str(exc), request_id=get_request_id(request)
            ),
        )
    return success_response(_stock_to_dict(result.stock), request_id=get_request_id(request))


@router.patch(
    "/stock/{codigo}/umbral",
    summary="EP-STK-05: Actualizar umbral mínimo",
)
async def actualizar_umbral(
    request: Request, codigo: str, body: UmbralRequest,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ActualizarUmbralUseCase(repo)
    try:
        stock = await uc.execute(
            ActualizarUmbralCommand(
                codigo=codigo,
                umbral_minimo=body.umbral_minimo,
                actor_id=body.actor_id,
            )
        )
    except StockNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "STOCK_NO_ENCONTRADO",
                f"Stock para {codigo!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    return success_response(_stock_to_dict(stock), request_id=get_request_id(request))


@router.post(
    "/reabastecimientos",
    status_code=status.HTTP_201_CREATED,
    summary="EP-STK-06: Crear reabastecimiento",
)
async def crear_reabastecimiento(
    request: Request, body: CrearReabastecimientoRequest,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = CrearReabastecimientoUseCase(repo)
    reab = await uc.execute(
        CrearReabastecimientoCommand(
            proveedor=body.proveedor,
            solicitado_por=getattr(request.state, "usuario_id", ""),
            items=[
                ItemReabastecimientoInput(
                    repuesto_id=i.repuesto_id,
                    codigo=i.codigo,
                    cantidad_solicitada=i.cantidad_solicitada,
                    precio_costo_unitario=i.precio_costo_unitario,
                )
                for i in body.items
            ],
            notas=body.notas,
        )
    )
    return success_response(
        {"reabastecimiento_id": reab.id, "estado": reab.estado.value, "proveedor": reab.proveedor},
        status_code=201,
        request_id=get_request_id(request),
    )


@router.patch(
    "/reabastecimientos/{reab_id}/estado",
    summary="EP-STK-07: Actualizar estado de reabastecimiento",
)
async def actualizar_estado_reabastecimiento(
    request: Request, reab_id: str, body: ActualizarEstadoRequest,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    event_publisher = _get_event_publisher(request)
    uc = ActualizarEstadoReabastecimientoUseCase(repo, event_publisher)
    try:
        reab = await uc.execute(
            ActualizarEstadoReabastecimientoCommand(
                reabastecimiento_id=reab_id,
                nuevo_estado=body.estado,
                actor_id=body.actor_id,
            )
        )
    except ReabastecimientoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "REABASTECIMIENTO_NO_ENCONTRADO",
                f"Reabastecimiento {reab_id} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "TRANSICION_INVALIDA", str(exc), request_id=get_request_id(request)
            ),
        )
    return success_response(
        {"reabastecimiento_id": reab.id, "estado": reab.estado.value},
        request_id=get_request_id(request),
    )


@router.get(
    "/reabastecimientos/{reab_id}",
    summary="EP-STK-08: Obtener reabastecimiento",
)
async def obtener_reabastecimiento(
    request: Request, reab_id: str,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    repo = _get_repo(request)
    uc = ObtenerReabastecimientoUseCase(repo)
    try:
        reab = await uc.execute(reab_id)
    except ReabastecimientoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "REABASTECIMIENTO_NO_ENCONTRADO",
                f"Reabastecimiento {reab_id} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    return success_response(
        {
            "reabastecimiento_id": reab.id,
            "proveedor": reab.proveedor,
            "estado": reab.estado.value,
            "items": [
                {
                    "repuesto_id": i.repuesto_id,
                    "codigo": i.codigo,
                    "cantidad_solicitada": i.cantidad_solicitada,
                }
                for i in reab.items
            ],
        },
        request_id=get_request_id(request),
    )

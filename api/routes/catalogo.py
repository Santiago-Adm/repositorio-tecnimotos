"""
Router FastAPI para el módulo catalogo — 7 endpoints EP-CAT-01 a EP-CAT-06
más EP para consulta de lista S2 (03 §6.2, HU-S1-01, HU-S1-05, HU-INT-01).

Regla crítica de separación (03 §6.2):
- EP-CAT-01 y EP-CAT-02 NUNCA devuelven precio_venta bajo ninguna condición.
- Solo EP-CAT-02-B expone precio, con lógica de visibilidad.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from api.auth import require_roles
from api.dependencies import error_response, get_request_id, success_response
from src.catalogo.application.use_cases.actualizar_precio import (
    ActualizarPrecioCommand,
    ActualizarPrecioVentaUseCase,
)
from src.catalogo.application.use_cases.buscar_repuestos import (
    BuscarRepuestosQuery,
    BuscarRepuestosUseCase,
    ConsultarListaCodigosQuery,
    ConsultarListaCodigosUseCase,
    ObtenerRepuestoPorCodigoQuery,
    ObtenerRepuestoPorCodigoUseCase,
)
from src.catalogo.application.use_cases.consultar_precio import (
    ConsultarPrecioQuery,
    ConsultarPrecioUseCase,
)
from src.catalogo.application.use_cases.crear_repuesto import (
    CrearRepuestoCommand,
    CrearRepuestoUseCase,
)
from src.catalogo.application.use_cases.dar_de_baja_repuesto import (
    DarDeBajaRepuestoCommand,
    DarDeBajaRepuestoUseCase,
)
from src.catalogo.application.use_cases.obtener_historial_precio import (
    ObtenerHistorialPrecioQuery,
    ObtenerHistorialPrecioUseCase,
)
from src.catalogo.domain.models.repuesto import (
    CategoriaRepuesto,
    DomainError,
    RepuestoDadoDeBajaError,
    RepuestoNoEncontradoError,
    UniversoRepuesto,
)

router = APIRouter(prefix="/v1", tags=["catalogo"])
logger = logging.getLogger(__name__)


# ── Schemas de entrada/salida ────────────────────────────────────────────────

class RepuestoListItem(BaseModel):
    """Schema para EP-CAT-01 — SIN precio_venta (03 §6.2 regla crítica)."""
    id: str
    codigo: str
    nombre: str
    universo: str
    modelo: str
    año: int
    categoria: str
    activo: bool
    advertencia_instalacion: bool


class RepuestoDetalle(BaseModel):
    """Schema para EP-CAT-02 — SIN precio_venta (03 §6.2 regla crítica)."""
    id: str
    codigo: str
    nombre: str
    descripcion: str
    universo: str
    modelo: str
    año: int
    categoria: str
    activo: bool
    advertencia_instalacion: bool
    disponible: bool
    opcion_notificacion: bool


class PrecioResponse(BaseModel):
    """Schema para EP-CAT-02-B — único endpoint que expone precio."""
    repuesto_id: str
    codigo: str
    precio_venta: Optional[Decimal]
    precio_visible: bool
    precio_limite_alcanzado: bool
    mensaje: Optional[str]
    disponible: bool
    opcion_notificacion: bool


class CrearRepuestoRequest(BaseModel):
    codigo: str = Field(min_length=1, max_length=50)
    nombre: str = Field(min_length=1, max_length=200)
    universo: UniversoRepuesto
    modelo: str = Field(min_length=1, max_length=100)
    año: int = Field(ge=1990, le=2100)
    categoria: CategoriaRepuesto
    precio_venta: Decimal = Field(gt=0)
    descripcion: str = ""


class ActualizarPrecioRequest(BaseModel):
    precio_venta: Decimal = Field(gt=0)


class DarDeBajaRequest(BaseModel):
    motivo: str = Field(min_length=1)


class ConsultarListaRequest(BaseModel):
    codigos: list[str] = Field(min_length=1)
    universo: Optional[UniversoRepuesto] = None


# ── Factory de casos de uso (simplificado — la DI real va en factories.py) ──

def _get_repo(request: Request):
    return request.app.state.catalogo_repo


def _get_event_publisher(request: Request):
    return request.app.state.event_bus


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/repuestos", summary="EP-CAT-01: Buscar repuestos")
async def buscar_repuestos(
    request: Request,
    universo: UniversoRepuesto,
    modelo: Optional[str] = None,
    año: Optional[int] = None,
) -> dict[str, Any]:
    """Búsqueda por universo, modelo y año. NUNCA devuelve precio_venta."""
    repo = _get_repo(request)
    use_case = BuscarRepuestosUseCase(repo)
    result = await use_case.execute(
        BuscarRepuestosQuery(universo=universo, modelo=modelo, año=año)
    )
    items = [
        RepuestoListItem(
            id=r.id,
            codigo=r.codigo,
            nombre=r.nombre,
            universo=r.universo.value,
            modelo=r.modelo,
            año=r.año,
            categoria=r.categoria.value,
            activo=r.activo,
            advertencia_instalacion=r.requiere_advertencia_instalacion(),
        ).model_dump()
        for r in result.repuestos
    ]
    return success_response(
        {"repuestos": items, "total": result.total},
        request_id=get_request_id(request),
    )


@router.get("/repuestos/{codigo}", summary="EP-CAT-02: Obtener repuesto por código")
async def obtener_repuesto(request: Request, codigo: str) -> dict[str, Any]:
    """Obtiene repuesto por código. NUNCA devuelve precio_venta."""
    repo = _get_repo(request)
    use_case = ObtenerRepuestoPorCodigoUseCase(repo)
    repuesto = await use_case.execute(ObtenerRepuestoPorCodigoQuery(codigo=codigo))
    if repuesto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "REPUESTO_NO_ENCONTRADO",
                "Código no encontrado — intenta con modelo y año",
                request_id=get_request_id(request),
            ),
        )
    stock = await repo.contar_disponibles(repuesto.id)
    item = RepuestoDetalle(
        id=repuesto.id,
        codigo=repuesto.codigo,
        nombre=repuesto.nombre,
        descripcion=repuesto.descripcion,
        universo=repuesto.universo.value,
        modelo=repuesto.modelo,
        año=repuesto.año,
        categoria=repuesto.categoria.value,
        activo=repuesto.activo,
        advertencia_instalacion=repuesto.requiere_advertencia_instalacion(),
        disponible=repuesto.activo and stock > 0,
        opcion_notificacion=not repuesto.activo or stock == 0,
    )
    return success_response(item.model_dump(), request_id=get_request_id(request))


@router.get("/repuestos/{codigo}/precio", summary="EP-CAT-02-B: Consultar precio")
async def consultar_precio(
    request: Request,
    codigo: str,
    consultas_realizadas: int = 0,
    nivel_visibilidad: int = 0,
) -> dict[str, Any]:
    """
    Único endpoint que expone precio_venta.
    Decrementa consultas_precio en sesión si rol CLIENTE_*.
    """
    repo = _get_repo(request)
    use_case = ConsultarPrecioUseCase(repo)
    # Determinar si es cliente (simplificado — en producción viene del JWT)
    es_cliente = nivel_visibilidad >= 1

    try:
        result = await use_case.execute(
            ConsultarPrecioQuery(
                codigo=codigo,
                es_cliente=es_cliente,
                consultas_realizadas=consultas_realizadas,
                nivel_visibilidad=nivel_visibilidad,
            )
        )
    except RepuestoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "REPUESTO_NO_ENCONTRADO",
                "Código no encontrado",
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        PrecioResponse(**result.__dict__).model_dump(),
        request_id=get_request_id(request),
    )


@router.post(
    "/repuestos",
    status_code=status.HTTP_201_CREATED,
    summary="EP-CAT-03: Crear repuesto",
)
async def crear_repuesto(
    request: Request,
    body: CrearRepuestoRequest,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """Crea repuesto nuevo. Solo ADMINISTRADOR y SUPERADMIN."""
    repo = _get_repo(request)
    event_publisher = _get_event_publisher(request)
    use_case = CrearRepuestoUseCase(repo, event_publisher)

    try:
        repuesto = await use_case.execute(
            CrearRepuestoCommand(
                codigo=body.codigo,
                nombre=body.nombre,
                universo=body.universo,
                modelo=body.modelo,
                año=body.año,
                categoria=body.categoria,
                precio_venta=body.precio_venta,
                descripcion=body.descripcion,
                creado_por=getattr(request.state, "usuario_id", ""),
            )
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                str(exc),
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        {
            "repuesto_id": repuesto.id,
            "codigo": repuesto.codigo,
            "nombre": repuesto.nombre,
            "universo": repuesto.universo.value,
        },
        status_code=201,
        request_id=get_request_id(request),
    )


@router.patch(
    "/repuestos/{codigo}/precio",
    summary="EP-CAT-04: Actualizar precio de venta",
)
async def actualizar_precio(
    request: Request,
    codigo: str,
    body: ActualizarPrecioRequest,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """Actualiza precio. Solo ADMINISTRADOR y SUPERADMIN."""
    repo = _get_repo(request)
    event_publisher = _get_event_publisher(request)
    use_case = ActualizarPrecioVentaUseCase(repo, event_publisher)

    try:
        result = await use_case.execute(
            ActualizarPrecioCommand(
                codigo=codigo,
                precio_venta=body.precio_venta,
                modificado_por=getattr(request.state, "usuario_id", ""),
            )
        )
    except RepuestoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "REPUESTO_NO_ENCONTRADO",
                f"Repuesto {codigo} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    except RepuestoDadoDeBajaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(
                "REPUESTO_DADO_DE_BAJA",
                f"Repuesto {codigo} está dado de baja",
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        {
            "repuesto_id": result.repuesto.id,
            "codigo": codigo,
            "precio_venta": str(result.repuesto.precio_venta),
            "precio_anterior": str(result.historial_entrada.precio_anterior),
        },
        request_id=get_request_id(request),
    )


@router.delete(
    "/repuestos/{codigo}",
    summary="EP-CAT-05: Dar de baja repuesto (baja lógica)",
)
async def dar_de_baja_repuesto(
    request: Request,
    codigo: str,
    body: DarDeBajaRequest,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """Baja lógica — nunca eliminación física. Solo ADMINISTRADOR y SUPERADMIN."""
    repo = _get_repo(request)
    event_publisher = _get_event_publisher(request)
    use_case = DarDeBajaRepuestoUseCase(repo, event_publisher)

    try:
        repuesto = await use_case.execute(
            DarDeBajaRepuestoCommand(
                codigo=codigo,
                motivo=body.motivo,
                dado_de_baja_por=getattr(request.state, "usuario_id", ""),
            )
        )
    except RepuestoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "REPUESTO_NO_ENCONTRADO",
                f"Repuesto {codigo} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(
                "REPUESTO_DADO_DE_BAJA",
                str(exc),
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        {"codigo": codigo, "activo": repuesto.activo},
        request_id=get_request_id(request),
    )


@router.get(
    "/repuestos/{codigo}/historial-precio",
    summary="EP-CAT-06: Historial de precio",
)
async def historial_precio(
    request: Request,
    codigo: str,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """Historial de cambios de precio. Solo ADMINISTRADOR y SUPERADMIN."""
    repo = _get_repo(request)
    use_case = ObtenerHistorialPrecioUseCase(repo)

    try:
        historial = await use_case.execute(ObtenerHistorialPrecioQuery(codigo=codigo))
    except RepuestoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "REPUESTO_NO_ENCONTRADO",
                f"Repuesto {codigo} no encontrado",
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        {
            "codigo": codigo,
            "historial": [
                {
                    "precio_anterior": str(h.precio_anterior),
                    "precio_nuevo": str(h.precio_nuevo),
                    "modificado_por": h.modificado_por,
                    "timestamp": h.timestamp.isoformat(),
                }
                for h in historial
            ],
        },
        request_id=get_request_id(request),
    )


@router.post("/catalogo/repuestos/consulta-lista", summary="HU-S2-01: Consulta múltiple")
async def consultar_lista_codigos(
    request: Request,
    body: ConsultarListaRequest,
) -> dict[str, Any]:
    """Consulta múltiple por lista de códigos para CLIENTE_DISTRITO (HU-S2-01)."""
    repo = _get_repo(request)
    use_case = ConsultarListaCodigosUseCase(repo)
    result = await use_case.execute(
        ConsultarListaCodigosQuery(codigos=body.codigos, universo=body.universo)
    )
    return success_response(
        {
            "disponibles": [item.__dict__ for item in result.disponibles],
            "sin_stock": [item.__dict__ for item in result.sin_stock],
            "bajo_pedido": [item.__dict__ for item in result.bajo_pedido],
            "accion_pedido": result.accion_pedido,
        },
        request_id=get_request_id(request),
    )

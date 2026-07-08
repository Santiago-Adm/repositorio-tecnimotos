"""
Router FastAPI para el módulo catalogo — EP-CAT-01 a EP-CAT-12
más EP para consulta de lista S2 (03 §6.2, HU-S1-01, HU-S1-05, HU-INT-01).

Regla crítica de separación (03 §6.2):
- EP-CAT-01 y EP-CAT-02 NUNCA devuelven precio_venta bajo ninguna condición.
- Solo EP-CAT-02-B expone precio, con lógica de visibilidad.

EP-CAT-04: actualiza precio, dispara repuesto.precio_actualizado.
EP-CAT-10: actualiza datos descriptivos, NUNCA toca precio ni dispara eventos.
EP-CAT-08/09: galería de imágenes (sesión 2026-06-27).
EP-CAT-11/12: reemplazar imagen y reordenar galería (sesión 2026-06-28).
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
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
from src.catalogo.application.use_cases.gestionar_imagenes import (
    EliminarImagenCommand,
    EliminarImagenUseCase,
    ImagenNoEncontradaError,
    ImagenNoPertenecerAlRepuestoError,
    ListarImagenesUseCase,
    ReemplazarImagenCommand,
    ReemplazarImagenUseCase,
    ReordenarImagenesCommand,
    ReordenarImagenesUseCase,
    ReordenInvalidoError,
    SubirImagenCommand,
    SubirImagenUseCase,
)
from src.catalogo.application.use_cases.actualizar_datos_repuesto import (
    ActualizarDatosCommand,
    ActualizarDatosRepuestoUseCase,
)
from src.catalogo.application.use_cases.obtener_historial_precio import (
    ObtenerHistorialPrecioQuery,
    ObtenerHistorialPrecioUseCase,
)
from src.catalogo.application.use_cases.subir_imagen_repuesto import (
    SubirImagenRepuestoCommand,
    SubirImagenRepuestoUseCase,
)
from src.catalogo.application.use_cases.gestionar_categorias import (
    ActualizarCategoriaCommand,
    ActualizarCategoriaUseCase,
    CrearCategoriaCommand,
    CrearCategoriaUseCase,
    EliminarCategoriaCommand,
    EliminarCategoriaUseCase,
    ListarCategoriasUseCase,
)
from src.catalogo.domain.models.categoria import (
    CategoriaDuplicadaError,
    CategoriaEnUsoError,
    CategoriaNoEncontradaError,
)
from src.catalogo.domain.models.repuesto import (
    DomainError,
    RepuestoDadoDeBajaError,
    RepuestoNoEncontradoError,
    UniversoRepuesto,
)

_IMAGEN_MAX_BYTES = 5 * 1024 * 1024  # 5 MB — decisión tomada en sesión 2026-06-27
_IMAGEN_TIPOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}

router = APIRouter(prefix="/v1", tags=["catalogo"])
logger = logging.getLogger(__name__)


# ── Schemas de entrada/salida ────────────────────────────────────────────────

class RepuestoListItem(BaseModel):
    """Schema para EP-CAT-01 — SIN precio_venta (03 §6.2 regla crítica).
    imagen_principal_url: extensión aditiva (sesión 2026-06-27) — URL de imagen orden=0."""
    id: str
    codigo: str
    nombre: str
    universo: str
    modelo: str
    año: Optional[int] = None
    categoria: str
    activo: bool
    advertencia_instalacion: bool
    imagen_principal_url: Optional[str] = None
    imagen_url: Optional[str] = None
    destacado: bool = False


class ImagenResumen(BaseModel):
    imagen_id: str
    url: str
    orden: int


class RepuestoDetalle(BaseModel):
    """Schema para EP-CAT-02 — SIN precio_venta (03 §6.2 regla crítica).
    imagenes: extensión aditiva (sesión 2026-06-27) — lista ordenada por campo orden."""
    id: str
    codigo: str
    nombre: str
    descripcion: str
    universo: str
    modelo: str
    año: Optional[int] = None
    categoria: str
    activo: bool
    advertencia_instalacion: bool
    disponible: bool
    opcion_notificacion: bool
    imagenes: list[ImagenResumen] = Field(default_factory=list)
    imagen_url: Optional[str] = None
    destacado: bool = False


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
    categoria: str = Field(min_length=1, max_length=50)
    precio_venta: Decimal = Field(gt=0)
    descripcion: str = ""


class ActualizarPrecioRequest(BaseModel):
    precio_venta: Decimal = Field(gt=0)


class ActualizarDatosRequest(BaseModel):
    """EP-CAT-10 — campos editables de repuesto. Todos opcionales (PATCH semántico).
    codigo y universo se declaran explícitamente para poder detectar su presencia y
    rechazar con 422 específico (decisión PCT 2026-06-28 corr. 2026-06-28 — mejor
    visibilidad de errores de integración que silenciar). precio_venta nunca se acepta
    aquí (usa EP-CAT-04)."""
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(default=None, max_length=2000)
    categoria: Optional[str] = Field(default=None, min_length=1, max_length=50)
    modelo: Optional[str] = Field(default=None, min_length=1, max_length=100)
    año: Optional[int] = Field(default=None, ge=1990, le=2100)
    destacado: Optional[bool] = None
    # Campos declarados para detectar su presencia — siempre deben ser None
    codigo: Optional[str] = Field(default=None, exclude=True)
    universo: Optional[str] = Field(default=None, exclude=True)


class DarDeBajaRequest(BaseModel):
    motivo: str = Field(min_length=1)


class ConsultarListaRequest(BaseModel):
    codigos: list[str] = Field(min_length=1)
    universo: Optional[UniversoRepuesto] = None


# ── Factory de casos de uso (simplificado — la DI real va en factories.py) ──

def _get_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.catalogo.infrastructure.repositories.repuesto_repository_pg import RepuestoRepositoryPG
        return RepuestoRepositoryPG(db)
    return request.app.state.catalogo_repo


def _get_event_publisher(request: Request):
    return request.app.state.event_bus


def _get_imagen_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.catalogo.infrastructure.repositories.imagen_repuesto_repository_pg import (
            ImagenRepuestoRepositoryPG,
        )
        return ImagenRepuestoRepositoryPG(db)
    return request.app.state.imagen_repuesto_repo


def _get_imagen_storage(request: Request):
    return request.app.state.imagen_storage


def _get_categoria_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.catalogo.infrastructure.repositories.categoria_repository_pg import CategoriaRepositoryPG
        return CategoriaRepositoryPG(db)
    return request.app.state.categoria_repo


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/repuestos", summary="EP-CAT-01: Buscar repuestos")
async def buscar_repuestos(
    request: Request,
    universo: UniversoRepuesto,
    modelo: Optional[str] = None,
    año: Optional[int] = None,
    categoria: Optional[str] = None,
    destacado: Optional[bool] = None,
    completar_aleatorio: bool = False,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: Optional[int] = Query(None, ge=1, le=200),
) -> dict[str, Any]:
    """Búsqueda por universo, modelo, año, categoría, destacado y texto libre (q). NUNCA
    devuelve precio_venta. Incluye imagen_principal_url (primera imagen, orden=0) si existe —
    extensión aditiva.
    page/limit son opcionales — sin limit, devuelve el resultado completo (compatibilidad
    con consumidores existentes que no paginan). Con limit, pagina server-side (ADR-012 /
    sesión orquestación — EP-CAT-01 no paginaba, ver .doc3/05-trazabilidad-ligera.md).
    destacado=true filtra la selección editorial manual usada en la landing pública.
    completar_aleatorio=true (junto con destacado=true y limit): si hay menos
    destacados que `limit`, completa con repuestos reales aleatorios (nunca
    vacío mientras haya catálogo — PIEZA A, sesión 2026-07-03). Opt-in: solo
    para vistas de escaparate público, nunca para listados administrativos.
    q: filtro avanzado por código o nombre (ILIKE substring, insensible a mayúsculas) —
    matchea contra `nombre` OR `codigo`, pensado como filtro de apoyo real sobre las 16 195
    piezas del catálogo (PCT sesión responsive/filtros, ver .doc3/03-diseno-sistema.md §6.2)."""
    repo = _get_repo(request)
    imagen_repo = _get_imagen_repo(request)
    use_case = BuscarRepuestosUseCase(repo)
    listar_uc = ListarImagenesUseCase(imagen_repo)
    result = await use_case.execute(
        BuscarRepuestosQuery(universo=universo, modelo=modelo, año=año, destacado=destacado, q=q)
    )
    repuestos_filtrados = result.repuestos

    if completar_aleatorio and destacado and limit is not None and len(repuestos_filtrados) < limit:
        faltan = limit - len(repuestos_filtrados)
        ya_incluidos = {r.id for r in repuestos_filtrados}
        relleno = await repo.buscar(
            universo=universo, año=año, random_order=True, limit=faltan + len(ya_incluidos),
        )
        relleno = [r for r in relleno if r.id not in ya_incluidos][:faltan]
        repuestos_filtrados = repuestos_filtrados + relleno

    if categoria is not None:
        _cat_norm = categoria.strip().lower()
        repuestos_filtrados = [r for r in repuestos_filtrados if r.categoria == _cat_norm]
    total_filtrado = len(repuestos_filtrados)

    total_paginas: Optional[int] = None
    if limit is not None:
        total_paginas = max(1, -(-total_filtrado // limit))
        inicio = (page - 1) * limit
        repuestos_pagina = repuestos_filtrados[inicio: inicio + limit]
    else:
        repuestos_pagina = repuestos_filtrados

    items = []
    for r in repuestos_pagina:
        imagenes = await listar_uc.execute(r.id)
        principal = imagenes[0].url if imagenes else None
        items.append(
            RepuestoListItem(
                id=r.id,
                codigo=r.codigo,
                nombre=r.nombre,
                universo=r.universo.value,
                modelo=r.modelo,
                año=r.año,
                categoria=r.categoria,
                activo=r.activo,
                advertencia_instalacion=r.requiere_advertencia_instalacion(),
                imagen_principal_url=principal,
                imagen_url=r.imagen_url,
                destacado=r.destacado,
            ).model_dump()
        )
    respuesta: dict[str, Any] = {"repuestos": items, "total": total_filtrado}
    if limit is not None:
        respuesta.update({"page": page, "limit": limit, "total_paginas": total_paginas})
    return success_response(
        respuesta,
        request_id=get_request_id(request),
    )


# Registrado antes de /repuestos/{codigo} — evita que FastAPI capture "modelos"
# como codigo (mismo patrón ya usado para EP-CAT-12 vs EP-CAT-11, ver memoria).
@router.get("/repuestos/modelos", summary="EP-CAT-17: Listar modelos distintos por universo")
async def listar_modelos(request: Request, universo: UniversoRepuesto) -> dict[str, Any]:
    """Público — sin auth. Puebla el autocomplete de modelo en el catálogo
    (107 valores reales confirmados en FASE 0.3, sesión 2026-07-03 — pocos y
    reutilizables, no texto libre disperso)."""
    repo = _get_repo(request)
    modelos = await repo.listar_modelos_distintos(universo)
    return success_response({"modelos": modelos}, request_id=get_request_id(request))


@router.get("/repuestos/{codigo}", summary="EP-CAT-02: Obtener repuesto por código")
async def obtener_repuesto(request: Request, codigo: str) -> dict[str, Any]:
    """Obtiene repuesto por código. NUNCA devuelve precio_venta.
    Incluye lista de imágenes ordenadas por campo orden — extensión aditiva."""
    repo = _get_repo(request)
    imagen_repo = _get_imagen_repo(request)
    use_case = ObtenerRepuestoPorCodigoUseCase(repo)
    listar_uc = ListarImagenesUseCase(imagen_repo)
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
    imagenes = await listar_uc.execute(repuesto.id)
    item = RepuestoDetalle(
        id=repuesto.id,
        codigo=repuesto.codigo,
        nombre=repuesto.nombre,
        descripcion=repuesto.descripcion,
        universo=repuesto.universo.value,
        modelo=repuesto.modelo,
        año=repuesto.año,
        categoria=repuesto.categoria,
        activo=repuesto.activo,
        advertencia_instalacion=repuesto.requiere_advertencia_instalacion(),
        disponible=repuesto.activo and stock > 0,
        opcion_notificacion=not repuesto.activo or stock == 0,
        imagenes=[
            ImagenResumen(imagen_id=img.id, url=img.url, orden=img.orden)
            for img in imagenes
        ],
        imagen_url=repuesto.imagen_url,
        destacado=repuesto.destacado,
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
    categoria_repo = _get_categoria_repo(request)
    if await categoria_repo.obtener_por_nombre(body.categoria) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "CATEGORIA_NO_ENCONTRADA",
                f"Categoría {body.categoria!r} no existe — crear vía POST /v1/categorias primero",
                request_id=get_request_id(request),
            ),
        )

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
                categoria=body.categoria.strip().lower(),
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


# ── EP-CAT-10 — Editar datos descriptivos de repuesto ────────────────────────

@router.patch(
    "/repuestos/{codigo}",
    summary="EP-CAT-10: Actualizar datos descriptivos de repuesto",
)
async def actualizar_datos_repuesto(
    request: Request,
    codigo: str,
    body: ActualizarDatosRequest,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """
    Corrige nombre, descripcion, categoria, modelo o año.
    NUNCA toca precio_venta ni dispara repuesto.precio_actualizado.
    Solo ADMINISTRADOR y SUPERADMIN.
    """
    _no_editables = [campo for campo, val in (("codigo", body.codigo), ("universo", body.universo)) if val is not None]
    if _no_editables:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"Los campos {_no_editables} no son editables por este endpoint. "
                "`codigo` es el identificador canónico del repuesto y no se modifica. "
                "`universo` no es editable una vez creado el repuesto.",
                request_id=get_request_id(request),
            ),
        )

    if body.categoria is not None:
        categoria_repo = _get_categoria_repo(request)
        if await categoria_repo.obtener_por_nombre(body.categoria) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_response(
                    "CATEGORIA_NO_ENCONTRADA",
                    f"Categoría {body.categoria!r} no existe — crear vía POST /v1/categorias primero",
                    request_id=get_request_id(request),
                ),
            )

    repo = _get_repo(request)
    use_case = ActualizarDatosRepuestoUseCase(repo)

    try:
        repuesto = await use_case.execute(
            ActualizarDatosCommand(
                codigo=codigo,
                modificado_por=getattr(request.state, "usuario_id", ""),
                nombre=body.nombre,
                descripcion=body.descripcion,
                categoria=body.categoria.strip().lower() if body.categoria else None,
                modelo=body.modelo,
                año=body.año,
                destacado=body.destacado,
            )
        )
    except RepuestoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "REPUESTO_NO_ENCONTRADO",
                f"Repuesto {codigo!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    except RepuestoDadoDeBajaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(
                "REPUESTO_DADO_DE_BAJA",
                f"Repuesto {codigo!r} está dado de baja — no se puede editar",
                request_id=get_request_id(request),
            ),
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA", str(exc),
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        {
            "repuesto_id": repuesto.id,
            "codigo": repuesto.codigo,
            "nombre": repuesto.nombre,
            "descripcion": repuesto.descripcion,
            "categoria": repuesto.categoria,
            "modelo": repuesto.modelo,
            "año": repuesto.año,
            "destacado": repuesto.destacado,
            "updated_at": repuesto.updated_at.isoformat(),
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


# ── EP-CAT-08 — Subir imagen a repuesto ──────────────────────────────────────

@router.post(
    "/repuestos/{codigo}/imagenes",
    status_code=status.HTTP_201_CREATED,
    summary="EP-CAT-08: Subir imagen a repuesto",
)
async def subir_imagen_repuesto(
    request: Request,
    codigo: str,
    archivo: UploadFile = File(...),
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """
    Solo ADMINISTRADOR y SUPERADMIN.
    Tipos permitidos: image/jpeg, image/png, image/webp.
    Límite: 5 MB por imagen (decisión sesión 2026-06-27).
    La primera imagen subida (orden=0) se convierte automáticamente en la principal.
    """
    if archivo.content_type not in _IMAGEN_TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"Tipo de archivo no permitido: {archivo.content_type!r}. "
                "Permitidos: image/jpeg, image/png, image/webp",
                request_id=get_request_id(request),
            ),
        )

    contenido = await archivo.read()
    if len(contenido) > _IMAGEN_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"El archivo supera el límite de 5 MB ({len(contenido)} bytes recibidos)",
                request_id=get_request_id(request),
            ),
        )

    repo = _get_repo(request)
    imagen_repo = _get_imagen_repo(request)
    storage = _get_imagen_storage(request)
    use_case = SubirImagenUseCase(repo, imagen_repo, storage)

    try:
        imagen = await use_case.execute(
            SubirImagenCommand(
                codigo_repuesto=codigo,
                contenido=contenido,
                nombre_archivo=archivo.filename or "imagen",
                tipo_contenido=archivo.content_type or "image/jpeg",
                subido_por=getattr(request.state, "user_id", ""),
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

    return success_response(
        {
            "imagen_id": imagen.id,
            "repuesto_id": imagen.repuesto_id,
            "url": imagen.url,
            "orden": imagen.orden,
            "subido_en": imagen.subido_en.isoformat(),
        },
        status_code=201,
        request_id=get_request_id(request),
    )


# ── EP-CAT-09 — Eliminar imagen de repuesto ───────────────────────────────────

@router.delete(
    "/repuestos/{codigo}/imagenes/{imagen_id}",
    summary="EP-CAT-09: Eliminar imagen de repuesto",
)
async def eliminar_imagen_repuesto(
    request: Request,
    codigo: str,
    imagen_id: str,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """Solo ADMINISTRADOR y SUPERADMIN."""
    repo = _get_repo(request)
    imagen_repo = _get_imagen_repo(request)
    storage = _get_imagen_storage(request)
    use_case = EliminarImagenUseCase(repo, imagen_repo, storage)

    try:
        await use_case.execute(
            EliminarImagenCommand(
                codigo_repuesto=codigo,
                imagen_id=imagen_id,
                eliminado_por=getattr(request.state, "user_id", ""),
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
    except (ImagenNoEncontradaError, ImagenNoPertenecerAlRepuestoError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "RECURSO_NO_ENCONTRADO",
                str(exc),
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        {"imagen_id": imagen_id, "eliminada": True},
        request_id=get_request_id(request),
    )


# ── EP-CAT-12 — Reordenar imágenes (registrar ANTES que EP-CAT-11 para evitar
#    que "orden" coincida con un imagen_id capturado por el parámetro de ruta) ──

class ReordenarImagenesRequest(BaseModel):
    imagenes_ordenadas: list[str] = Field(
        description="Lista completa de imagen_ids en el nuevo orden deseado. "
                    "Debe contener exactamente los IDs existentes para este repuesto."
    )


@router.put(
    "/repuestos/{codigo}/imagenes/orden",
    summary="EP-CAT-12: Reordenar imágenes de repuesto",
)
async def reordenar_imagenes_repuesto(
    request: Request,
    codigo: str,
    body: ReordenarImagenesRequest,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """
    Solo ADMINISTRADOR y SUPERADMIN.
    Recibe la lista completa de imagen_ids en el orden deseado.
    Validación estricta: debe contener exactamente los IDs existentes del repuesto
    — ni más, ni menos, ni IDs de otro repuesto.
    Si no coincide, responde 422 con el detalle exacto de la discrepancia.
    """
    repo = _get_repo(request)
    imagen_repo = _get_imagen_repo(request)
    use_case = ReordenarImagenesUseCase(repo, imagen_repo)

    try:
        imagenes = await use_case.execute(
            ReordenarImagenesCommand(
                codigo_repuesto=codigo,
                nuevo_orden=body.imagenes_ordenadas,
                reordenado_por=getattr(request.state, "user_id", ""),
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
    except ReordenInvalidoError as exc:
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
            "codigo": codigo,
            "imagenes": [
                {"imagen_id": img.id, "url": img.url, "orden": img.orden}
                for img in imagenes
            ],
        },
        request_id=get_request_id(request),
    )


# ── EP-CAT-11 — Reemplazar imagen de repuesto ────────────────────────────────

@router.put(
    "/repuestos/{codigo}/imagenes/{imagen_id}",
    summary="EP-CAT-11: Reemplazar imagen de repuesto",
)
async def reemplazar_imagen_repuesto(
    request: Request,
    codigo: str,
    imagen_id: str,
    archivo: UploadFile = File(...),
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """
    Solo ADMINISTRADOR y SUPERADMIN.
    Mantiene el mismo id, orden y repuesto_id — solo cambia la referencia en R2.
    Tipos permitidos: image/jpeg, image/png, image/webp. Límite: 5 MB.
    Orden de operaciones: subir nueva → actualizar registro → eliminar objeto anterior.
    """
    if archivo.content_type not in _IMAGEN_TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"Tipo de archivo no permitido: {archivo.content_type!r}. "
                "Permitidos: image/jpeg, image/png, image/webp",
                request_id=get_request_id(request),
            ),
        )

    contenido = await archivo.read()
    if len(contenido) > _IMAGEN_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"El archivo supera el límite de 5 MB ({len(contenido)} bytes recibidos)",
                request_id=get_request_id(request),
            ),
        )

    repo = _get_repo(request)
    imagen_repo = _get_imagen_repo(request)
    storage = _get_imagen_storage(request)
    use_case = ReemplazarImagenUseCase(repo, imagen_repo, storage)

    try:
        imagen = await use_case.execute(
            ReemplazarImagenCommand(
                codigo_repuesto=codigo,
                imagen_id=imagen_id,
                contenido=contenido,
                nombre_archivo=archivo.filename or "imagen",
                tipo_contenido=archivo.content_type or "image/jpeg",
                reemplazado_por=getattr(request.state, "user_id", ""),
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
    except (ImagenNoEncontradaError, ImagenNoPertenecerAlRepuestoError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "RECURSO_NO_ENCONTRADO",
                str(exc),
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        {
            "imagen_id": imagen.id,
            "repuesto_id": imagen.repuesto_id,
            "url": imagen.url,
            "orden": imagen.orden,
            "updated_at": imagen.updated_at.isoformat() if imagen.updated_at else None,
        },
        request_id=get_request_id(request),
    )


# ── Imagen única de repuesto (campo imagen_url — sesión migración Bajaj) ─────
# Distinta de EP-CAT-08/09/11/12 (galería multi-imagen, tabla imagen_repuesto):
# aquí un repuesto tiene una sola foto, key fija repuestos/{codigo}/1.{ext}.
# Ver .doc3/adr-010-imagen-repuesto-campo-unico.md.

_EXTENSION_POR_TIPO = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _get_repuesto_imagen_storage(request: Request):
    return request.app.state.imagen_storage


@router.post(
    "/repuestos/{codigo}/imagen",
    summary="Subir/reemplazar la imagen de catálogo de un repuesto",
)
async def subir_imagen_unica_repuesto(
    request: Request,
    codigo: str,
    archivo: UploadFile = File(...),
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    """
    Solo ADMINISTRADOR y SUPERADMIN. Backend-only (sin UI — queda para sesión
    de frontend aparte). Tipos permitidos: image/jpeg, image/png, image/webp.
    Límite: 5 MB. Reemplaza la imagen anterior (key fija, no se acumulan).
    """
    if archivo.content_type not in _IMAGEN_TIPOS_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"Tipo de archivo no permitido: {archivo.content_type!r}. "
                "Permitidos: image/jpeg, image/png, image/webp",
                request_id=get_request_id(request),
            ),
        )

    contenido = await archivo.read()
    if len(contenido) > _IMAGEN_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"El archivo supera el límite de 5 MB ({len(contenido)} bytes recibidos)",
                request_id=get_request_id(request),
            ),
        )

    repo = _get_repo(request)
    storage = _get_repuesto_imagen_storage(request)
    use_case = SubirImagenRepuestoUseCase(repo, storage)

    try:
        url = await use_case.execute(
            SubirImagenRepuestoCommand(
                codigo=codigo,
                contenido=contenido,
                extension=_EXTENSION_POR_TIPO[archivo.content_type],
                tipo_contenido=archivo.content_type,
                subido_por=getattr(request.state, "user_id", ""),
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

    return success_response(
        {"codigo": codigo, "imagen_url": url},
        request_id=get_request_id(request),
    )


# ── Categorías — CRUD dinámico (sesión 2026-07-03, Pieza C) ──────────────────
# Normaliza repuesto.categoria (varchar) contra la tabla `categoria` real
# (FK ON UPDATE CASCADE, migración 593686985730). GET es público (pobla el
# filtro de categoría en el catálogo); POST/PATCH/DELETE solo ADMIN/SUPERADMIN.

class CategoriaResponse(BaseModel):
    id: str
    nombre: str
    orden: int


class CrearCategoriaRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=50)
    orden: int = 0


class ActualizarCategoriaRequest(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=50)
    orden: Optional[int] = None


@router.get("/categorias", summary="EP-CAT-13: Listar categorías")
async def listar_categorias(request: Request) -> dict[str, Any]:
    """Público — sin auth. Pobla el filtro de categoría del catálogo."""
    repo = _get_categoria_repo(request)
    categorias = await ListarCategoriasUseCase(repo).execute()
    return success_response(
        {"categorias": [
            CategoriaResponse(id=c.id, nombre=c.nombre, orden=c.orden).model_dump()
            for c in categorias
        ]},
        request_id=get_request_id(request),
    )


@router.post(
    "/categorias", status_code=status.HTTP_201_CREATED,
    summary="EP-CAT-14: Crear categoría",
)
async def crear_categoria(
    request: Request,
    body: CrearCategoriaRequest,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    repo = _get_categoria_repo(request)
    try:
        categoria = await CrearCategoriaUseCase(repo).execute(
            CrearCategoriaCommand(nombre=body.nombre, orden=body.orden)
        )
    except CategoriaDuplicadaError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        CategoriaResponse(id=categoria.id, nombre=categoria.nombre, orden=categoria.orden).model_dump(),
        status_code=201, request_id=get_request_id(request),
    )


@router.patch("/categorias/{categoria_id}", summary="EP-CAT-15: Actualizar categoría")
async def actualizar_categoria(
    request: Request,
    categoria_id: str,
    body: ActualizarCategoriaRequest,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> dict[str, Any]:
    repo = _get_categoria_repo(request)
    try:
        categoria = await ActualizarCategoriaUseCase(repo).execute(
            ActualizarCategoriaCommand(categoria_id=categoria_id, nombre=body.nombre, orden=body.orden)
        )
    except CategoriaNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "CATEGORIA_NO_ENCONTRADA", f"Categoría {categoria_id!r} no encontrada",
                request_id=get_request_id(request),
            ),
        )
    except CategoriaDuplicadaError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("VALIDACION_FALLIDA", str(exc), request_id=get_request_id(request)),
        )
    return success_response(
        CategoriaResponse(id=categoria.id, nombre=categoria.nombre, orden=categoria.orden).model_dump(),
        request_id=get_request_id(request),
    )


@router.delete(
    "/categorias/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="EP-CAT-16: Eliminar categoría",
)
async def eliminar_categoria(
    request: Request,
    categoria_id: str,
    _auth: dict = Depends(require_roles("ADMINISTRADOR", "SUPERADMIN")),
) -> Response:
    repo = _get_categoria_repo(request)
    try:
        await EliminarCategoriaUseCase(repo).execute(EliminarCategoriaCommand(categoria_id=categoria_id))
    except CategoriaNoEncontradaError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "CATEGORIA_NO_ENCONTRADA", f"Categoría {categoria_id!r} no encontrada",
                request_id=get_request_id(request),
            ),
        )
    except CategoriaEnUsoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("CATEGORIA_EN_USO", str(exc), request_id=get_request_id(request)),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

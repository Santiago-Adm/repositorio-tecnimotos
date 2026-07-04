"""
Endpoints de administración EP-ADM-01 a EP-ADM-10 (03 §6.6).
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import logging
import sys
from typing import Any, Optional
import jwt

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from api.auth import ADMIN_ROLES, VENDEDOR_ROLES, require_roles, issue_impersonation_token
from api.dependencies import error_response, get_request_id, success_response

router = APIRouter(prefix="/v1/admin", tags=["admin"])

_ROLES_NO_SUPERADMIN = (
    "ADMINISTRADOR", "VENDEDOR", "MECANICO_MASTER", "MECANICO_JUNIOR",
    "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
    "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
)


def _get_parametros(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.shared.infrastructure.repositories.parametros_repository_pg import ParametrosRepositoryPG
        return ParametrosRepositoryPG(db)
    return request.app.state.parametros_service


def _get_taller_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.taller.infrastructure.repositories.taller_repository_pg import TallerRepositoryPG
        return TallerRepositoryPG(db)
    return request.app.state.taller_repo


def _get_user_store(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.shared.infrastructure.repositories.usuario_repository_pg import UsuarioRepositoryPG
        return UsuarioRepositoryPG(db)
    return request.app.state.user_store


def _get_pedido_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.pedidos.infrastructure.repositories.pedido_repository_pg import PedidoRepositoryPG
        return PedidoRepositoryPG(db)
    return request.app.state.pedidos_repo


def _get_catalogo_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.catalogo.infrastructure.repositories.repuesto_repository_pg import RepuestoRepositoryPG
        return RepuestoRepositoryPG(db)
    return request.app.state.catalogo_repo


def _get_stock_repo(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.stock.infrastructure.repositories.stock_repository_pg import StockRepositoryPG
        return StockRepositoryPG(db)
    return request.app.state.stock_repo


# ── EP-ADM-01 — Listar parámetros ────────────────────────────────────────────

@router.get(
    "/parametros",
    summary="EP-ADM-01: Listar parámetros del sistema",
)
async def listar_parametros(
    request: Request,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """SUPERADMIN · ADMINISTRADOR — lista todos los parámetros configurables."""
    svc = _get_parametros(request)
    resultados = await svc.listar()
    parametros = [
        {"clave": r.clave, "valor": r.valor, "modificable_por": r.modificable_por}
        for r in resultados
    ]
    return success_response(
        {"parametros": parametros, "total": len(parametros)},
        request_id=get_request_id(request),
    )


# ── EP-ADM-02 — Actualizar parámetro ─────────────────────────────────────────

class ActualizarParametroRequest(BaseModel):
    valor: Any


@router.patch(
    "/parametros/{clave}",
    summary="EP-ADM-02: Actualizar parámetro del sistema",
)
async def actualizar_parametro(
    request: Request,
    clave: str,
    body: ActualizarParametroRequest,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """
    SUPERADMIN · ADMINISTRADOR — actualiza un parámetro (ABAC-07: solo si modificable_por == ADMINISTRADOR).
    Invalida caché Redis DB-1 (InMemory: actualización directa).
    """
    from src.shared.domain.parametros_port import ParametroNoEncontradoError
    svc = _get_parametros(request)
    try:
        actual = await svc.obtener_parametro(clave)  # verifica que existe + trae modificable_por real
    except ParametroNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "RECURSO_NO_ENCONTRADO", f"Parámetro {clave!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )

    # ABAC-07: solo si modificable_por == ADMINISTRADOR o es SUPERADMIN
    if actual.modificable_por == "SUPERADMIN" and _auth.get("rol") != "SUPERADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                "ACCESO_DENEGADO", f"Solo SUPERADMIN puede modificar {clave!r}",
                request_id=get_request_id(request),
            ),
        )

    await svc.establecer(clave, body.valor)
    return success_response(
        {"clave": clave, "valor": body.valor, "cache_invalidado": True},
        request_id=get_request_id(request),
    )


# ── EP-ADM-03 — Crear vehículo ────────────────────────────────────────────────

class CrearVehiculoRequest(BaseModel):
    universo: str = Field(pattern=r"^(mototaxi|motolineal)$")
    modelo: str = Field(min_length=1, max_length=100)
    año: int = Field(ge=1990, le=2100)
    cliente_id: Optional[str] = None
    placa: Optional[str] = None


@router.post(
    "/vehiculos",
    status_code=status.HTTP_201_CREATED,
    summary="EP-ADM-03: Registrar vehículo",
    tags=["vehiculos"],
)
async def crear_vehiculo(
    request: Request,
    body: CrearVehiculoRequest,
    _auth: dict = Depends(require_roles(*VENDEDOR_ROLES)),
) -> dict[str, Any]:
    """SUPERADMIN · ADMINISTRADOR · VENDEDOR — registra un vehículo en el sistema."""
    from src.taller.domain.models.orden_trabajo import Vehiculo
    repo = _get_taller_repo(request)
    vehiculo = Vehiculo(
        universo=body.universo,
        modelo=body.modelo,
        año=body.año,
        cliente_id=body.cliente_id,
        placa=body.placa,
    )
    await repo.guardar_vehiculo(vehiculo)
    return success_response(
        {
            "vehiculo_id": vehiculo.id,
            "universo": vehiculo.universo,
            "modelo": vehiculo.modelo,
            "año": vehiculo.año,
            "placa": vehiculo.placa,
            "cliente_id": vehiculo.cliente_id,
        },
        status_code=201,
        request_id=get_request_id(request),
    )


# ── EP-ADM-04 — Crear mecánico ────────────────────────────────────────────────

class CrearMecanicoRequest(BaseModel):
    usuario_id: str = Field(min_length=1)
    nivel: str = Field(pattern=r"^(MASTER|JUNIOR)$")
    supervisor_id: Optional[str] = None


@router.post(
    "/mecanicos",
    status_code=status.HTTP_201_CREATED,
    summary="EP-ADM-04: Registrar mecánico",
    tags=["mecanicos"],
)
async def crear_mecanico(
    request: Request,
    body: CrearMecanicoRequest,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """SUPERADMIN · ADMINISTRADOR — registra un mecánico en el sistema."""
    from src.taller.domain.models.orden_trabajo import Mecanico, NivelMecanico
    repo = _get_taller_repo(request)
    nivel = NivelMecanico.MASTER if body.nivel == "MASTER" else NivelMecanico.JUNIOR
    mecanico = Mecanico(
        usuario_id=body.usuario_id,
        nivel=nivel,
        supervisor_id=body.supervisor_id,
    )
    await repo.guardar_mecanico(mecanico)
    return success_response(
        {
            "mecanico_id": mecanico.id,
            "usuario_id": mecanico.usuario_id,
            "nivel": mecanico.nivel.value,
            "supervisor_id": mecanico.supervisor_id,
            "disponible": mecanico.disponible,
        },
        status_code=201,
        request_id=get_request_id(request),
    )


# ── EP-ADM-12 — Listar mecánicos disponibles ─────────────────────────────────

@router.get(
    "/mecanicos",
    summary="EP-ADM-12: Listar mecánicos disponibles",
    tags=["mecanicos"],
)
async def listar_mecanicos(
    request: Request,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """SUPERADMIN · ADMINISTRADOR — lista mecánicos disponibles con su nombre
    real (join con usuario), usada por el filtro 'mecánico asignado' del panel BI (ADR-015)."""
    taller_repo = _get_taller_repo(request)
    user_store = _get_user_store(request)
    mecanicos = await taller_repo.listar_mecanicos_disponibles()
    resultado = []
    for m in mecanicos:
        usuario = await user_store.obtener_por_id(m.usuario_id)
        resultado.append({
            "mecanico_id": m.id,
            "usuario_id": m.usuario_id,
            "nombre": usuario.nombre if usuario else m.usuario_id,
            "nivel": m.nivel.value,
            "disponible": m.disponible,
        })
    return success_response(
        {"mecanicos": resultado, "total": len(resultado)},
        request_id=get_request_id(request),
    )


# ── EP-ADM-05 — Crear usuario ─────────────────────────────────────────────────

_ROLES_CLIENTE = {
    "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
    "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
}


class CrearUsuarioRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    nombre: str = Field(min_length=1, max_length=200)
    rol: str
    password: str = Field(min_length=8)
    # Requerido y debe ser True para roles CLIENTE_* — 08 §8.1 Legal (Ley N.° 29733)
    consentimiento_privacidad: bool = Field(default=False)


_ROLES_VALIDOS = {
    "ADMINISTRADOR", "VENDEDOR", "MECANICO_MASTER", "MECANICO_JUNIOR",
    "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
    "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
}


@router.post(
    "/usuarios",
    status_code=status.HTTP_201_CREATED,
    summary="EP-ADM-05: Crear usuario",
    tags=["usuarios"],
)
async def crear_usuario(
    request: Request,
    body: CrearUsuarioRequest,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """
    SUPERADMIN · ADMINISTRADOR — crea usuario.
    No puede crear SUPERADMIN (03 §6.6).
    """
    if body.rol not in _ROLES_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"Rol {body.rol!r} inválido o no autorizado en este endpoint",
                request_id=get_request_id(request),
            ),
        )

    # Ley N.° 29733: consentimiento explícito requerido para datos personales de clientes
    if body.rol in _ROLES_CLIENTE and not body.consentimiento_privacidad:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                "consentimiento_privacidad debe ser true para roles de cliente (Ley N.° 29733)",
                request_id=get_request_id(request),
            ),
        )

    user_store = _get_user_store(request)
    try:
        user = await user_store.crear_usuario(
            email=body.email,
            nombre=body.nombre,
            rol=body.rol,
            password=body.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(
                "VALIDACION_FALLIDA", str(exc),
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        {
            "usuario_id": user.usuario_id,
            "email": user.email,
            "nombre": user.nombre,
            "rol": user.rol,
            "variante_tema": user.variante_tema,
        },
        status_code=201,
        request_id=get_request_id(request),
    )


# ── EP-ADM-06 — Listar cuentas pendientes de revisión ────────────────────────

@router.get(
    "/usuarios/pendientes",
    summary="EP-ADM-06: Listar cuentas pendientes de aprobación",
    tags=["usuarios"],
)
async def listar_usuarios_pendientes(
    request: Request,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """SUPERADMIN · ADMINISTRADOR — lista cuentas en PENDIENTE_DOCUMENTOS o EN_REVISION."""
    user_store = _get_user_store(request)
    pendientes = await user_store.listar_pendientes()
    return success_response(
        {
            "total": len(pendientes),
            "usuarios": [
                {
                    "usuario_id": u.usuario_id,
                    "email": u.email,
                    "nombre": u.nombre,
                    "rol": u.rol,
                    "estado_cuenta": u.estado_cuenta,
                    "documentos": [
                        {"tipo": d.tipo, "url": d.url} for d in u.documentos
                    ],
                }
                for u in pendientes
            ],
        },
        request_id=get_request_id(request),
    )


# ── EP-ADM-07 — Aprobar cuenta ────────────────────────────────────────────────

@router.post(
    "/usuarios/{usuario_id}/aprobar",
    summary="EP-ADM-07: Aprobar cuenta pendiente",
    tags=["usuarios"],
)
async def aprobar_cuenta(
    request: Request,
    usuario_id: str,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """SUPERADMIN · ADMINISTRADOR — pasa cuenta a ACTIVO."""
    user_store = _get_user_store(request)
    user = await user_store.aprobar_cuenta(usuario_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "RECURSO_NO_ENCONTRADO",
                f"Usuario {usuario_id!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    return success_response(
        {
            "usuario_id": user.usuario_id,
            "email": user.email,
            "estado_cuenta": user.estado_cuenta,
            "mensaje": "Cuenta aprobada. El usuario puede iniciar sesión.",
        },
        request_id=get_request_id(request),
    )


# ── EP-ADM-08 — Rechazar cuenta ───────────────────────────────────────────────

class RechazarCuentaRequest(BaseModel):
    motivo_rechazo: str = Field(min_length=10, max_length=500)


@router.post(
    "/usuarios/{usuario_id}/rechazar",
    summary="EP-ADM-08: Rechazar cuenta pendiente",
    tags=["usuarios"],
)
async def rechazar_cuenta(
    request: Request,
    usuario_id: str,
    body: RechazarCuentaRequest,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """SUPERADMIN · ADMINISTRADOR — pasa cuenta a RECHAZADO con motivo."""
    user_store = _get_user_store(request)
    user = await user_store.rechazar_cuenta(usuario_id, body.motivo_rechazo)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "RECURSO_NO_ENCONTRADO",
                f"Usuario {usuario_id!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    return success_response(
        {
            "usuario_id": user.usuario_id,
            "estado_cuenta": user.estado_cuenta,
            "motivo_rechazo": user.motivo_rechazo,
            "mensaje": "Cuenta rechazada. El usuario no podrá iniciar sesión.",
        },
        request_id=get_request_id(request),
    )


# ── EP-ADM-09 — Listado general de usuarios ───────────────────────────────────

@router.get(
    "/usuarios",
    summary="EP-ADM-09: Listado general de usuarios",
    tags=["usuarios"],
)
async def listar_usuarios(
    request: Request,
    rol: Optional[str] = Query(default=None, description="Filtrar por rol exacto"),
    estado: Optional[str] = Query(default=None, description="Filtrar por estado_cuenta"),
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """
    SUPERADMIN · ADMINISTRADOR — lista todos los usuarios (cualquier estado_cuenta).
    Diferente de EP-ADM-06 que solo lista PENDIENTE_DOCUMENTOS/EN_REVISION.
    Filtros opcionales: rol (exacto) y estado (exacto).
    """
    user_store = _get_user_store(request)
    todos: list = await user_store.listar()
    if rol:
        todos = [u for u in todos if u.rol == rol]
    if estado:
        todos = [u for u in todos if u.estado_cuenta == estado]
    return success_response(
        {
            "total": len(todos),
            "usuarios": [
                {
                    "usuario_id": u.usuario_id,
                    "email": u.email,
                    "nombre": u.nombre,
                    "rol": u.rol,
                    "estado_cuenta": u.estado_cuenta,
                    "variante_tema": u.variante_tema,
                }
                for u in todos
            ],
        },
        request_id=get_request_id(request),
    )


# ── EP-ADM-10 — Métricas de negocio agregadas ────────────────────────────────

@router.get(
    "/metricas-negocio",
    summary="EP-ADM-10: Métricas de negocio agregadas",
)
async def metricas_negocio(
    request: Request,
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    categoria: Optional[str] = None,
    universo: Optional[str] = None,
    mecanico_id: Optional[str] = None,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """
    SUPERADMIN · ADMINISTRADOR — agrega métricas operativas del negocio.

    ADR-015: "OT activa" ya no es una regla fija — se lee de
    `taller.ot_activa.estados`/`taller.ot_activa.dias_maximo` en
    parametros_sistema, editable desde GET/PATCH /v1/admin/parametros.

    Período de ingresos: `desde`/`hasta` (ISO date, ej. 2026-07-01) — rango
    libre, cálculo on-demand, sin agregación fija (ADR-015). Sin params,
    mantiene el comportamiento anterior (mes calendario actual) — retro-
    compatible con cualquier consumidor existente.

    Filtros avanzados (Pieza 1, panel BI): `categoria`/`universo` acotan
    `repuestos_bajo_umbral` a los repuestos reales que cumplen ambos;
    `mecanico_id` acota `ots_activas` a las OTs de ese mecánico
    (master o junior). Todos opcionales — sin ellos, comportamiento agregado
    de siempre.
    """
    from src.taller.domain.services.ot_activa_service import es_ot_activa, obtener_config_ot_activa
    from src.catalogo.domain.models.repuesto import UniversoRepuesto

    taller_repo = _get_taller_repo(request)
    pedido_repo = _get_pedido_repo(request)
    stock_repo = _get_stock_repo(request)
    parametros_svc = _get_parametros(request)

    _ESTADOS_PEDIDO_ACTIVOS = {"BORRADOR", "CONFIRMADO", "EN_PREPARACION"}

    ots = await taller_repo.listar_ots()
    pedidos = await pedido_repo.listar_todos()
    stocks = await stock_repo.listar_todos()
    comprobantes = await pedido_repo.listar_comprobantes()
    config_ot_activa = await obtener_config_ot_activa(parametros_svc)

    ahora = datetime.now(timezone.utc)
    if desde:
        rango_desde = datetime.fromisoformat(desde).replace(tzinfo=timezone.utc)
    else:
        rango_desde = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if hasta:
        rango_hasta = datetime.fromisoformat(hasta).replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
    else:
        rango_hasta = ahora
    hoy_fecha = ahora.date()

    ots_filtradas = ots
    if mecanico_id:
        ots_filtradas = [
            ot for ot in ots_filtradas
            if ot.mecanico_master_id == mecanico_id or ot.mecanico_junior_id == mecanico_id
        ]
    ots_activas = sum(1 for ot in ots_filtradas if es_ot_activa(ot, config_ot_activa, ahora))

    pedidos_dia = sum(
        1 for p in pedidos
        if p.estado.value in _ESTADOS_PEDIDO_ACTIVOS and p.created_at.date() == hoy_fecha
    )

    stocks_filtrados = stocks
    if categoria or universo:
        catalogo_repo = _get_catalogo_repo(request)
        universos = [UniversoRepuesto(universo)] if universo else list(UniversoRepuesto)
        repuestos_por_codigo = {}
        for u in universos:
            for r in await catalogo_repo.buscar(universo=u):
                repuestos_por_codigo[r.codigo] = r

        def _coincide(s) -> bool:
            r = repuestos_por_codigo.get(s.codigo)
            if r is None:
                return False
            if categoria and r.categoria != categoria.strip().lower():
                return False
            return True

        stocks_filtrados = [s for s in stocks_filtrados if _coincide(s)]

    repuestos_bajo_umbral = sum(1 for s in stocks_filtrados if s.esta_bajo_umbral())
    suma_comprobantes_periodo = sum(
        c.monto for c in comprobantes
        if c.estado.value == "EMITIDO" and rango_desde <= c.created_at <= rango_hasta
    )

    return success_response(
        {
            "ots_activas": ots_activas,
            "pedidos_activos_hoy": pedidos_dia,
            "repuestos_bajo_umbral": repuestos_bajo_umbral,
            "comprobantes_emitidos_periodo": float(suma_comprobantes_periodo),
            "periodo_comprobantes": {
                "desde": rango_desde.date().isoformat(),
                "hasta": rango_hasta.date().isoformat(),
            },
        },
        request_id=get_request_id(request),
    )


# ── EP-ADM-11 — Métricas operacionales agregadas ──────────────────────────────

class MetricasOperacionalesResponse(BaseModel):
    rotacion_stock: float
    margen_promedio: float
    tasa_conversion: float


@router.get(
    "/metricas",
    summary="EP-ADM-11: Métricas operacionales agregadas",
    response_model=dict[str, Any],
)
async def metricas_operacionales(
    request: Request,
    _auth: dict = Depends(require_roles(*ADMIN_ROLES)),
) -> dict[str, Any]:
    """
    SUPERADMIN · ADMINISTRADOR — calcula y expone las métricas operacionales.
    Rotación de stock, margen promedio y tasa de conversión.
    """
    db = getattr(request.state, "db", None)

    total_entradas = 0
    entradas_con_ot = 0
    total_stock_disponible = 0
    unidades_vendidas_30d = 0
    margen_promedio = 0.0

    if db is not None:
        from sqlalchemy import select, func, and_
        from datetime import datetime, timezone, timedelta
        from src.taller.infrastructure.repositories.models.taller_models import EntradaModel
        from src.stock.infrastructure.repositories.models.stock_model import StockRepuestoModel, MovimientoStockModel, ReabastecimientoItemModel
        from src.catalogo.infrastructure.repositories.models.repuesto_model import RepuestoModel
        from src.shared.infrastructure.fernet import decrypt

        # 1. Tasa de conversión
        total_entradas = await db.scalar(select(func.count(EntradaModel.id))) or 0
        entradas_con_ot = await db.scalar(
            select(func.count(EntradaModel.id)).where(EntradaModel.orden_trabajo_id.isnot(None))
        ) or 0

        # 2. Rotación de stock
        limite_30d = datetime.now(timezone.utc) - timedelta(days=30)
        unidades_vendidas_30d = await db.scalar(
            select(func.coalesce(func.sum(MovimientoStockModel.cantidad), 0)).where(
                and_(
                    MovimientoStockModel.tipo_movimiento.in_(["SALIDA_VENTA", "SALIDA_TALLER"]),
                    MovimientoStockModel.timestamp >= limite_30d
                )
            )
        ) or 0
        total_stock_disponible = await db.scalar(
            select(func.coalesce(func.sum(StockRepuestoModel.cantidad_disponible + StockRepuestoModel.cantidad_apartada), 0))
        ) or 0

        # 3. Margen promedio
        repuestos_result = await db.execute(
            select(RepuestoModel.precio_venta, RepuestoModel.precio_costo, RepuestoModel.id).where(RepuestoModel.activo == True)
        )
        repuestos = repuestos_result.all()

        margenes = []
        for precio_venta, precio_costo_cifrado, rep_id in repuestos:
            precio_costo = None
            if precio_costo_cifrado:
                try:
                    precio_costo = Decimal(decrypt(precio_costo_cifrado))
                except Exception:
                    try:
                        precio_costo = Decimal(precio_costo_cifrado)
                    except Exception:
                        pass

            if precio_costo is None:
                latest_item_cifrado = await db.scalar(
                    select(ReabastecimientoItemModel.precio_costo_unitario)
                    .where(ReabastecimientoItemModel.repuesto_id == rep_id)
                    .order_by(ReabastecimientoItemModel.created_at.desc())
                    .limit(1)
                )
                if latest_item_cifrado:
                    try:
                        precio_costo = Decimal(decrypt(latest_item_cifrado))
                    except Exception:
                        try:
                            precio_costo = Decimal(latest_item_cifrado)
                        except Exception:
                            pass

            if precio_costo is None:
                precio_costo = precio_venta * Decimal("0.70")

            if precio_venta > 0:
                margin = (precio_venta - precio_costo) / precio_venta
                margenes.append(margin)

        if margenes:
            margen_promedio = float(sum(margenes) / len(margenes) * 100)
        else:
            margen_promedio = 0.0

    else:
        # InMemory Mode
        from datetime import datetime, timezone, timedelta
        taller_repo = _get_taller_repo(request)
        entradas = list(getattr(taller_repo, "_entradas", {}).values())
        total_entradas = len(entradas)
        entradas_con_ot = sum(1 for e in entradas if e.orden_trabajo_id is not None)

        limite_30d = datetime.now(timezone.utc) - timedelta(days=30)
        stock_repo = _get_stock_repo(request)
        for rep_movs in getattr(stock_repo, "_movimientos", {}).values():
            for m in rep_movs:
                tipo = str(m.tipo_movimiento.value) if hasattr(m.tipo_movimiento, "value") else str(m.tipo_movimiento)
                if tipo in ["SALIDA_VENTA", "SALIDA_TALLER"] and m.timestamp >= limite_30d:
                    unidades_vendidas_30d += m.cantidad

        stocks = list(getattr(stock_repo, "_stocks", {}).values())
        total_stock_disponible = sum(s.cantidad_disponible + s.cantidad_apartada for s in stocks)

        catalogo_repo = request.app.state.catalogo_repo
        repuestos = [r for r in getattr(catalogo_repo, "_store", {}).values() if r.activo]
        margenes = []
        for r in repuestos:
            precio_costo = None
            reabs = list(getattr(stock_repo, "_reabastecimientos", {}).values())
            latest_item = None
            for rb in reabs:
                for item in rb.items:
                    if item.repuesto_id == r.id:
                        latest_item = item
            if latest_item is not None:
                precio_costo = latest_item.precio_costo_unitario

            if precio_costo is None:
                precio_costo = r.precio_venta * Decimal("0.70")

            if r.precio_venta > 0:
                margin = (r.precio_venta - precio_costo) / r.precio_venta
                margenes.append(margin)

        if margenes:
            margen_promedio = float(sum(margenes) / len(margenes) * 100)
        else:
            margen_promedio = 0.0

    rotacion_stock = (unidades_vendidas_30d / total_stock_disponible) if total_stock_disponible > 0 else 0.0
    tasa_conversion = (entradas_con_ot / total_entradas * 100) if total_entradas > 0 else 0.0

    return success_response(
        {
            "rotacion_stock": round(float(rotacion_stock), 2),
            "margen_promedio": round(float(margen_promedio), 2),
            "tasa_conversion": round(float(tasa_conversion), 2),
        },
        request_id=get_request_id(request),
    )


class ImpersonateRequest(BaseModel):
    user_id: str


def _log_impersonation_event(
    event: str,
    admin_id: str,
    target_user_id: str,
    client_ip: str,
    status_str: str,
) -> None:
    """Emite un log JSON estructurado al sys.stdout de forma inmediata (CT-8)."""
    tz_lima = timezone(timedelta(hours=-5))
    timestamp = datetime.now(tz_lima).isoformat()
    log_data = {
        "event": event,
        "admin_id": admin_id,
        "target_user_id": target_user_id,
        "client_ip": client_ip,
        "status": status_str,
        "timestamp": timestamp,
    }
    sys.stdout.write(json.dumps(log_data) + "\n")
    sys.stdout.flush()


@router.post(
    "/impersonate",
    summary="EP-ADM-12: Suplantar identidad de un usuario (Impersonate)",
)
async def impersonate(
    request: Request,
    body: ImpersonateRequest,
    _auth: dict = Depends(require_roles("SUPERADMIN")),
) -> dict[str, Any]:
    """
    SUPERADMIN — Emite un token JWT efímero (máx 15 minutos) para suplantar a otro usuario.
    Registra auditoría estructurada en sys.stdout.
    """
    auditor_id = _auth.get("sub", "")
    client_ip = request.client.host if request.client else "unknown"

    # Registrar evento de inicio (CT-8)
    _log_impersonation_event(
        event="USER_IMPERSONATION_STARTED",
        admin_id=auditor_id,
        target_user_id=body.user_id,
        client_ip=client_ip,
        status_str="STARTED",
    )

    db = getattr(request.state, "db", None)
    target_user = None

    # Consultar persistencia en PostgreSQL (SQLAlchemy)
    if db is not None:
        from sqlalchemy import select
        from src.shared.infrastructure.models.usuario_model import UsuarioModel
        try:
            result = await db.execute(select(UsuarioModel).where(UsuarioModel.id == body.user_id))
            target_user = result.scalar_one_or_none()
        except Exception as db_exc:
            logger.error("Error al consultar persistencia PostgreSQL: %s", db_exc)

    # Fallback a almacén en memoria
    if not target_user:
        try:
            user_store = _get_user_store(request)
            target_user = await user_store.obtener_por_id(body.user_id)
        except Exception:
            pass

    if not target_user:
        _log_impersonation_event(
            event="USER_IMPERSONATION_FAILED",
            admin_id=auditor_id,
            target_user_id=body.user_id,
            client_ip=client_ip,
            status_str="REJECTED_USER_NOT_FOUND",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "RECURSO_NO_ENCONTRADO",
                f"Usuario destino {body.user_id!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )

    # Capturar claims y roles originales
    user_id = target_user.id if hasattr(target_user, "id") else target_user.usuario_id
    user_rol = target_user.rol
    user_token_version = getattr(target_user, "token_version", 0)
    user_email = target_user.email
    user_nombre = getattr(target_user, "nombre", "Usuario")

    # Prohibir suplantar a otro SUPERADMIN
    if user_rol == "SUPERADMIN":
        _log_impersonation_event(
            event="USER_IMPERSONATION_FAILED",
            admin_id=auditor_id,
            target_user_id=user_id,
            client_ip=client_ip,
            status_str="REJECTED_SUPERADMIN_IMPERSONATION",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                "ACCESO_DENEGADO",
                "No está permitido suplantar a otro usuario con rol SUPERADMIN",
                request_id=get_request_id(request),
            ),
        )

    # Validar estado de cuenta
    is_active = True
    estado_cuenta = getattr(target_user, "estado_cuenta", "ACTIVO")
    if hasattr(target_user, "activo"):
        is_active = target_user.activo
    if estado_cuenta != "ACTIVO":
        is_active = False

    if not is_active:
        _log_impersonation_event(
            event="USER_IMPERSONATION_FAILED",
            admin_id=auditor_id,
            target_user_id=user_id,
            client_ip=client_ip,
            status_str="REJECTED_USER_INACTIVE",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                "ACCESO_DENEGADO",
                f"No se puede suplantar a un usuario inactivo (estado: {estado_cuenta})",
                request_id=get_request_id(request),
            ),
        )

    # Emitir token de suplantación (Secure by Design - R25, CT-6)
    private_key = getattr(request.app.state, "jwt_private_key", None)
    if not private_key:
        _log_impersonation_event(
            event="USER_IMPERSONATION_FAILED",
            admin_id=auditor_id,
            target_user_id=user_id,
            client_ip=client_ip,
            status_str="REJECTED_KEY_MISSING",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                "ERROR_INTERNO",
                "Servicio de autenticación no configurado con llave privada",
                request_id=get_request_id(request),
            ),
        )

    tz_lima = timezone(timedelta(hours=-5))
    now_lima = datetime.now(tz_lima)
    exp_lima = now_lima + timedelta(minutes=15)

    payload = {
        "sub": user_id,
        "rol": user_rol,
        "role": user_rol,  # Inyectar claim role (DEP-10-001)
        "token_version": user_token_version,
        "iat": int(now_lima.timestamp()),
        "exp": int(exp_lima.timestamp()),  # Límite estricto de 15 minutos en Lima UTC-5
        "is_impersonated": True,
        "auditor_admin_id": auditor_id,  # Inyectar claim auditor_admin_id (DEP-10-001)
        "auditor_id": auditor_id,
    }

    # Generar usando PyJWT
    token = jwt.encode(payload, private_key, algorithm="RS256")

    _log_impersonation_event(
        event="USER_IMPERSONATION_STARTED",
        admin_id=auditor_id,
        target_user_id=user_id,
        client_ip=client_ip,
        status_str="SUCCESS",
    )

    return success_response(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 900,
            "user": {
                "usuario_id": user_id,
                "email": user_email,
                "nombre": user_nombre,
                "rol": user_rol,
            },
        },
        request_id=get_request_id(request),
    )

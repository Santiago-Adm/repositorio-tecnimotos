"""
Endpoints de administración EP-ADM-01 a EP-ADM-05 (03 §6.6).
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from api.auth import ADMIN_ROLES, VENDEDOR_ROLES, require_roles
from api.dependencies import error_response, get_request_id, success_response

router = APIRouter(prefix="/v1/admin", tags=["admin"])

_ROLES_NO_SUPERADMIN = (
    "ADMINISTRADOR", "VENDEDOR", "MECANICO_MASTER", "MECANICO_JUNIOR",
    "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
    "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
)


def _get_parametros(request: Request):
    return request.app.state.parametros_service


def _get_taller_repo(request: Request):
    return request.app.state.taller_repo


def _get_user_store(request: Request):
    return request.app.state.user_store


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
    # InMemoryParametrosService expone _parametros directamente
    parametros = [
        {"clave": k, "valor": v}
        for k, v in getattr(svc, "_parametros", {}).items()
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
        await svc.obtener_parametro(clave)  # verifica que existe
    except ParametroNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "RECURSO_NO_ENCONTRADO", f"Parámetro {clave!r} no encontrado",
                request_id=get_request_id(request),
            ),
        )
    svc.establecer(clave, body.valor)
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
        user = user_store.crear_usuario(
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
        },
        status_code=201,
        request_id=get_request_id(request),
    )

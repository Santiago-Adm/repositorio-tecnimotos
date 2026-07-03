"""
Endpoints de usuario autenticado — EP-USR-01 (PATCH /v1/usuarios/me/tema).
Permite a cualquier usuario autenticado cambiar su propia preferencia de tema.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from api.auth import ALL_AUTH_ROLES, require_roles
from api.auth_stores import ALL_VARIANTES, variantes_permitidas_para_rol
from api.dependencies import error_response, get_request_id, success_response

router = APIRouter(prefix="/v1/usuarios", tags=["usuarios"])


class ActualizarTemaRequest(BaseModel):
    variante_tema: str


@router.patch(
    "/me/tema",
    summary="EP-USR-01: Actualizar preferencia de tema del usuario autenticado",
)
async def actualizar_tema(
    request: Request,
    body: ActualizarTemaRequest,
    _auth: dict = Depends(require_roles(*ALL_AUTH_ROLES)),
) -> dict[str, Any]:
    """
    Cualquier usuario autenticado — cambia su propia variante_tema.
    Roles internos (SUPERADMIN, ADMINISTRADOR, VENDEDOR, MECANICO_*): solo OSCURO_*.
    Roles CLIENTE_*: solo CLARO_*.
    Cruce de superficie → VALIDACION_FALLIDA 422.
    """
    if body.variante_tema not in ALL_VARIANTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"variante_tema {body.variante_tema!r} no reconocida. "
                f"Valores válidos: {sorted(ALL_VARIANTES)}",
                request_id=get_request_id(request),
            ),
        )

    rol = request.state.user_rol
    permitidas = variantes_permitidas_para_rol(rol)
    if body.variante_tema not in permitidas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"La variante {body.variante_tema!r} no corresponde a la superficie del rol {rol!r}. "
                "Roles internos usan OSCURO_*; roles CLIENTE_* usan CLARO_*.",
                request_id=get_request_id(request),
            ),
        )

    usuario_id = request.state.user_id
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.shared.infrastructure.repositories.usuario_repository_pg import UsuarioRepositoryPG
        user_store = UsuarioRepositoryPG(db)
    else:
        user_store = request.app.state.user_store
    user = await user_store.actualizar_variante_tema(usuario_id, body.variante_tema)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                "RECURSO_NO_ENCONTRADO", "Usuario no encontrado",
                request_id=get_request_id(request),
            ),
        )

    return success_response(
        {"variante_tema": user.variante_tema},
        request_id=get_request_id(request),
    )

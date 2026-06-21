"""
Endpoints de autenticación EP-AUTH-01 a EP-AUTH-04 (03 §6.6, 07 §2).
EP-AUTH-05 (GET /v1/health) vive en api/main.py.

Flujo: login → mfa_session_token → mfa → access_token + refresh_token (cookie) →
       refresh → access_token rotado → logout → sesión revocada.
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from api.auth import ADMIN_ROLES, issue_access_token, require_roles
from api.dependencies import error_response, get_request_id, success_response

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_TOTP_PATTERN = re.compile(r"^[0-9]{6}$")
_REFRESH_COOKIE = "refresh_token"
_REFRESH_MAX_AGE = 7 * 24 * 3600  # 7 días en segundos — 07 §2.1


def _get_user_store(request: Request):
    return request.app.state.user_store


def _get_session_store(request: Request):
    return request.app.state.session_store


def _get_private_key(request: Request) -> str | None:
    return getattr(request.app.state, "jwt_private_key", None)


# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class MfaRequest(BaseModel):
    mfa_session_token: str = Field(min_length=1)
    totp_code: str = Field(pattern=r"^[0-9]{6}$")


# ── EP-AUTH-01 — Login ────────────────────────────────────────────────────────

@router.post(
    "/login",
    summary="EP-AUTH-01: Login con credenciales",
)
async def login(request: Request, body: LoginRequest) -> dict[str, Any]:
    """
    Público — sin token.
    Bloqueo 15 min tras 10 intentos fallidos/IP (07 §2.5).
    InMemory: rate limiting simplificado.
    """
    user_store = _get_user_store(request)
    session_store = _get_session_store(request)

    user = user_store.verificar_credenciales(body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA",
                "Credenciales inválidas",  # mensaje idéntico sin importar qué falló (07 §2.5)
                request_id=get_request_id(request),
            ),
        )

    mfa_token = session_store.crear_mfa_session(user.usuario_id)
    return success_response(
        {"mfa_session_token": mfa_token},
        request_id=get_request_id(request),
    )


# ── EP-AUTH-02 — MFA ──────────────────────────────────────────────────────────

@router.post(
    "/mfa",
    summary="EP-AUTH-02: Verificar MFA y obtener tokens",
)
async def mfa(request: Request, body: MfaRequest, response: Response) -> dict[str, Any]:
    """
    Semi-público — requiere mfa_session_token válido (TTL 5 min — 07 §2.4).
    En InMemory acepta cualquier código 6 dígitos.
    """
    session_store = _get_session_store(request)
    user_store = _get_user_store(request)
    private_key = _get_private_key(request)

    usuario_id = session_store.verificar_mfa(body.mfa_session_token, body.totp_code)
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA",
                "Token MFA inválido, expirado o código incorrecto",
                request_id=get_request_id(request),
            ),
        )

    user = user_store.obtener_por_id(usuario_id)
    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA", "Usuario inactivo",
                request_id=get_request_id(request),
            ),
        )

    if not private_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                "ERROR_INTERNO", "Clave privada JWT no configurada",
                request_id=get_request_id(request),
            ),
        )

    access_token = issue_access_token(private_key, user.usuario_id, user.rol, user.token_version)
    _session_id, refresh_raw = session_store.crear_sesion(user.usuario_id)

    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_raw,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=_REFRESH_MAX_AGE,
    )

    return success_response(
        {"access_token": access_token, "token_type": "bearer"},
        request_id=get_request_id(request),
    )


# ── EP-AUTH-03 — Refresh ──────────────────────────────────────────────────────

@router.post(
    "/refresh",
    summary="EP-AUTH-03: Rotar refresh token",
)
async def refresh(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
) -> dict[str, Any]:
    """
    Semi-público — requiere cookie refresh_token válido.
    Replay detection: reuso invalida familia completa (07 §2.3 Escenario 2).
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA", "Refresh token requerido",
                request_id=get_request_id(request),
            ),
        )

    session_store = _get_session_store(request)
    user_store = _get_user_store(request)
    private_key = _get_private_key(request)

    resultado = session_store.rotar_refresh(refresh_token)
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA", "Refresh token inválido o expirado",
                request_id=get_request_id(request),
            ),
        )

    usuario_id, _session_id, nuevo_refresh = resultado
    user = user_store.obtener_por_id(usuario_id)
    if not user or not user.activo or not private_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA", "Usuario inactivo o configuración inválida",
                request_id=get_request_id(request),
            ),
        )

    access_token = issue_access_token(private_key, user.usuario_id, user.rol, user.token_version)

    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=nuevo_refresh,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=_REFRESH_MAX_AGE,
    )

    return success_response(
        {"access_token": access_token, "token_type": "bearer"},
        request_id=get_request_id(request),
    )


# ── EP-AUTH-04 — Logout ───────────────────────────────────────────────────────

@router.post(
    "/logout",
    summary="EP-AUTH-04: Cerrar sesión",
)
async def logout(
    request: Request,
    response: Response,
    _auth: dict = Depends(require_roles(
        "SUPERADMIN", "ADMINISTRADOR", "VENDEDOR",
        "MECANICO_MASTER", "MECANICO_JUNIOR",
        "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
        "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
    )),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
) -> dict[str, Any]:
    """Todos autenticados — revoca la sesión y elimina cookie (07 §2.3 Escenario 1)."""
    session_store = _get_session_store(request)
    if refresh_token:
        session_store.revocar_por_refresh(refresh_token)
    response.delete_cookie(key=_REFRESH_COOKIE)
    return success_response(
        {"mensaje": "Sesión cerrada correctamente"},
        request_id=get_request_id(request),
    )

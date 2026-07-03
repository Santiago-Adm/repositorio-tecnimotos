"""
Autenticación JWT RS256 y autorización RBAC (07 §2, §3.2).
La verificación de rol vive aquí — nunca dentro de los use cases.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# Conjuntos de roles — 03 §6 · 07 §3.1 lista cerrada
ADMIN_ROLES = ("SUPERADMIN", "ADMINISTRADOR")
VENDEDOR_ROLES = (*ADMIN_ROLES, "VENDEDOR")
MECANICO_ROLES = (*ADMIN_ROLES, "MECANICO_MASTER")
MECANICO_JUNIOR_ROLES = (*MECANICO_ROLES, "MECANICO_JUNIOR")
INTERNO_ROLES = (*ADMIN_ROLES, "VENDEDOR", "MECANICO_MASTER", "MECANICO_JUNIOR")
TAL_VENDEDOR_ROLES = (*ADMIN_ROLES, "VENDEDOR", "MECANICO_MASTER")
CLIENTE_ROLES = (
    "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
    "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
)
ALL_AUTH_ROLES = (*INTERNO_ROLES, *CLIENTE_ROLES)


def _public_key(request: Request) -> str | None:
    return getattr(request.app.state, "jwt_public_key", None)


def issue_access_token(private_key: str, user_id: str, rol: str, token_version: int = 0) -> str:
    """Emite JWT RS256 de acceso (15 minutos — 07 §2.1)."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "rol": rol,
            "token_version": token_version,
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        private_key,
        algorithm="RS256",
    )


def verify_token(token: str, public_key: str) -> dict[str, Any]:
    """Verifica firma RS256 y retorna payload. Lanza ValueError si inválido."""
    try:
        return jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"require": ["sub", "rol", "exp"]},
        )
    except JWTError as exc:
        raise ValueError(str(exc)) from exc


def require_roles(*roles: str) -> Callable:
    """
    Fábrica de dependencias FastAPI — 07 §3.2 patrón de verificación RBAC.
    Uso: Depends(require_roles("ADMINISTRADOR", "SUPERADMIN"))

    Rechaza con 401 si no hay token o el token es inválido.
    Rechaza con 403 si el rol no está en la lista autorizada.
    Almacena user_id y user_rol en request.state para uso posterior.
    """
    role_set = frozenset(roles)

    async def _checker(request: Request) -> dict[str, Any]:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {
                    "code": "AUTENTICACION_REQUERIDA",
                    "message": "Token Bearer requerido",
                }},
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = auth[7:]
        pub = _public_key(request)
        if not pub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {
                    "code": "AUTENTICACION_REQUERIDA",
                    "message": "Servicio de autenticación no configurado",
                }},
            )
        try:
            payload = verify_token(token, pub)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {
                    "code": "TOKEN_INVALIDO",
                    "message": "Token inválido o expirado",
                }},
                headers={"WWW-Authenticate": "Bearer"},
            )
        rol = payload.get("rol", "")
        if rol not in role_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {
                    "code": "ACCESO_DENEGADO",
                    "message": f"Rol '{rol}' no autorizado para esta operación",
                }},
            )
        request.state.user_id = payload.get("sub", "")
        request.state.user_rol = rol
        return payload

    return _checker


def issue_impersonation_token(private_key: str, user_id: str, rol: str, auditor_id: str, token_version: int = 0) -> str:
    """Emite JWT RS256 de acceso para suplantación (15 minutos) con claims is_impersonated y auditor_id."""
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "rol": rol,
            "token_version": token_version,
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "is_impersonated": True,
            "auditor_id": auditor_id,
        },
        private_key,
        algorithm="RS256",
    )

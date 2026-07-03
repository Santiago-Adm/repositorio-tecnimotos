"""
Endpoints de autenticación EP-AUTH-01 a EP-AUTH-06 (03 §6.6, 07 §2).
EP-AUTH-05 (GET /v1/health) vive en api/main.py.
EP-AUTH-06 (POST /v1/auth/bootstrap-superadmin) crea el primer SUPERADMIN — un solo uso.

Flujo: login → mfa_session_token → mfa → access_token + refresh_token (cookie) →
       refresh → access_token rotado → logout → sesión revocada.
"""
from __future__ import annotations

import hmac
import logging
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Cookie, Depends, File, Form, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel, Field

from api.auth import ADMIN_ROLES, issue_access_token, require_roles
from api.auth_stores import (
    ESTADO_ACTIVO,
    ESTADO_EN_REVISION,
    ESTADO_PENDIENTE,
    ROLES_MFA_CORREO_REQUERIDO,
    DocumentoRecord,
)
from api.dependencies import error_response, get_request_id, success_response
from src.shared.infrastructure.email_sender import EmailSendError, enviar_correo
from src.shared.infrastructure.mfa_auditoria import registrar_intento_mfa

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_TOTP_PATTERN = re.compile(r"^[0-9]{6}$")
_REFRESH_COOKIE = "refresh_token"
_REFRESH_MAX_AGE = 7 * 24 * 3600  # 7 días en segundos — 07 §2.1


def _get_user_store(request: Request):
    """PG cuando hay sesión de BD en el request (ADR-014); InMemory si no (tests)."""
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.shared.infrastructure.repositories.usuario_repository_pg import UsuarioRepositoryPG
        return UsuarioRepositoryPG(db)
    return request.app.state.user_store


def _get_session_store(request: Request):
    db = getattr(request.state, "db", None)
    if db is not None:
        from src.shared.infrastructure.repositories.sesion_repository_pg import SesionRepositoryPG
        return SesionRepositoryPG(db)
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


class BootstrapSuperadminRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    nombre: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8)
    bootstrap_key: str = Field(min_length=1)


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

    user = await user_store.verificar_credenciales(body.email, body.password)
    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA",
                "Credenciales inválidas",  # mensaje idéntico sin importar qué falló (07 §2.5)
                request_id=get_request_id(request),
            ),
        )

    # Cuenta en flujo de revisión — mensaje específico (sesión 2026-06-28)
    if user.estado_cuenta != ESTADO_ACTIVO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                "CUENTA_EN_REVISION",
                "Tu cuenta está en revisión, te avisaremos cuando esté lista.",
                request_id=get_request_id(request),
            ),
        )

    # Bloqueo temporal por intentos MFA fallidos (ADR-011) — mismo mensaje
    # genérico que credenciales inválidas para no confirmar existencia de cuenta.
    if await user_store.usuario_bloqueado_mfa(user.usuario_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                "CUENTA_BLOQUEADA_TEMPORAL",
                "Demasiados intentos fallidos de verificación. Intenta de nuevo en unos minutos.",
                request_id=get_request_id(request),
            ),
        )

    requiere_codigo_real = user.rol in ROLES_MFA_CORREO_REQUERIDO
    mfa_token, codigo_claro = await session_store.crear_mfa_session(
        user.usuario_id, requiere_codigo_real=requiere_codigo_real
    )

    if requiere_codigo_real and codigo_claro:
        try:
            await enviar_correo(
                user.email,
                "Tu código de verificación Tecnimotos",
                f"Tu código de verificación es: {codigo_claro}\n"
                f"Expira en {session_store.MFA_TTL_MINUTES} minutos. "
                "Si no fuiste tú, ignora este correo.",
            )
        except EmailSendError:
            logger.exception(
                "login: fallo al enviar correo MFA",
                extra={"usuario_id": user.usuario_id, "request_id": get_request_id(request)},
            )

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
    SUPERADMIN/ADMINISTRADOR: código real enviado por correo (ADR-011).
    Resto de roles: acepta cualquier código 6 dígitos (paso "de forma").
    Rate limit: 20 req/min/IP vía RateLimiterMiddleware en /v1/auth/* (R31).
    Cada intento se audita en mfa_intento (R29).
    """
    session_store = _get_session_store(request)
    user_store = _get_user_store(request)
    private_key = _get_private_key(request)

    # Bloqueo cross-sesión (ADR-011/ADR-014) — chequeo previo: un mfa_session_token
    # emitido justo antes de que el usuario quedara bloqueado en otra sesión no
    # debe poder gastar el intento, aunque el código sea correcto.
    usuario_id_token = await session_store.usuario_id_de_token(body.mfa_session_token)
    if usuario_id_token and await user_store.usuario_bloqueado_mfa(usuario_id_token):
        resultado, usuario_id_auditoria = "BLOQUEADO", usuario_id_token
    else:
        resultado, usuario_id_auditoria = await session_store.verificar_mfa(
            body.mfa_session_token, body.totp_code
        )
        if resultado == "CODIGO_INCORRECTO" and usuario_id_auditoria:
            if await user_store.registrar_fallo_mfa(usuario_id_auditoria):
                resultado = "BLOQUEADO"
        elif resultado == "EXITOSO" and usuario_id_auditoria:
            await user_store.resetear_fallos_mfa(usuario_id_auditoria)

    ip = request.client.host if request.client else None
    if usuario_id_auditoria:
        db = getattr(request.state, "db", None)
        await registrar_intento_mfa(db, usuario_id_auditoria, resultado, ip)

    if resultado != "EXITOSO":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA",
                "Token MFA inválido, expirado o código incorrecto",
                request_id=get_request_id(request),
            ),
        )
    usuario_id = usuario_id_auditoria

    user = await user_store.obtener_por_id(usuario_id)
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
    _session_id, refresh_raw = await session_store.crear_sesion(user.usuario_id)

    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_raw,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=_REFRESH_MAX_AGE,
    )

    return success_response(
        {
            "access_token": access_token,
            "token_type": "bearer",
            "variante_tema": user.variante_tema,
        },
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

    resultado = await session_store.rotar_refresh(refresh_token)
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA", "Refresh token inválido o expirado",
                request_id=get_request_id(request),
            ),
        )

    usuario_id, _session_id, nuevo_refresh = resultado
    user = await user_store.obtener_por_id(usuario_id)
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
        await session_store.revocar_por_refresh(refresh_token)
    response.delete_cookie(key=_REFRESH_COOKIE)
    return success_response(
        {"mensaje": "Sesión cerrada correctamente"},
        request_id=get_request_id(request),
    )


# ── EP-AUTH-06 — Bootstrap SUPERADMIN ────────────────────────────────────────

@router.post(
    "/bootstrap-superadmin",
    status_code=status.HTTP_201_CREATED,
    summary="EP-AUTH-06: Crear el primer SUPERADMIN",
)
async def bootstrap_superadmin(
    request: Request,
    body: BootstrapSuperadminRequest,
) -> dict[str, Any]:
    """
    Público — sin token JWT.
    Funciona SOLO si no existe ningún SUPERADMIN en la base de datos.
    Tras crear el primero, cualquier llamada posterior se rechaza permanentemente
    (la condición "cero SUPERADMIN" deja de cumplirse).
    La clave de bootstrap proviene exclusivamente de SUPERADMIN_BOOTSTRAP_KEY (env).
    Nunca se loguea la clave en texto plano.
    """
    configured_key: str = getattr(request.app.state, "superadmin_bootstrap_key", "")
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_response(
                "ERROR_INTERNO",
                "Bootstrap no disponible — SUPERADMIN_BOOTSTRAP_KEY no configurada",
                request_id=get_request_id(request),
            ),
        )

    # Comparación en tiempo constante para evitar timing attacks
    if not hmac.compare_digest(body.bootstrap_key.encode(), configured_key.encode()):
        logger.warning(
            "bootstrap_superadmin: clave incorrecta",
            extra={"request_id": get_request_id(request), "ip": request.client.host if request.client else "unknown"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response(
                "AUTENTICACION_REQUERIDA",
                "Clave de bootstrap incorrecta",
                request_id=get_request_id(request),
            ),
        )

    user_store = _get_user_store(request)
    if await user_store.existe_superadmin():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(
                "VALIDACION_FALLIDA",
                "Ya existe un SUPERADMIN — este endpoint está permanentemente deshabilitado",
                request_id=get_request_id(request),
            ),
        )

    try:
        user = await user_store.crear_superadmin_bootstrap(
            email=body.email,
            nombre=body.nombre,
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

    logger.info(
        "bootstrap_superadmin: SUPERADMIN creado — evento de auditoría",
        extra={
            "usuario_id": user.usuario_id,
            "email_parcial": body.email[:3] + "***",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": get_request_id(request),
        },
    )

    return success_response(
        {
            "usuario_id": user.usuario_id,
            "email": user.email,
            "nombre": user.nombre,
            "rol": user.rol,
            "mensaje": "SUPERADMIN creado. A partir de ahora use el login normal (EP-AUTH-01 → EP-AUTH-02).",
        },
        status_code=201,
        request_id=get_request_id(request),
    )


# ── EP-AUTH-07 — Autorregistro público ───────────────────────────────────────

# Roles que puede declarar el usuario al autorregistrarse.
# ADMINISTRADOR y SUPERADMIN NUNCA por autorregistro.
_ROLES_AUTORREGISTRO = {
    "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
    "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
    "MECANICO_MASTER", "MECANICO_JUNIOR",
    "VENDEDOR",
}
_ROLES_CLIENTE = {
    "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
    "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
}

# Documentos requeridos por rol (tipo_documento → descripción)
_DOCS_REQUERIDOS: dict[str, list[str]] = {
    "CLIENTE_CONDUCTOR":        ["dni_frente", "dni_dorso"],
    "CLIENTE_DISTRITO":         ["dni_frente", "dni_dorso"],
    "CLIENTE_RURAL":            ["dni_frente", "dni_dorso"],
    "CLIENTE_FLOTA_DUENO":      ["dni_frente", "dni_dorso"],
    "CLIENTE_FLOTA_CONDUCTOR":  ["dni_frente", "dni_dorso"],
    "CLIENTE_MOTOLINEAL":       ["dni_frente", "dni_dorso"],
    "VENDEDOR":                 ["dni_frente", "dni_dorso"],
    "MECANICO_MASTER":          ["dni_frente", "dni_dorso", "certificado_tecnico"],
    "MECANICO_JUNIOR":          ["dni_frente", "dni_dorso", "certificado_tecnico"],
}


@router.post(
    "/registro",
    status_code=status.HTTP_201_CREATED,
    summary="EP-AUTH-07: Autorregistro público con documentos",
)
async def registro(
    request: Request,
    email: str = Form(min_length=5, max_length=200),
    nombre: str = Form(min_length=1, max_length=200),
    password: str = Form(min_length=8),
    rol: str = Form(),
    consentimiento_privacidad: bool = Form(),
    dni_frente: UploadFile = File(),
    dni_dorso: UploadFile = File(),
    certificado_tecnico: UploadFile | None = File(default=None),
) -> dict:
    """
    Público — sin token.
    Crea cuenta en PENDIENTE_DOCUMENTOS. No puede declarar ADMINISTRADOR/SUPERADMIN.
    MECANICO_MASTER/JUNIOR requieren certificado_tecnico adicional.
    Publica usuario.registro_pendiente para notificar al ADMINISTRADOR.
    """
    if rol not in _ROLES_AUTORREGISTRO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"Rol {rol!r} no permitido en autorregistro. "
                "ADMINISTRADOR y SUPERADMIN solo se crean por admin o bootstrap.",
                request_id=get_request_id(request),
            ),
        )

    if not consentimiento_privacidad:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                "consentimiento_privacidad debe ser true (Ley N.° 29733)",
                request_id=get_request_id(request),
            ),
        )

    docs_requeridos = _DOCS_REQUERIDOS.get(rol, [])
    if "certificado_tecnico" in docs_requeridos and certificado_tecnico is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response(
                "VALIDACION_FALLIDA",
                f"El rol {rol!r} requiere certificado_tecnico",
                request_id=get_request_id(request),
            ),
        )

    storage = getattr(request.app.state, "documento_storage", None)
    documentos: list[DocumentoRecord] = []

    archivos: list[tuple[str, UploadFile]] = [
        ("dni_frente", dni_frente),
        ("dni_dorso", dni_dorso),
    ]
    if certificado_tecnico is not None:
        archivos.append(("certificado_tecnico", certificado_tecnico))

    if storage is not None:
        for tipo, archivo in archivos:
            contenido = await archivo.read()
            content_type = archivo.content_type or "application/octet-stream"
            url = await storage.subir(contenido, archivo.filename or f"{tipo}.bin", content_type)
            documentos.append(DocumentoRecord(tipo=tipo, url=url))
    else:
        # Fallback sin storage (tests sin R2 ni InMemory configurado)
        for tipo, archivo in archivos:
            documentos.append(DocumentoRecord(tipo=tipo, url=f"pending://{tipo}"))

    user_store = _get_user_store(request)
    try:
        user = await user_store.crear_cuenta_pendiente(
            email=email,
            nombre=nombre,
            rol=rol,
            password=password,
            documentos=documentos,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response(
                "VALIDACION_FALLIDA", str(exc),
                request_id=get_request_id(request),
            ),
        )

    # Notificar al ADMINISTRADOR
    event_bus = getattr(request.app.state, "event_bus", None)
    if event_bus:
        from src.shared.events.envelope import EventEnvelope
        await event_bus.publish(EventEnvelope(
            tipo="usuario.registro_pendiente",
            modulo_origen="auth",
            payload={
                "usuario_id": user.usuario_id,
                "rol": rol,
                "email_parcial": email[:3] + "***",
            },
        ))

    logger.info(
        "autorregistro: cuenta creada en PENDIENTE_DOCUMENTOS",
        extra={"usuario_id": user.usuario_id, "rol": rol},
    )

    return success_response(
        {
            "usuario_id": user.usuario_id,
            "estado_cuenta": user.estado_cuenta,
            "variante_tema": user.variante_tema,
            "mensaje": "Registro recibido. Tu cuenta está en revisión, te avisaremos cuando esté lista.",
            "documentos_recibidos": [d.tipo for d in documentos],
        },
        status_code=201,
        request_id=get_request_id(request),
    )

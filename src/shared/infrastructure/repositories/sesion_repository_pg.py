"""
Repositorio PostgreSQL de sesiones y desafíos MFA — ADR-014.
Mismo contrato público que api.auth_stores.InMemorySessionStore para que
api/routes/auth_routes.py no cambie su forma de invocarlo. La diferencia clave
frente a InMemorySessionStore es que aquí el desafío MFA (mfa_session_token,
5 min TTL) se persiste en la tabla `mfa_sesion` en vez de un dict de proceso —
necesario porque login() y mfa() pueden ejecutarse en réplicas/procesos
distintos en producción.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth_stores import (
    _hash_codigo_mfa,
    _verificar_codigo_mfa,
    generar_codigo_mfa,
)
from src.shared.infrastructure.models.usuario_model import MfaSesionModel, SesionModel


class SesionRepositoryPG:
    """Implementación PostgreSQL — mismo contrato que InMemorySessionStore."""

    MFA_TTL_MINUTES = 5
    REFRESH_TTL_DAYS = 7
    MAX_MFA_INTENTOS = 5

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── MFA (desafío de 2 pasos) ──

    async def usuario_id_de_token(self, mfa_token: str) -> Optional[str]:
        """Peek sin mutar — permite al caller chequear bloqueo cross-sesión
        (ADR-011/ADR-014) antes de gastar un intento contra el código."""
        model = await self._session.get(MfaSesionModel, mfa_token)
        return model.usuario_id if model else None

    async def crear_mfa_session(
        self, usuario_id: str, requiere_codigo_real: bool = False
    ) -> tuple[str, Optional[str]]:
        token = str(uuid.uuid4())
        codigo_claro: Optional[str] = None
        codigo_hash: Optional[str] = None
        if requiere_codigo_real:
            codigo_claro = generar_codigo_mfa()
            codigo_hash = _hash_codigo_mfa(codigo_claro)
        model = MfaSesionModel(
            token=token,
            usuario_id=usuario_id,
            expira_en=datetime.now(timezone.utc) + timedelta(minutes=self.MFA_TTL_MINUTES),
            requiere_codigo_real=requiere_codigo_real,
            codigo_hash=codigo_hash,
        )
        self._session.add(model)
        await self._session.flush()
        return token, codigo_claro

    async def verificar_mfa(self, mfa_token: str, totp_code: str) -> tuple[str, Optional[str]]:
        """No verifica bloqueo cross-sesión aquí — eso vive ahora en
        UsuarioRepositoryPG.usuario_bloqueado_mfa (ADR-014), consultado por el
        caller (api/routes/auth_routes.py::mfa()) antes de llamar a este método."""
        model = await self._session.get(MfaSesionModel, mfa_token)
        if not model:
            return "TOKEN_INVALIDO", None

        if model.usado:
            return "TOKEN_INVALIDO", model.usuario_id

        expira_en = model.expira_en
        if isinstance(expira_en, str):
            expira_en = datetime.fromisoformat(expira_en)
        if expira_en.tzinfo is None:
            expira_en = expira_en.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expira_en:
            return "EXPIRADO", model.usuario_id

        if model.intentos_fallidos >= self.MAX_MFA_INTENTOS:
            return "BLOQUEADO", model.usuario_id

        if model.requiere_codigo_real:
            valido = bool(model.codigo_hash) and _verificar_codigo_mfa(totp_code, model.codigo_hash)
        else:
            valido = len(totp_code) == 6 and totp_code.isdigit()

        if not valido:
            model.intentos_fallidos += 1
            await self._session.flush()
            if model.intentos_fallidos >= self.MAX_MFA_INTENTOS:
                return "BLOQUEADO", model.usuario_id
            return "CODIGO_INCORRECTO", model.usuario_id

        model.usado = True
        await self._session.flush()
        return "EXITOSO", model.usuario_id

    # ── Sesiones (refresh token) ──

    def _hash_refresh(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def crear_sesion(self, usuario_id: str) -> tuple[str, str]:
        session_id = str(uuid.uuid4())
        refresh_raw = str(uuid.uuid4())
        model = SesionModel(
            id=session_id,
            usuario_id=usuario_id,
            refresh_token_hash=self._hash_refresh(refresh_raw),
            jti=str(uuid.uuid4()),
            mfa_completado=True,
            estado="ACTIVA",
            expira_en=datetime.now(timezone.utc) + timedelta(days=self.REFRESH_TTL_DAYS),
        )
        self._session.add(model)
        await self._session.flush()
        return session_id, refresh_raw

    async def _obtener_por_refresh(self, refresh_raw: str) -> Optional[SesionModel]:
        h = self._hash_refresh(refresh_raw)
        stmt = select(SesionModel).where(SesionModel.refresh_token_hash == h)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def rotar_refresh(self, refresh_raw: str) -> Optional[tuple[str, str, str]]:
        model = await self._obtener_por_refresh(refresh_raw)
        if not model or model.estado == "REVOCADA":
            return None
        expira_en = model.expira_en
        if isinstance(expira_en, str):
            expira_en = datetime.fromisoformat(expira_en)
        if expira_en.tzinfo is None:
            expira_en = expira_en.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expira_en:
            return None

        nuevo_raw = str(uuid.uuid4())
        model.refresh_token_hash = self._hash_refresh(nuevo_raw)
        await self._session.flush()
        return model.usuario_id, model.id, nuevo_raw

    async def revocar_por_refresh(self, refresh_raw: str) -> bool:
        model = await self._obtener_por_refresh(refresh_raw)
        if not model:
            return False
        model.estado = "REVOCADA"
        await self._session.flush()
        return True

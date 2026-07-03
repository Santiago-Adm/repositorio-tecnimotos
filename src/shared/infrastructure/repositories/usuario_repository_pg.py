"""
Repositorio PostgreSQL de usuarios — ADR-014 (migración auth InMemory -> PG).
Mismo contrato público que api.auth_stores.InMemoryUserStore (mismos nombres
de método, mismo dataclass UsuarioRecord de retorno) para que api/routes/auth_routes.py,
api/routes/admin.py y api/routes/usuarios.py no cambien su forma de invocarlo,
solo agreguen `await` (los métodos de InMemoryUserStore también son async ahora).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth_stores import (
    ESTADO_ACTIVO,
    ESTADO_EN_REVISION,
    ESTADO_PENDIENTE,
    DocumentoRecord,
    UsuarioRecord,
    _hash_password,
    _verify_password,
)
from src.shared.infrastructure.models.usuario_model import DocumentoUsuarioModel, UsuarioModel


class UsuarioRepositoryPG:
    """Implementación PostgreSQL — mismo contrato que InMemoryUserStore."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Lectura ──

    async def buscar_por_email(self, email: str) -> Optional[UsuarioRecord]:
        stmt = select(UsuarioModel).where(UsuarioModel.email == email.lower())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_record(model) if model else None

    async def verificar_credenciales(self, email: str, password: str) -> Optional[UsuarioRecord]:
        user = await self.buscar_por_email(email)
        if user and _verify_password(password, user.password_hash):
            return user
        return None

    async def obtener_por_id(self, uid: str) -> Optional[UsuarioRecord]:
        model = await self._session.get(UsuarioModel, uid)
        return await self._to_record(model) if model else None

    async def listar(self) -> list[UsuarioRecord]:
        result = await self._session.execute(select(UsuarioModel))
        return [await self._to_record(m) for m in result.scalars().all()]

    async def obtener_todos(self) -> list[UsuarioRecord]:
        return await self.listar()

    async def existe_superadmin(self) -> bool:
        stmt = select(UsuarioModel).where(UsuarioModel.rol == "SUPERADMIN")
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def listar_pendientes(self) -> list[UsuarioRecord]:
        stmt = select(UsuarioModel).where(
            or_(
                UsuarioModel.estado_cuenta == ESTADO_PENDIENTE,
                UsuarioModel.estado_cuenta == ESTADO_EN_REVISION,
            )
        )
        result = await self._session.execute(stmt)
        return [await self._to_record(m) for m in result.scalars().all()]

    # ── Escritura ──

    async def crear_usuario(self, email: str, nombre: str, rol: str, password: str) -> UsuarioRecord:
        existente = await self.buscar_por_email(email)
        if existente is not None:
            raise ValueError(f"Email {email!r} ya registrado")
        model = UsuarioModel(
            id=str(uuid.uuid4()),
            email=email.lower(),
            nombre=nombre,
            rol=rol,
            password_hash=_hash_password(password),
            estado_cuenta=ESTADO_ACTIVO,
            variante_tema=_default_variante_tema(rol),
        )
        self._session.add(model)
        await self._session.flush()
        return await self._to_record(model)

    async def crear_superadmin_bootstrap(self, email: str, nombre: str, password: str) -> UsuarioRecord:
        """Crea el primer SUPERADMIN. Solo debe llamarse cuando existe_superadmin() es False."""
        existente = await self.buscar_por_email(email)
        if existente is not None:
            raise ValueError(f"Email {email!r} ya registrado")
        model = UsuarioModel(
            id=str(uuid.uuid4()),
            email=email.lower(),
            nombre=nombre,
            rol="SUPERADMIN",
            password_hash=_hash_password(password),
            estado_cuenta=ESTADO_ACTIVO,
            variante_tema=_default_variante_tema("SUPERADMIN"),
        )
        self._session.add(model)
        await self._session.flush()
        return await self._to_record(model)

    async def crear_cuenta_pendiente(
        self,
        email: str,
        nombre: str,
        rol: str,
        password: str,
        documentos: list[DocumentoRecord] | None = None,
    ) -> UsuarioRecord:
        existente = await self.buscar_por_email(email)
        if existente is not None:
            raise ValueError(f"Email {email!r} ya registrado")
        model = UsuarioModel(
            id=str(uuid.uuid4()),
            email=email.lower(),
            nombre=nombre,
            rol=rol,
            password_hash=_hash_password(password),
            estado_cuenta=ESTADO_PENDIENTE,
            variante_tema=_default_variante_tema(rol),
        )
        self._session.add(model)
        await self._session.flush()
        for doc in documentos or []:
            self._session.add(DocumentoUsuarioModel(
                id=doc.documento_id, usuario_id=model.id, tipo=doc.tipo, url=doc.url,
            ))
        await self._session.flush()
        return await self._to_record(model)

    async def incrementar_token_version(self, uid: str) -> None:
        model = await self._session.get(UsuarioModel, uid)
        if model:
            model.token_version += 1
            await self._session.flush()

    async def aprobar_cuenta(self, usuario_id: str) -> Optional[UsuarioRecord]:
        model = await self._session.get(UsuarioModel, usuario_id)
        if model:
            model.estado_cuenta = ESTADO_ACTIVO
            await self._session.flush()
        return await self._to_record(model) if model else None

    async def rechazar_cuenta(self, usuario_id: str, motivo: str) -> Optional[UsuarioRecord]:
        model = await self._session.get(UsuarioModel, usuario_id)
        if model:
            model.estado_cuenta = "RECHAZADO"
            model.motivo_rechazo = motivo
            await self._session.flush()
        return await self._to_record(model) if model else None

    async def actualizar_variante_tema(self, usuario_id: str, variante: str) -> Optional[UsuarioRecord]:
        model = await self._session.get(UsuarioModel, usuario_id)
        if model:
            model.variante_tema = variante
            await self._session.flush()
        return await self._to_record(model) if model else None

    # ── Bloqueo temporal MFA cross-sesión (ADR-011 + ADR-014) ──
    # Antes vivía en InMemorySessionStore._mfa_fallos_usuario/_mfa_bloqueo (memoria,
    # no sobrevive reinicio/réplicas). Ahora persiste en usuario.mfa_fallos_consecutivos
    # / usuario.mfa_bloqueado_hasta — misma semántica exacta (MFA_LOCKOUT_INTENTOS=5,
    # MFA_LOCKOUT_MINUTOS=15).

    MFA_LOCKOUT_INTENTOS = 5
    MFA_LOCKOUT_MINUTOS = 15

    async def usuario_bloqueado_mfa(self, usuario_id: str) -> Optional[datetime]:
        model = await self._session.get(UsuarioModel, usuario_id)
        if not model or not model.mfa_bloqueado_hasta:
            return None
        hasta = model.mfa_bloqueado_hasta
        if isinstance(hasta, str):
            hasta = datetime.fromisoformat(hasta)
        if hasta.tzinfo is None:
            hasta = hasta.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) < hasta:
            return hasta
        return None

    async def registrar_fallo_mfa(self, usuario_id: str) -> bool:
        """Incrementa el contador de fallos cross-sesión. Retorna True si el
        usuario queda bloqueado tras este fallo."""
        model = await self._session.get(UsuarioModel, usuario_id)
        if not model:
            return False
        model.mfa_fallos_consecutivos += 1
        bloqueado = model.mfa_fallos_consecutivos >= self.MFA_LOCKOUT_INTENTOS
        if bloqueado:
            from datetime import timedelta
            model.mfa_bloqueado_hasta = datetime.now(timezone.utc) + timedelta(minutes=self.MFA_LOCKOUT_MINUTOS)
        await self._session.flush()
        return bloqueado

    async def resetear_fallos_mfa(self, usuario_id: str) -> None:
        model = await self._session.get(UsuarioModel, usuario_id)
        if model:
            model.mfa_fallos_consecutivos = 0
            model.mfa_bloqueado_hasta = None
            await self._session.flush()

    # ── Conversión ──

    async def _to_record(self, model: UsuarioModel) -> UsuarioRecord:
        stmt = select(DocumentoUsuarioModel).where(DocumentoUsuarioModel.usuario_id == model.id)
        result = await self._session.execute(stmt)
        documentos = [
            DocumentoRecord(tipo=d.tipo, url=d.url, documento_id=d.id)
            for d in result.scalars().all()
        ]
        return UsuarioRecord(
            usuario_id=model.id,
            email=model.email,
            nombre=model.nombre,
            rol=model.rol,
            password_hash=model.password_hash,
            token_version=model.token_version,
            activo=model.activo,
            estado_cuenta=model.estado_cuenta,
            motivo_rechazo=model.motivo_rechazo,
            documentos=documentos,
            variante_tema=model.variante_tema,
        )


_ROLES_CLIENTE_TEMA: frozenset[str] = frozenset({
    "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL",
    "CLIENTE_FLOTA_DUENO", "CLIENTE_FLOTA_CONDUCTOR", "CLIENTE_MOTOLINEAL",
})


def _default_variante_tema(rol: str) -> str:
    return "CLARO_ESTANDAR" if rol in _ROLES_CLIENTE_TEMA else "OSCURO_ESTANDAR"

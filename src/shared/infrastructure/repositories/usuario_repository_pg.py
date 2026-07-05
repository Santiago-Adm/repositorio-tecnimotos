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
    _necesita_rehash,
    _verify_password,
)
from src.shared.infrastructure.models.usuario_model import DocumentoUsuarioModel, UsuarioModel
from src.shared.infrastructure.models.usuario_eliminado_model import UsuarioEliminadoModel
from src.shared.infrastructure.fernet import decrypt, encrypt, hash_email


class UsuarioRepositoryPG:
    """Implementación PostgreSQL — mismo contrato que InMemoryUserStore."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Lectura ──

    async def buscar_por_email(self, email: str) -> Optional[UsuarioRecord]:
        stmt = select(UsuarioModel).where(UsuarioModel.email_hash == hash_email(email))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return await self._to_record(model) if model else None

    async def verificar_credenciales(self, email: str, password: str) -> Optional[UsuarioRecord]:
        stmt = select(UsuarioModel).where(UsuarioModel.email_hash == hash_email(email))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model or not _verify_password(password, model.password_hash):
            return None
        if _necesita_rehash(model.password_hash):
            # Migración perezosa PBKDF2 → Argon2id (07 §2.1, hallazgo de la
            # verificación profunda 2026-07-05) — nunca fuerza un reset de
            # contraseña, solo re-hashea con el password ya verificado.
            model.password_hash = _hash_password(password)
            await self._session.flush()
        return await self._to_record(model)

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
            email=encrypt(email.lower()),
            email_hash=hash_email(email),
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
            email=encrypt(email.lower()),
            email_hash=hash_email(email),
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
        estado_inicial: str = ESTADO_PENDIENTE,
    ) -> UsuarioRecord:
        existente = await self.buscar_por_email(email)
        if existente is not None:
            raise ValueError(f"Email {email!r} ya registrado")
        model = UsuarioModel(
            id=str(uuid.uuid4()),
            email=encrypt(email.lower()),
            email_hash=hash_email(email),
            nombre=nombre,
            rol=rol,
            password_hash=_hash_password(password),
            estado_cuenta=estado_inicial,
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

    # ── Gestión real de usuarios (editar/suspender/eliminar) — ADR-016 ──────────

    async def actualizar_usuario(
        self, usuario_id: str, nombre: Optional[str] = None,
        email: Optional[str] = None, rol: Optional[str] = None,
    ) -> Optional[UsuarioRecord]:
        model = await self._session.get(UsuarioModel, usuario_id)
        if not model:
            return None
        if email is not None and hash_email(email) != model.email_hash:
            existente = await self.buscar_por_email(email)
            if existente is not None:
                raise ValueError(f"Email {email!r} ya registrado")
            model.email = encrypt(email.lower())
            model.email_hash = hash_email(email)
        if nombre is not None:
            model.nombre = nombre
        if rol is not None:
            model.rol = rol
        await self._session.flush()
        return await self._to_record(model)

    async def actualizar_estado_activo(self, usuario_id: str, activo: bool) -> Optional[UsuarioRecord]:
        model = await self._session.get(UsuarioModel, usuario_id)
        if model:
            model.activo = activo
            await self._session.flush()
        return await self._to_record(model) if model else None

    async def registrar_eliminacion(
        self, usuario: UsuarioRecord, eliminado_por: str, motivo: Optional[str] = None,
    ) -> None:
        """Snapshot de auditoría (R29) — se inserta ANTES del DELETE físico,
        en la misma transacción (ADR-016)."""
        self._session.add(UsuarioEliminadoModel(
            usuario_id_original=usuario.usuario_id,
            email=usuario.email,
            nombre=usuario.nombre,
            rol=usuario.rol,
            eliminado_por=eliminado_por,
            motivo=motivo,
        ))
        await self._session.flush()

    async def eliminar_usuario(self, usuario_id: str) -> bool:
        model = await self._session.get(UsuarioModel, usuario_id)
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

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
            email=decrypt(model.email),
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

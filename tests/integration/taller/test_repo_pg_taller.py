"""
Tests de integración — TallerRepositoryPG contra PostgreSQL real.
Se salta automáticamente si PostgreSQL no está disponible.

Nota FK: VehiculoModel.cliente_id nullable, MecanicoModel.usuario_id FK→usuario.id.
Para evitar FK hacia usuario, los tests de mecanico crean primero un usuario mínimo.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import text

# Registra UsuarioModel en el metadata compartido (Base) antes de que
# MecanicoModel intente resolver el FK usuario_id → usuario.id
import src.shared.infrastructure.models.usuario_model  # noqa: F401

from src.taller.domain.models.orden_trabajo import (
    EstadoOrdenTrabajo,
    Mecanico,
    ModalidadIntervencion,
    NivelMecanico,
    NivelUrgencia,
    OrdenTrabajo,
    OrdenTrabajoEvento,
    Vehiculo,
)
from src.taller.infrastructure.repositories.taller_repository_pg import TallerRepositoryPG
from tests.integration.conftest_pg import pg_session


@pytest.fixture
async def repo(pg_session):
    return TallerRepositoryPG(pg_session)


@pytest.fixture
async def usuario_id(pg_session) -> str:
    """Crea un usuario mínimo en BD para satisfacer FK de mecanico."""
    import hashlib
    import os
    from src.shared.infrastructure.fernet import encrypt, hash_email
    uid = str(uuid.uuid4())
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", b"test", salt, 100_000)
    pw_hash = salt.hex() + ":" + h.hex()
    email = f"mec-{uid[:8]}@test.test"
    await pg_session.execute(text(
        "INSERT INTO usuario (id, email, email_hash, password_hash, rol) VALUES "
        "(:id, :email, :email_hash, :pw, 'MECANICO_MASTER')"
    ), {"id": uid, "email": encrypt(email), "email_hash": hash_email(email), "pw": pw_hash})
    await pg_session.flush()
    return uid


class TestTallerRepositoryPG:

    async def test_guardar_y_obtener_vehiculo(self, repo, pg_session):
        v = Vehiculo(universo="mototaxi", modelo="Bajaj RE PG", año=2022)
        saved = await repo.guardar_vehiculo(v)
        assert saved.id == v.id

        obtenido = await repo.obtener_vehiculo(v.id)
        assert obtenido is not None
        assert obtenido.modelo == "Bajaj RE PG"
        assert obtenido.universo == "mototaxi"

    async def test_guardar_y_obtener_mecanico(self, repo, usuario_id, pg_session):
        m = Mecanico(usuario_id=usuario_id, nivel=NivelMecanico.MASTER)
        saved = await repo.guardar_mecanico(m)
        assert saved.id == m.id

        obtenido = await repo.obtener_mecanico(m.id)
        assert obtenido is not None
        assert obtenido.nivel == NivelMecanico.MASTER
        assert obtenido.disponible is True

    async def test_actualizar_disponibilidad_mecanico(self, repo, usuario_id, pg_session):
        m = Mecanico(usuario_id=usuario_id, nivel=NivelMecanico.MASTER)
        await repo.guardar_mecanico(m)

        m.disponible = False
        await repo.actualizar_mecanico(m)

        actualizado = await repo.obtener_mecanico(m.id)
        assert actualizado.disponible is False

    async def test_guardar_ot_y_obtener(self, repo, usuario_id, pg_session):
        v = Vehiculo(universo="mototaxi", modelo="Honda CB PG", año=2021)
        await repo.guardar_vehiculo(v)

        m = Mecanico(usuario_id=usuario_id, nivel=NivelMecanico.MASTER)
        await repo.guardar_mecanico(m)

        ot = OrdenTrabajo(
            vehiculo_id=v.id,
            mecanico_master_id=m.id,
            modalidad=ModalidadIntervencion.CORRECTIVO,
            urgencia=NivelUrgencia.ALTA,
        )
        await repo.guardar_ot(ot)

        obtenida = await repo.obtener_ot(ot.id)
        assert obtenida is not None
        assert obtenida.vehiculo_id == v.id
        assert obtenida.estado.value == "ABIERTA"

    async def test_actualizar_estado_ot(self, repo, usuario_id, pg_session):
        v = Vehiculo(universo="motolineal", modelo="Yamaha PG", año=2023)
        await repo.guardar_vehiculo(v)
        m = Mecanico(usuario_id=usuario_id, nivel=NivelMecanico.MASTER)
        await repo.guardar_mecanico(m)

        ot = OrdenTrabajo(
            vehiculo_id=v.id,
            mecanico_master_id=m.id,
            modalidad=ModalidadIntervencion.PREVENTIVO,
            urgencia=NivelUrgencia.BAJA,
        )
        await repo.guardar_ot(ot)

        ot.avanzar_estado(EstadoOrdenTrabajo.LISTA_REPUESTOS)  # ABIERTA → LISTA_REPUESTOS
        await repo.actualizar_ot(ot)

        actualizada = await repo.obtener_ot(ot.id)
        assert actualizada.estado.value == "LISTA_REPUESTOS"

    async def test_listar_mecanicos_disponibles(self, repo, usuario_id, pg_session):
        m = Mecanico(usuario_id=usuario_id, nivel=NivelMecanico.MASTER)
        await repo.guardar_mecanico(m)

        disponibles = await repo.listar_mecanicos_disponibles()
        ids = {x.id for x in disponibles}
        assert m.id in ids

    async def test_listar_ots(self, repo, usuario_id, pg_session):
        v = Vehiculo(universo="mototaxi", modelo="Piaggio PG", año=2020)
        await repo.guardar_vehiculo(v)
        m = Mecanico(usuario_id=usuario_id, nivel=NivelMecanico.MASTER)
        await repo.guardar_mecanico(m)

        ot = OrdenTrabajo(
            vehiculo_id=v.id, mecanico_master_id=m.id,
            modalidad=ModalidadIntervencion.DIAGNOSTICO, urgencia=NivelUrgencia.MEDIA,
        )
        await repo.guardar_ot(ot)

        todos = await repo.listar_ots()
        ids = {o.id for o in todos}
        assert ot.id in ids


class TestOrdenTrabajoEventoPG:
    async def test_registrar_y_listar_eventos_ot(self, repo, usuario_id, pg_session):
        v = Vehiculo(universo="mototaxi", modelo="Bajaj RE PG evento", año=2022)
        await repo.guardar_vehiculo(v)
        m = Mecanico(usuario_id=usuario_id, nivel=NivelMecanico.MASTER)
        await repo.guardar_mecanico(m)
        ot = OrdenTrabajo(
            vehiculo_id=v.id, mecanico_master_id=m.id,
            modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
        )
        await repo.guardar_ot(ot)

        await repo.registrar_evento_ot(OrdenTrabajoEvento(
            ot_id=ot.id, evento="EP-TAL-01-ABRIR",
            estado_anterior="ABIERTA", estado_nuevo="ABIERTA", actor_id="actor-1",
        ))
        await repo.registrar_evento_ot(OrdenTrabajoEvento(
            ot_id=ot.id, evento="EP-TAL-09-CANCELAR",
            estado_anterior="ABIERTA", estado_nuevo="CANCELADA", actor_id="actor-1",
        ))

        eventos = await repo.listar_eventos_ot(ot.id)
        assert [e.evento for e in eventos] == ["EP-TAL-01-ABRIR", "EP-TAL-09-CANCELAR"]
        assert eventos[1].estado_nuevo == "CANCELADA"

"""
Tests de integración contra PostgreSQL real — ADR-016: gestión de usuarios
(editar/suspender/eliminar) y detección real de historial de negocio
(cliente/mecánico) usada para bloquear el DELETE físico con 409.
"""
from __future__ import annotations

import pytest

from src.pedidos.domain.models.pedido import Pedido
from src.pedidos.infrastructure.repositories.models.pedido_models import ClienteModel
from src.pedidos.infrastructure.repositories.pedido_repository_pg import PedidoRepositoryPG
from src.shared.infrastructure.repositories.usuario_repository_pg import UsuarioRepositoryPG
from src.taller.domain.models.orden_trabajo import (
    Mecanico, ModalidadIntervencion, NivelMecanico, NivelUrgencia, OrdenTrabajo,
)
from src.taller.infrastructure.repositories.models.taller_models import MecanicoModel
from src.taller.infrastructure.repositories.taller_repository_pg import TallerRepositoryPG
from tests.integration.conftest_pg import pg_session


@pytest.fixture
async def usuario_repo(pg_session):
    return UsuarioRepositoryPG(pg_session)


@pytest.fixture
async def pedido_repo(pg_session):
    return PedidoRepositoryPG(pg_session)


@pytest.fixture
async def taller_repo(pg_session):
    return TallerRepositoryPG(pg_session)


class TestUsuarioRepositoryPGGestion:
    async def test_crear_cuenta_pendiente_con_estado_inicial_explicito(self, usuario_repo):
        # S3/S5 (FLOTA_DUENO/FLOTA_CONDUCTOR/MOTOLINEAL): la cuenta nace en
        # EN_REVISION, no en ACTIVO — bloqueada en login hasta aprobación real.
        from api.auth_stores import ESTADO_EN_REVISION
        user = await usuario_repo.crear_cuenta_pendiente(
            email="adr-flota-pg@test.com", nombre="Flota Dueno PG", rol="CLIENTE_FLOTA_DUENO",
            password="pass12345", estado_inicial=ESTADO_EN_REVISION,
        )
        assert user.estado_cuenta == ESTADO_EN_REVISION

        recargado = await usuario_repo.obtener_por_id(user.usuario_id)
        assert recargado.estado_cuenta == ESTADO_EN_REVISION

    async def test_actualizar_usuario_nombre_email_rol(self, usuario_repo):
        user = await usuario_repo.crear_usuario(
            email="adr016-edit@test.com", nombre="Original", rol="VENDEDOR", password="pass12345",
        )
        actualizado = await usuario_repo.actualizar_usuario(
            user.usuario_id, nombre="Editado", email="adr016-edit-2@test.com", rol="MECANICO_JUNIOR",
        )
        assert actualizado.nombre == "Editado"
        assert actualizado.email == "adr016-edit-2@test.com"
        assert actualizado.rol == "MECANICO_JUNIOR"

    async def test_actualizar_estado_activo(self, usuario_repo):
        user = await usuario_repo.crear_usuario(
            email="adr016-susp@test.com", nombre="X", rol="VENDEDOR", password="pass12345",
        )
        assert user.activo is True
        suspendido = await usuario_repo.actualizar_estado_activo(user.usuario_id, False)
        assert suspendido.activo is False

    async def test_eliminar_usuario_con_auditoria(self, usuario_repo):
        user = await usuario_repo.crear_usuario(
            email="adr016-del@test.com", nombre="Borrar", rol="VENDEDOR", password="pass12345",
        )
        admin = await usuario_repo.crear_usuario(
            email="adr016-admin-aud@test.com", nombre="Admin", rol="VENDEDOR", password="pass12345",
        )
        await usuario_repo.registrar_eliminacion(user, eliminado_por=admin.usuario_id, motivo="prueba real")
        ok = await usuario_repo.eliminar_usuario(user.usuario_id)
        assert ok is True

        sigue = await usuario_repo.obtener_por_id(user.usuario_id)
        assert sigue is None


class TestHistorialClientePG:
    async def test_obtener_cliente_id_por_usuario_y_sin_actividad(self, usuario_repo, pedido_repo, pg_session):
        user = await usuario_repo.crear_usuario(
            email="adr016-cliente-limpio@test.com", nombre="Cliente Limpio", rol="CLIENTE_CONDUCTOR", password="pass12345",
        )
        pg_session.add(ClienteModel(usuario_id=user.usuario_id, segmento="S1"))
        await pg_session.flush()

        cliente_id = await pedido_repo.obtener_cliente_id_por_usuario(user.usuario_id)
        assert cliente_id is not None
        assert await pedido_repo.tiene_actividad_cliente(cliente_id) is False

    async def test_tiene_actividad_cliente_con_pedido_real(self, usuario_repo, pedido_repo, pg_session):
        user = await usuario_repo.crear_usuario(
            email="adr016-cliente-activo@test.com", nombre="Cliente Activo", rol="CLIENTE_CONDUCTOR", password="pass12345",
        )
        pg_session.add(ClienteModel(usuario_id=user.usuario_id, segmento="S1"))
        await pg_session.flush()
        cliente_id = await pedido_repo.obtener_cliente_id_por_usuario(user.usuario_id)

        pedido = Pedido(canal_origen="presencial", origen_actor="CLIENTE", cliente_id=cliente_id)
        await pedido_repo.guardar(pedido)

        assert await pedido_repo.tiene_actividad_cliente(cliente_id) is True


class TestHistorialMecanicoPG:
    async def test_tiene_actividad_mecanico_con_ot_real(self, usuario_repo, taller_repo, pg_session):
        from src.taller.domain.models.orden_trabajo import Vehiculo

        user = await usuario_repo.crear_usuario(
            email="adr016-mec-activo@test.com", nombre="Mec Activo", rol="MECANICO_JUNIOR", password="pass12345",
        )
        mecanico = Mecanico(usuario_id=user.usuario_id, nivel=NivelMecanico.JUNIOR)
        await taller_repo.guardar_mecanico(mecanico)

        user_master = await usuario_repo.crear_usuario(
            email="adr016-mec-master-pg@test.com", nombre="Mec Master", rol="MECANICO_MASTER", password="pass12345",
        )
        mecanico_master = Mecanico(usuario_id=user_master.usuario_id, nivel=NivelMecanico.MASTER)
        await taller_repo.guardar_mecanico(mecanico_master)

        vehiculo = Vehiculo(universo="motolineal", modelo="Pulsar", año=2020)
        await taller_repo.guardar_vehiculo(vehiculo)

        mecanico_id = await taller_repo.obtener_mecanico_id_por_usuario(user.usuario_id)
        assert mecanico_id == mecanico.id
        assert await taller_repo.tiene_actividad_mecanico(mecanico_id) is False

        ot = OrdenTrabajo(
            vehiculo_id=vehiculo.id, mecanico_master_id=mecanico_master.id, mecanico_junior_id=mecanico_id,
            modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
        )
        await taller_repo.guardar_ot(ot)

        assert await taller_repo.tiene_actividad_mecanico(mecanico_id) is True

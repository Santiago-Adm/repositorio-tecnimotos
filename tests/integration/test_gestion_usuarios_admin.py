"""
Tests de integración — EP-ADM-14/15/16 (editar/suspender/eliminar usuario) +
protección real de roles master (ADR-016).
"""
from __future__ import annotations

import pytest

from tests.integration.conftest import make_test_token


@pytest.fixture
async def usuario_vendedor(app_client):
    r = await app_client.post("/v1/admin/usuarios", json={
        "email": "vend-adr016@test.com", "nombre": "Vend ADR016",
        "rol": "VENDEDOR", "password": "pass12345",
    })
    assert r.status_code == 201
    return r.json()["data"]["usuario_id"]


class TestEditarUsuarioEpAdm14:
    async def test_edita_nombre_email_rol(self, app_client, usuario_vendedor):
        r = await app_client.patch(f"/v1/admin/usuarios/{usuario_vendedor}", json={
            "nombre": "Vend Renombrado", "rol": "MECANICO_JUNIOR",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["nombre"] == "Vend Renombrado"
        assert data["rol"] == "MECANICO_JUNIOR"

    async def test_404_usuario_inexistente(self, app_client):
        r = await app_client.patch("/v1/admin/usuarios/no-existe", json={"nombre": "X"})
        assert r.status_code == 404

    async def test_403_editar_administrador(self, app_client):
        r = await app_client.patch("/v1/admin/usuarios/user-admin-seed", json={"nombre": "X"})
        assert r.status_code == 403

    async def test_403_editar_superadmin(self, app_client):
        token = make_test_token(app_client._test_private_pem, "SUPERADMIN", sub="sup-1")
        r = await app_client.post("/v1/admin/usuarios", json={
            "email": "sup-target@test.com", "nombre": "X", "rol": "VENDEDOR", "password": "pass12345",
        })
        vend_id = r.json()["data"]["usuario_id"]
        # promocionar manualmente a SUPERADMIN vía el store para simular el escenario
        user_store = app_client.app.state.user_store
        await user_store.actualizar_usuario(vend_id, rol="SUPERADMIN")
        r2 = await app_client.patch(f"/v1/admin/usuarios/{vend_id}", json={"nombre": "Y"})
        assert r2.status_code == 403

    async def test_422_rol_destino_invalido(self, app_client, usuario_vendedor):
        r = await app_client.patch(f"/v1/admin/usuarios/{usuario_vendedor}", json={"rol": "ADMINISTRADOR"})
        assert r.status_code == 422

    async def test_rbac_vendedor_bloqueado(self, app_client, usuario_vendedor):
        token = make_test_token(app_client._test_private_pem, "VENDEDOR")
        r = await app_client.patch(
            f"/v1/admin/usuarios/{usuario_vendedor}", json={"nombre": "X"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403


class TestSuspenderUsuarioEpAdm15:
    async def test_suspende_y_bloquea_login(self, app_client, usuario_vendedor):
        r = await app_client.patch(
            f"/v1/admin/usuarios/{usuario_vendedor}/estado", json={"activo": False},
        )
        assert r.status_code == 200
        assert r.json()["data"]["activo"] is False

        r_login = await app_client.post("/v1/auth/login", json={
            "email": "vend-adr016@test.com", "password": "pass12345",
        })
        assert r_login.status_code in (401, 403)

    async def test_reactiva(self, app_client, usuario_vendedor):
        await app_client.patch(f"/v1/admin/usuarios/{usuario_vendedor}/estado", json={"activo": False})
        r = await app_client.patch(f"/v1/admin/usuarios/{usuario_vendedor}/estado", json={"activo": True})
        assert r.status_code == 200
        assert r.json()["data"]["activo"] is True

    async def test_404_usuario_inexistente(self, app_client):
        r = await app_client.patch("/v1/admin/usuarios/no-existe/estado", json={"activo": False})
        assert r.status_code == 404

    async def test_403_suspender_administrador(self, app_client):
        r = await app_client.patch("/v1/admin/usuarios/user-admin-seed/estado", json={"activo": False})
        assert r.status_code == 403

    async def test_rbac_vendedor_bloqueado(self, app_client, usuario_vendedor):
        token = make_test_token(app_client._test_private_pem, "VENDEDOR")
        r = await app_client.patch(
            f"/v1/admin/usuarios/{usuario_vendedor}/estado", json={"activo": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403


class TestEliminarUsuarioEpAdm16:
    async def test_elimina_sin_historial_y_registra_auditoria(self, app_client, usuario_vendedor):
        r = await app_client.delete(f"/v1/admin/usuarios/{usuario_vendedor}?motivo=cuenta+de+prueba")
        assert r.status_code == 200
        assert r.json()["data"]["eliminado"] is True

        # confirma que ya no existe
        r2 = await app_client.patch(f"/v1/admin/usuarios/{usuario_vendedor}", json={"nombre": "X"})
        assert r2.status_code == 404

        # confirma snapshot de auditoría real (InMemory)
        auditoria = app_client.app.state.user_store._eliminados
        encontrado = next(e for e in auditoria if e["usuario_id_original"] == usuario_vendedor)
        assert encontrado["email"] == "vend-adr016@test.com"
        assert encontrado["motivo"] == "cuenta de prueba"

    async def test_404_usuario_inexistente(self, app_client):
        r = await app_client.delete("/v1/admin/usuarios/no-existe")
        assert r.status_code == 404

    async def test_403_eliminar_administrador(self, app_client):
        r = await app_client.delete("/v1/admin/usuarios/user-admin-seed")
        assert r.status_code == 403

    async def test_409_mecanico_con_ot_asignada(self, app_client):
        """Mecánico con OT real asignada — bloqueado con 409 (ADR-016),
        verificable en InMemory porque el vínculo usuario->mecanico existe ahí."""
        from src.taller.domain.models.orden_trabajo import (
            Mecanico, NivelMecanico, ModalidadIntervencion, NivelUrgencia, OrdenTrabajo,
        )
        r = await app_client.post("/v1/admin/usuarios", json={
            "email": "mec-historial@test.com", "nombre": "Mec Historial",
            "rol": "MECANICO_JUNIOR", "password": "pass12345",
        })
        usuario_id = r.json()["data"]["usuario_id"]

        taller_repo = app_client.app.state.taller_repo
        mecanico = Mecanico(usuario_id=usuario_id, nivel=NivelMecanico.JUNIOR)
        await taller_repo.guardar_mecanico(mecanico)
        ot = OrdenTrabajo(
            vehiculo_id="v-hist", mecanico_master_id="mec-otro",
            mecanico_junior_id=mecanico.id,
            modalidad=ModalidadIntervencion.CORRECTIVO, urgencia=NivelUrgencia.ALTA,
        )
        await taller_repo.guardar_ot(ot)

        r_del = await app_client.delete(f"/v1/admin/usuarios/{usuario_id}")
        assert r_del.status_code == 409
        assert r_del.json()["detail"]["error"]["code"] == "USUARIO_CON_HISTORIAL"

        # el usuario sigue existiendo — no se eliminó
        r_check = await app_client.patch(f"/v1/admin/usuarios/{usuario_id}", json={"nombre": "sigue-vivo"})
        assert r_check.status_code == 200

    async def test_rbac_vendedor_bloqueado(self, app_client, usuario_vendedor):
        token = make_test_token(app_client._test_private_pem, "VENDEDOR")
        r = await app_client.delete(
            f"/v1/admin/usuarios/{usuario_vendedor}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403

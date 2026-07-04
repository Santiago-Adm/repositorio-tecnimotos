"""
Tests de integración — CRUD de categorías (EP-CAT-13 a EP-CAT-16, sesión 2026-07-03).
GET público; POST/PATCH/DELETE solo ADMINISTRADOR/SUPERADMIN.
DELETE bloquea (409) si hay repuestos usando la categoría (decisión Sant).
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.catalogo.domain.models.repuesto import Repuesto, UniversoRepuesto
from tests.integration.conftest import make_test_token


class TestListarCategoriasPublico:
    async def test_lista_sin_auth(self, app_client):
        r = await app_client.get("/v1/categorias", headers={})
        assert r.status_code == 200
        nombres = [c["nombre"] for c in r.json()["data"]["categorias"]]
        assert "motor" in nombres
        assert "otro" in nombres
        assert len(nombres) == 9


class TestCrearCategoria:
    async def test_admin_crea_categoria(self, app_client):
        r = await app_client.post("/v1/categorias", json={"nombre": "Iluminación", "orden": 10})
        assert r.status_code == 201, r.text
        assert r.json()["data"]["nombre"] == "iluminación"

        listado = await app_client.get("/v1/categorias")
        nombres = [c["nombre"] for c in listado.json()["data"]["categorias"]]
        assert "iluminación" in nombres

    async def test_crear_duplicada_retorna_409(self, app_client):
        r = await app_client.post("/v1/categorias", json={"nombre": "motor"})
        assert r.status_code == 409

    async def test_vendedor_no_puede_crear(self, app_client):
        token = make_test_token(app_client._test_private_pem, "VENDEDOR")
        r = await app_client.post(
            "/v1/categorias", json={"nombre": "otra"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 403


class TestActualizarCategoria:
    async def test_admin_renombra_categoria(self, app_client):
        crear = await app_client.post("/v1/categorias", json={"nombre": "temporal"})
        cat_id = crear.json()["data"]["id"]

        r = await app_client.patch(f"/v1/categorias/{cat_id}", json={"nombre": "renombrada"})
        assert r.status_code == 200
        assert r.json()["data"]["nombre"] == "renombrada"

    async def test_actualizar_inexistente_404(self, app_client):
        r = await app_client.patch("/v1/categorias/no-existe", json={"nombre": "x"})
        assert r.status_code == 404


class TestEliminarCategoria:
    async def test_eliminar_categoria_sin_uso_exitoso(self, app_client):
        crear = await app_client.post("/v1/categorias", json={"nombre": "sin_uso"})
        cat_id = crear.json()["data"]["id"]

        r = await app_client.delete(f"/v1/categorias/{cat_id}")
        assert r.status_code == 204

        listado = await app_client.get("/v1/categorias")
        nombres = [c["nombre"] for c in listado.json()["data"]["categorias"]]
        assert "sin_uso" not in nombres

    async def test_eliminar_categoria_en_uso_bloqueado_409(self, app_client):
        crear = await app_client.post("/v1/categorias", json={"nombre": "en_uso_test"})
        cat_id = crear.json()["data"]["id"]

        repo = app_client.app.state.catalogo_repo
        repuesto = Repuesto(
            codigo="CAT-TEST-001", nombre="Repuesto de prueba",
            universo=UniversoRepuesto.MOTOLINEAL, modelo="X", año=2020,
            categoria="en_uso_test", precio_venta=Decimal("10.00"),
        )
        await repo.guardar(repuesto)

        r = await app_client.delete(f"/v1/categorias/{cat_id}")
        assert r.status_code == 409
        assert "en_uso_test" in r.json()["detail"]["error"]["message"]


class TestCrearRepuestoValidaCategoriaReal:
    async def test_crear_repuesto_con_categoria_inexistente_422(self, app_client):
        r = await app_client.post("/v1/repuestos", json={
            "codigo": "CAT-VAL-001", "nombre": "X", "universo": "motolineal",
            "modelo": "X", "año": 2020, "categoria": "no_existe_esta_categoria",
            "precio_venta": "10.00",
        })
        assert r.status_code == 422
        assert r.json()["detail"]["error"]["code"] == "CATEGORIA_NO_ENCONTRADA"

    async def test_crear_repuesto_con_categoria_real_exitoso(self, app_client):
        r = await app_client.post("/v1/repuestos", json={
            "codigo": "CAT-VAL-002", "nombre": "X", "universo": "motolineal",
            "modelo": "X", "año": 2020, "categoria": "motor",
            "precio_venta": "10.00",
        })
        assert r.status_code == 201, r.text

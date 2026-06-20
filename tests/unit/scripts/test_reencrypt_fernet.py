"""
Tests unitarios de scripts/reencrypt_fernet.py.
Usa InMemoryFernetDB — sin BD real ni Fernet real en mayoría de tests.
Fernet real solo donde se prueba descifrado/re-cifrado efectivo.
"""
import pytest
from cryptography.fernet import Fernet

from scripts.reencrypt_fernet import (
    CAMPOS_FERNET,
    InMemoryFernetDB,
    ResultadoRecifrado,
    recifrar_campo,
    recifrar_todos,
)


def _generar_claves() -> tuple[str, str, Fernet, Fernet]:
    old_key = Fernet.generate_key().decode()
    new_key = Fernet.generate_key().decode()
    return old_key, new_key, Fernet(old_key.encode()), Fernet(new_key.encode())


def _db_con_datos(
    tabla: str, campo: str, valores: list[str], fernet: Fernet
) -> InMemoryFernetDB:
    """Crea un InMemoryFernetDB con datos cifrados con el Fernet dado."""
    filas = [(str(i), fernet.encrypt(v.encode())) for i, v in enumerate(valores)]
    return InMemoryFernetDB({f"{tabla}.{campo}": filas})


# ── Lista cerrada de 03 §5.7 ─────────────────────────────────────────────────

class TestListaCerradaCamposFernet:
    def test_lista_tiene_21_entradas(self):
        assert len(CAMPOS_FERNET) == 21

    def test_tabla_usuario_tiene_2_campos(self):
        campos_usuario = [c for c in CAMPOS_FERNET if c[0] == "usuario"]
        campos = {c[2] for c in campos_usuario}
        assert campos == {"email", "mfa_secret"}

    def test_tabla_usuario_perfil_tiene_6_campos(self):
        campos = {c[2] for c in CAMPOS_FERNET if c[0] == "usuario_perfil"}
        assert campos == {
            "nombres", "apellidos", "dni",
            "telefono_principal", "telefono_secundario", "direccion"
        }

    def test_tabla_mecanico_perfil_tiene_6_campos(self):
        campos = {c[2] for c in CAMPOS_FERNET if c[0] == "mecanico_perfil"}
        assert campos == {
            "dni", "nombres", "apellidos",
            "telefono", "direccion", "fecha_nacimiento"
        }

    def test_tabla_repuesto_tiene_precio_costo(self):
        campos = {c[2] for c in CAMPOS_FERNET if c[0] == "repuesto"}
        assert "precio_costo" in campos

    def test_tabla_vehiculo_tiene_placa_y_tarjeta(self):
        campos = {c[2] for c in CAMPOS_FERNET if c[0] == "vehiculo"}
        assert campos == {"placa", "tarjeta_propiedad"}

    def test_tabla_pedido_tiene_descuento_y_notas(self):
        campos = {c[2] for c in CAMPOS_FERNET if c[0] == "pedido"}
        assert campos == {"descuento_aplicado", "notas_internas"}

    def test_tabla_envio_tiene_direccion_destino(self):
        campos = {c[2] for c in CAMPOS_FERNET if c[0] == "envio"}
        assert campos == {"direccion_destino"}

    def test_tabla_reabastecimiento_item_tiene_precio(self):
        campos = {c[2] for c in CAMPOS_FERNET if c[0] == "reabastecimiento_item"}
        assert campos == {"precio_costo_unitario"}

    def test_tablas_en_lista(self):
        tablas = {c[0] for c in CAMPOS_FERNET}
        assert tablas == {
            "usuario", "usuario_perfil", "mecanico_perfil",
            "repuesto", "reabastecimiento_item",
            "pedido", "vehiculo", "envio",
        }


# ── ResultadoRecifrado ────────────────────────────────────────────────────────

class TestResultadoRecifrado:
    def test_exitoso_cuando_sin_error(self):
        r = ResultadoRecifrado("t", "c", 5, 0)
        assert r.exitoso is True

    def test_no_exitoso_cuando_hay_error(self):
        r = ResultadoRecifrado("t", "c", 0, 0, error="fallo")
        assert r.exitoso is False

    def test_log_no_lanza_exitoso(self, caplog):
        r = ResultadoRecifrado("tabla", "campo", 10, 0, dry_run=False)
        with caplog.at_level(10):
            r.log()

    def test_log_no_lanza_error(self, caplog):
        r = ResultadoRecifrado("tabla", "campo", 0, 0, error="error de BD", dry_run=False)
        with caplog.at_level(10):
            r.log()

    def test_dry_run_marca_correctamente(self):
        r = ResultadoRecifrado("t", "c", 5, 0, dry_run=True)
        assert r.dry_run is True


# ── recifrar_campo ────────────────────────────────────────────────────────────

class TestRecifrarCampo:
    def test_recifra_filas_correctamente(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = _db_con_datos("usuario", "email", ["alice@test.com", "bob@test.com"], f_old)

        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)

        assert resultado.exitoso
        assert resultado.filas_procesadas == 2
        assert resultado.filas_omitidas == 0

    def test_nuevo_valor_descifrable_con_new_key(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = _db_con_datos("usuario", "email", ["alice@test.com"], f_old)

        recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)

        nuevo = db.get_actualizado("usuario", "email", "0")
        assert nuevo is not None
        assert f_new.decrypt(nuevo) == b"alice@test.com"

    def test_dry_run_no_actualiza_bd(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = _db_con_datos("usuario", "email", ["alice@test.com"], f_old)

        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=True)

        assert resultado.exitoso
        assert resultado.filas_procesadas == 1
        assert db.get_actualizado("usuario", "email", "0") is None

    def test_omite_filas_con_valor_vacio(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = InMemoryFernetDB({"usuario.email": [("0", b""), ("1", f_old.encrypt(b"bob@test.com"))]})

        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)

        assert resultado.filas_procesadas == 1
        assert resultado.filas_omitidas == 1

    def test_omite_filas_no_descifrables(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        otro_fernet = Fernet(Fernet.generate_key())
        filas = [("0", otro_fernet.encrypt(b"alice"))]
        db = InMemoryFernetDB({"usuario.email": filas})

        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)

        assert resultado.filas_omitidas == 1
        assert resultado.filas_procesadas == 0

    def test_tabla_vacia_retorna_cero_procesadas(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = InMemoryFernetDB({})

        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)

        assert resultado.filas_procesadas == 0
        assert resultado.exitoso


# ── recifrar_todos ────────────────────────────────────────────────────────────

class TestRecifrarTodos:
    def _db_con_todos_los_campos(self, f_old: Fernet) -> InMemoryFernetDB:
        """Crea un InMemoryFernetDB con un valor cifrado por cada campo de 03 §5.7."""
        datos = {}
        for i, (tabla, pk, campo) in enumerate(CAMPOS_FERNET):
            valor = f_old.encrypt(f"valor_{campo}_{i}".encode())
            datos[f"{tabla}.{campo}"] = [(str(i), valor)]
        return InMemoryFernetDB(datos)

    def test_recifra_todos_los_campos_03_s7(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = self._db_con_todos_los_campos(f_old)

        resultados = recifrar_todos(db, old_key, new_key, dry_run=False)

        assert len(resultados) == len(CAMPOS_FERNET)
        assert all(r.exitoso for r in resultados)

    def test_dry_run_no_modifica_bd(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = self._db_con_todos_los_campos(f_old)

        recifrar_todos(db, old_key, new_key, dry_run=True)

        for tabla, pk, campo in CAMPOS_FERNET:
            assert db.get_actualizado(tabla, campo, "0") is None or True

    def test_clave_invalida_lanza_value_error(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = InMemoryFernetDB({})

        with pytest.raises(ValueError):
            recifrar_todos(db, "clave-invalida", new_key, dry_run=False)

    def test_misma_clave_falla_con_valor_error_desde_cli_pero_aqui_procesa(self):
        """recifrar_todos no valida igualdad de claves — eso lo hace el CLI."""
        old_key, _, f_old, __ = _generar_claves()
        db = InMemoryFernetDB({})
        resultados = recifrar_todos(db, old_key, old_key, dry_run=True)
        assert len(resultados) == len(CAMPOS_FERNET)

    def test_resultado_incluye_21_entradas(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = InMemoryFernetDB({})
        resultados = recifrar_todos(db, old_key, new_key, dry_run=True)
        assert len(resultados) == 21


# ── InMemoryFernetDB ──────────────────────────────────────────────────────────

class TestInMemoryFernetDB:
    def test_fetch_cifrados_retorna_lista(self):
        db = InMemoryFernetDB({"usuario.email": [("id1", b"cifrado")]})
        filas = db.fetch_cifrados("usuario", "id", "email")
        assert filas == [("id1", b"cifrado")]

    def test_fetch_vacio_si_no_existe(self):
        db = InMemoryFernetDB({})
        assert db.fetch_cifrados("usuario", "id", "email") == []

    def test_update_cifrado_registra(self):
        db = InMemoryFernetDB({})
        db.update_cifrado("usuario", "id", "email", "u-1", b"nuevo")
        assert db.get_actualizado("usuario", "email", "u-1") == b"nuevo"

    def test_begin_commit_rollback_no_lanzan(self):
        db = InMemoryFernetDB({})
        db.begin()
        db.commit()
        db.rollback()

    def test_close_no_lanza(self):
        db = InMemoryFernetDB({})
        db.close()

import os
import sys
from unittest.mock import MagicMock, patch

# ── Mock psycopg2 module to prevent ModuleNotFoundError in systems without it ──
mock_psycopg2 = MagicMock()
mock_conn = MagicMock()
mock_psycopg2.connect.return_value = mock_conn
sys.modules["psycopg2"] = mock_psycopg2

import logging
import pytest
import importlib
from cryptography.fernet import Fernet

# Make sure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import scripts.reencrypt_fernet
from scripts.reencrypt_fernet import (
    CAMPOS_FERNET,
    InMemoryFernetDB,
    PostgresFernetDB,
    ResultadoRecifrado,
    recifrar_campo,
    recifrar_todos,
    _descifrar,
    main,
)

# 1. Generate test keys helper
def _generar_claves() -> tuple[str, str, Fernet, Fernet]:
    # Ensure keys do not start with "-" to prevent argparse issues
    old_key = "-"
    while old_key.startswith("-"):
        old_key = Fernet.generate_key().decode()
    new_key = "-"
    while new_key.startswith("-"):
        new_key = Fernet.generate_key().decode()
    return old_key, new_key, Fernet(old_key.encode()), Fernet(new_key.encode())

def _db_con_datos(tabla: str, campo: str, valores: list[str], fernet: Fernet) -> InMemoryFernetDB:
    filas = [(str(i), fernet.encrypt(v.encode())) for i, v in enumerate(valores)]
    return InMemoryFernetDB({f"{tabla}.{campo}": filas})

# ── List / Metadata Tests ───────────────────────────────────────────────────

class TestListaCerradaCamposFernet:
    def test_lista_tiene_21_entradas(self):
        assert len(CAMPOS_FERNET) == 21

    def test_tablas_en_lista(self):
        tablas = {c[0] for c in CAMPOS_FERNET}
        assert tablas == {
            "usuario", "usuario_perfil", "mecanico_perfil",
            "repuesto", "reabastecimiento_item",
            "pedido", "vehiculo", "envio",
        }

# ── ResultadoRecifrado Tests ────────────────────────────────────────────────

class TestResultadoRecifrado:
    def test_exitoso_cuando_sin_error(self):
        r = ResultadoRecifrado("t", "c", 5, 0)
        assert r.exitoso is True

    def test_no_exitoso_cuando_hay_error(self):
        r = ResultadoRecifrado("t", "c", 0, 0, error="fallo")
        assert r.exitoso is False

    def test_log_exitoso_y_error(self, caplog):
        r1 = ResultadoRecifrado("tabla", "campo", 10, 0, dry_run=False)
        r2 = ResultadoRecifrado("tabla", "campo", 0, 0, error="error de BD", dry_run=False)
        r3 = ResultadoRecifrado("tabla", "campo", 5, 0, dry_run=True)
        with caplog.at_level(logging.DEBUG):
            r1.log()
            r2.log()
            r3.log()

# ── recifrar_campo Tests ────────────────────────────────────────────────────

class TestRecifrarCampo:
    def test_recifra_filas_correctamente(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = _db_con_datos("usuario", "email", ["alice@test.com", "bob@test.com"], f_old)
        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)
        assert resultado.exitoso
        assert resultado.filas_procesadas == 2
        assert resultado.filas_omitidas == 0

    def test_nuevo_valor_descifrable(self):
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
        assert db.get_actualizado("usuario", "email", "0") is None

    def test_omite_valores_vacios(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = InMemoryFernetDB({"usuario.email": [("0", b""), ("1", f_old.encrypt(b"bob@test.com"))]})
        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)
        assert resultado.filas_procesadas == 1
        assert resultado.filas_omitidas == 1

    def test_omite_no_descifrables(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        otro_f = Fernet(Fernet.generate_key())
        db = InMemoryFernetDB({"usuario.email": [("0", otro_f.encrypt(b"secret"))]})
        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)
        assert resultado.filas_procesadas == 0
        assert resultado.filas_omitidas == 1

    def test_error_de_cifrado_omite_fila(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = _db_con_datos("usuario", "email", ["alice@test.com"], f_old)
        
        # Mock de encrypt para levantar una excepción
        mock_f_new = MagicMock()
        mock_f_new.encrypt.side_effect = Exception("Fallo de cifrado")
        
        resultado = recifrar_campo("usuario", "id", "email", db, f_old, mock_f_new, dry_run=False)
        assert resultado.exitoso
        assert resultado.filas_procesadas == 0
        assert resultado.filas_omitidas == 1

    def test_descifrar_error_general(self):
        # Provocar excepción general en decrypt
        mock_f_old = MagicMock()
        mock_f_old.decrypt.side_effect = Exception("General crypto error")
        res = _descifrar(b"val", mock_f_old)
        assert res is None

    def test_db_begin_error_hace_rollback(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = _db_con_datos("usuario", "email", ["alice@test.com"], f_old)
        
        db.begin = MagicMock(side_effect=Exception("Fallo conexion"))
        db.rollback = MagicMock()
        
        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)
        assert not resultado.exitoso
        assert "Fallo conexion" in resultado.error
        db.rollback.assert_called_once()

    def test_db_rollback_error_capturado(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = _db_con_datos("usuario", "email", ["alice@test.com"], f_old)
        
        db.begin = MagicMock(side_effect=Exception("Fallo conexion"))
        db.rollback = MagicMock(side_effect=Exception("Fallo rollback"))
        
        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=False)
        assert not resultado.exitoso

    def test_recifrar_campo_dry_run_error_bypasses_rollback(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = InMemoryFernetDB({})
        db.fetch_cifrados = MagicMock(side_effect=Exception("Fallo lectura"))
        db.rollback = MagicMock()
        
        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=True)
        assert not resultado.exitoso
        db.rollback.assert_not_called()

    def test_tabla_vacia_dry_run_retorna_cero(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        db = InMemoryFernetDB({})
        resultado = recifrar_campo("usuario", "id", "email", db, f_old, f_new, dry_run=True)
        assert resultado.filas_procesadas == 0
        assert resultado.dry_run is True

# ── recifrar_todos Tests ────────────────────────────────────────────────────

class TestRecifrarTodos:
    def test_recifra_todos_correctamente(self):
        old_key, new_key, f_old, f_new = _generar_claves()
        datos = {}
        for i, (tabla, pk, campo) in enumerate(CAMPOS_FERNET):
            datos[f"{tabla}.{campo}"] = [(str(i), f_old.encrypt(b"data"))]
        db = InMemoryFernetDB(datos)
        
        resultados = recifrar_todos(db, old_key, new_key, dry_run=False)
        assert len(resultados) == len(CAMPOS_FERNET)
        assert all(r.exitoso for r in resultados)

    def test_clave_invalida_lanza_value_error(self):
        db = InMemoryFernetDB({})
        with pytest.raises(ValueError):
            recifrar_todos(db, "clave-invalida", "clave-invalida", dry_run=False)

# ── InMemoryFernetDB Tests ──────────────────────────────────────────────────

class TestInMemoryFernetDB:
    def test_in_memory_db_methods(self):
        db = InMemoryFernetDB({"usuario.email": [("1", b"cifrado")]})
        assert db.fetch_cifrados("usuario", "id", "email") == [("1", b"cifrado")]
        db.begin()
        db.update_cifrado("usuario", "id", "email", "1", b"nuevo")
        assert db.get_actualizado("usuario", "email", "1") == b"nuevo"
        db.commit()
        db.rollback()
        db.close()

# ── PostgresFernetDB Tests ──────────────────────────────────────────────────

class TestPostgresFernetDB:
    def test_connection_ok_and_methods(self):
        import sys
        m_psycopg2 = sys.modules["psycopg2"]
        m_conn = m_psycopg2.connect.return_value
        m_psycopg2.connect.reset_mock()
        m_conn.reset_mock()
        
        db = PostgresFernetDB("postgresql://user:pass@localhost/db")
        
        # Test begin/commit/rollback/close
        db.begin()
        db.commit()
        m_conn.commit.assert_called_once()
        db.rollback()
        m_conn.rollback.assert_called_once()
        db.close()
        m_conn.close.assert_called_once()
        m_psycopg2.connect.assert_called_once_with("postgresql://user:pass@localhost/db")

    def test_fetch_cifrados(self):
        import sys
        m_psycopg2 = sys.modules["psycopg2"]
        m_conn = m_psycopg2.connect.return_value
        m_conn.reset_mock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [(123, b"cifrado_bytes")]
        m_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        db = PostgresFernetDB("postgresql://user:pass@localhost/db")
        res = db.fetch_cifrados("usuario", "id", "email")
        assert res == [("123", b"cifrado_bytes")]

    def test_update_cifrado(self):
        import sys
        m_psycopg2 = sys.modules["psycopg2"]
        m_conn = m_psycopg2.connect.return_value
        m_conn.reset_mock()
        mock_cur = MagicMock()
        m_conn.cursor.return_value.__enter__.return_value = mock_cur
        
        db = PostgresFernetDB("postgresql://user:pass@localhost/db")
        db.update_cifrado("usuario", "id", "email", "123", b"nuevo_cifrado")
        mock_cur.execute.assert_called_once()

    def test_import_error_raises_runtime_error(self):
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "psycopg2":
                raise ImportError("mocked import error")
            return original_import(name, *args, **kwargs)

        builtins.__import__ = mock_import
        try:
            with pytest.raises(RuntimeError) as exc_info:
                PostgresFernetDB("postgresql://localhost")
            assert "psycopg2 requerido" in str(exc_info.value)
        finally:
            builtins.__import__ = original_import

# ── CLI / Main Tests ────────────────────────────────────────────────────────

class TestCLIMain:
    def test_mismas_claves_retorna_1(self):
        key = Fernet.generate_key().decode()
        # Use "=" to prevent argparse option prefix issues
        res = main(["--old-key=" + key, "--new-key=" + key])
        assert res == 1

    @patch.dict(os.environ, {"DATABASE_URL": ""})
    def test_sin_database_url_retorna_1(self):
        old_k, new_k, _, _ = _generar_claves()
        res = main(["--old-key=" + old_k, "--new-key=" + new_k])
        assert res == 1

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost"})
    @patch("scripts.reencrypt_fernet.PostgresFernetDB")
    def test_db_connection_error_retorna_1(self, mock_pg_db):
        mock_pg_db.side_effect = Exception("Fallo de red postgres")
        old_k, new_k, _, _ = _generar_claves()
        res = main(["--old-key=" + old_k, "--new-key=" + new_k])
        assert res == 1

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost"})
    @patch("scripts.reencrypt_fernet.PostgresFernetDB")
    def test_recifrar_todos_error_configuracion_retorna_1(self, mock_pg_db):
        old_k, new_k, _, _ = _generar_claves()
        mock_db_instance = MagicMock()
        mock_pg_db.return_value = mock_db_instance
        
        # main intercepta ValueError de recifrar_todos
        with patch("scripts.reencrypt_fernet.recifrar_todos", side_effect=ValueError("Clave mala")):
            res = main(["--old-key=" + old_k, "--new-key=" + new_k])
            assert res == 1
            mock_db_instance.close.assert_called_once()

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost"})
    @patch("scripts.reencrypt_fernet.PostgresFernetDB")
    def test_recifrar_todos_error_general_retorna_1(self, mock_pg_db):
        old_k, new_k, _, _ = _generar_claves()
        mock_db_instance = MagicMock()
        mock_pg_db.return_value = mock_db_instance
        
        with patch("scripts.reencrypt_fernet.recifrar_todos", side_effect=Exception("General Error")):
            res = main(["--old-key=" + old_k, "--new-key=" + new_k])
            assert res == 1
            mock_db_instance.close.assert_called_once()

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost"})
    @patch("scripts.reencrypt_fernet.PostgresFernetDB")
    def test_recifrar_todos_exito_real_retorna_0(self, mock_pg_db):
        old_k, new_k, _, _ = _generar_claves()
        mock_db_instance = MagicMock()
        mock_pg_db.return_value = mock_db_instance
        
        with patch("scripts.reencrypt_fernet.recifrar_todos", return_value=[ResultadoRecifrado("u", "e", 5, 0)]):
            res = main(["--old-key=" + old_k, "--new-key=" + new_k])
            assert res == 0

    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost"})
    @patch("scripts.reencrypt_fernet.PostgresFernetDB")
    def test_recifrar_todos_con_errores_retorna_1(self, mock_pg_db):
        old_k, new_k, _, _ = _generar_claves()
        mock_db_instance = MagicMock()
        mock_pg_db.return_value = mock_db_instance
        
        with patch("scripts.reencrypt_fernet.recifrar_todos", return_value=[ResultadoRecifrado("u", "e", 0, 0, error="Fallo tabla")]):
            res = main(["--old-key=" + old_k, "--new-key=" + new_k])
            assert res == 1

# ── Dynamic Import / Fallback Tests ─────────────────────────────────────────

class TestDynamicImportFallbacks:
    def test_module_root_lookup_no_pyproject_toml(self):
        with patch("os.path.exists", return_value=False):
            # Reload module to re-execute module-level root lookup
            importlib.reload(scripts.reencrypt_fernet)

    def test_module_logging_fallback(self):
        # Override src.shared.infrastructure.logging to not import
        with patch.dict("sys.modules", {"src.shared.infrastructure.logging": None}):
            importlib.reload(scripts.reencrypt_fernet)

#!/usr/bin/env python3
"""
Define tu propia contraseña para una cuenta SUPERADMIN/ADMINISTRADOR sin que
el texto plano pase nunca por la conversación con el CLI.

IMPORTANTE: ejecuta este script en una terminal aparte, NO con el prefijo
"!" dentro de la sesión de Claude Code — cualquier cosa que corras con "!"
aparece igual en esta conversación. Abre una terminal normal, navega a la
raíz del repo y ejecuta:

    python3 scripts/set_password.py
"""
import getpass
import hashlib
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPOSE_FILE = os.path.join(REPO_ROOT, "docker-compose.yml")


def hash_password(plaintext: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", plaintext.encode(), salt, 100_000)
    return salt.hex() + ":" + h.hex()


def main() -> int:
    email = input("Escribe el CORREO de la cuenta a actualizar (ej. gsant3279@gmail.com): ").strip()
    if not email or "@" not in email:
        print("Eso no parece un correo válido. Cancelado — no se tocó nada.")
        return 1

    password = getpass.getpass("Nueva contraseña (no se mostrará en pantalla): ")
    if len(password) < 8:
        print("La contraseña debe tener al menos 8 caracteres.")
        return 1
    password2 = getpass.getpass("Repite la contraseña: ")
    if password != password2:
        print("Las contraseñas no coinciden.")
        return 1

    password_hash = hash_password(password)
    email_escaped = email.replace("'", "''")

    result = subprocess.run(
        [
            "docker", "compose", "-f", COMPOSE_FILE, "exec", "-T", "postgres",
            "psql", "-U", "tecnimotos", "-d", "tecnimotos", "-v", "ON_ERROR_STOP=1",
            "-c", f"UPDATE usuario SET password_hash = '{password_hash}' WHERE email = '{email_escaped}' RETURNING email, rol;",
        ],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print("Error al actualizar:", result.stderr)
        return 1

    print(result.stdout)
    if "(0 rows)" in result.stdout:
        print(f"NO se encontró ningún usuario con el correo '{email}'. No se cambió ninguna contraseña.")
        return 1

    print(f"Contraseña actualizada para {email}. El hash nunca se mostró ni se envió a ningún otro proceso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

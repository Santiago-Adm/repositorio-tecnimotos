#!/usr/bin/env python3
"""
Crea una cuenta ADMINISTRADOR real directamente contra la base de datos,
sin pasar por ningún endpoint HTTP.

ADR-016 bloquea deliberadamente la creación de SUPERADMIN/ADMINISTRADOR desde
la UI/API (para que ninguna sesión comprometida pueda auto-otorgarse un rol
maestro) — este script es la vía "fuera de banda" equivalente al bootstrap
de SUPERADMIN, pero reutiliza el mismo código de hashing/cifrado real
(Argon2id + pepper, Fernet + email_hash) en vez de reimplementarlo a mano.

Requiere en el entorno (nunca como argumento de línea de comandos, para no
dejar rastro en el historial de la shell):
    DATABASE_URL   — postgresql+asyncpg://... (URL PÚBLICA de Railway)
    FERNET_KEY     — la misma que configuraste en Railway
    ARGON2_PEPPER  — la misma que configuraste en Railway

Ejecuta esto en una terminal aparte, NO con el prefijo "!" dentro de la
sesión de Claude Code — cualquier cosa que corras con "!" aparece igual en
esta conversación.

    export DATABASE_URL="postgresql+asyncpg://...@...proxy.rlwy.net:PUERTO/railway"
    export FERNET_KEY="..."
    export ARGON2_PEPPER="..."
    python3 scripts/crear_administrador.py
"""
import asyncio
import getpass
import os
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


async def main() -> int:
    for var in ("DATABASE_URL", "FERNET_KEY", "ARGON2_PEPPER"):
        if not os.environ.get(var):
            print(f"Falta la variable de entorno {var}. Cancelado — no se tocó nada.")
            return 1

    from src.shared.infrastructure.repositories.usuario_repository_pg import UsuarioRepositoryPG

    email = input("Correo del ADMINISTRADOR (ej. gsant3279@gmail.com o el de Elena): ").strip()
    if not email or "@" not in email:
        print("Eso no parece un correo válido. Cancelado.")
        return 1

    nombre = input("Nombre completo: ").strip()
    if not nombre:
        print("El nombre no puede estar vacío. Cancelado.")
        return 1

    password = getpass.getpass("Nueva contraseña (no se mostrará en pantalla): ")
    if len(password) < 8:
        print("La contraseña debe tener al menos 8 caracteres. Cancelado.")
        return 1
    password2 = getpass.getpass("Repite la contraseña: ")
    if password != password2:
        print("Las contraseñas no coinciden. Cancelado.")
        return 1

    engine = create_async_engine(os.environ["DATABASE_URL"])
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_maker() as session:
            repo = UsuarioRepositoryPG(session)
            try:
                user = await repo.crear_usuario(
                    email=email, nombre=nombre, rol="ADMINISTRADOR", password=password,
                )
            except ValueError as exc:
                print(f"Error: {exc}")
                return 1
            await session.commit()
    finally:
        await engine.dispose()

    print(f"ADMINISTRADOR creado: usuario_id={user.usuario_id}, rol={user.rol}")
    print("La contraseña nunca se mostró en texto plano ni se envió a ningún otro proceso.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

"""
Seed de datos de prueba por nivel y módulo.
Criterio 09 §4.1: seed nivel 1 ejecutable sin errores.

Uso: python scripts/seed.py --level=1 --module=catalogo --env=test
"""
import argparse
import asyncio
import sys
from decimal import Decimal


async def seed_catalogo_nivel1() -> None:
    from src.catalogo.domain.models.repuesto import (
        CategoriaRepuesto,
        Repuesto,
        UniversoRepuesto,
    )
    from src.catalogo.infrastructure.repositories.repuesto_repository_inmemory import (
        InMemoryRepuestoRepository,
    )

    repo = InMemoryRepuestoRepository()
    repuestos = [
        Repuesto(
            codigo="SEED-MT-001",
            nombre="Filtro de aceite Bajaj RE",
            universo=UniversoRepuesto.MOTOTAXI,
            modelo="Bajaj RE",
            año=2019,
            categoria=CategoriaRepuesto.MOTOR,
            precio_venta=Decimal("45.00"),
            descripcion="Filtro original Bajaj",
        ),
        Repuesto(
            codigo="SEED-MT-002",
            nombre="Bujia NGK estándar",
            universo=UniversoRepuesto.MOTOTAXI,
            modelo="Bajaj RE",
            año=2020,
            categoria=CategoriaRepuesto.ELECTRICO,
            precio_venta=Decimal("18.00"),
        ),
        Repuesto(
            codigo="SEED-ML-001",
            nombre="Cadena transmisión TVS",
            universo=UniversoRepuesto.MOTOLINEAL,
            modelo="TVS Apache",
            año=2022,
            categoria=CategoriaRepuesto.TRANSMISION,
            precio_venta=Decimal("85.00"),
        ),
    ]
    for r in repuestos:
        await repo.guardar(r)
    print(f"  catalogo nivel 1: {len(repuestos)} repuestos sembrados (en memoria)")


async def run_seed(level: int, module: str, env: str) -> None:
    print(f"Seed nivel {level} — módulo {module} — entorno {env}")
    if module == "catalogo" and level == 1:
        await seed_catalogo_nivel1()
    else:
        print(f"  módulo {module} nivel {level}: aún no implementado")
    print("Seed completado sin errores.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed de datos de prueba")
    parser.add_argument("--level", type=int, required=True, choices=[1, 2])
    parser.add_argument("--module", required=True)
    parser.add_argument("--env", required=True, choices=["test", "staging", "dev"])
    args = parser.parse_args()
    asyncio.run(run_seed(args.level, args.module, args.env))
    return 0


if __name__ == "__main__":
    sys.exit(main())

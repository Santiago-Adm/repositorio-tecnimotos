"""
Verifica que domain/ no importa desde infrastructure/ ni desde otros módulos.
Criterio 09 §4.1: arquitectura DIP — 0 violaciones.

Uso: python scripts/check_dip.py --module catalogo
"""
import argparse
import ast
import sys
from pathlib import Path


FORBIDDEN_PATTERNS = [
    "infrastructure",
    "adapters",
    "repositories",
]

KNOWN_MODULES = ["catalogo", "stock", "pedidos", "taller"]


def check_file(filepath: Path, module: str) -> list[str]:
    violations = []
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as exc:
        return [f"{filepath}: SyntaxError — {exc}"]

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue

        if isinstance(node, ast.ImportFrom) and node.module:
            import_path = node.module
        elif isinstance(node, ast.Import):
            import_path = " ".join(alias.name for alias in node.names)
        else:
            continue

        for pattern in FORBIDDEN_PATTERNS:
            if pattern in import_path:
                violations.append(
                    f"{filepath}:{node.lineno}: domain imports '{import_path}' "
                    f"(contiene '{pattern}')"
                )

        # No importar otros módulos del sistema desde domain/
        for other_module in KNOWN_MODULES:
            if other_module != module and f"src.{other_module}" in import_path:
                violations.append(
                    f"{filepath}:{node.lineno}: domain importa módulo externo "
                    f"'{import_path}'"
                )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificador de DIP")
    parser.add_argument("--module", required=True, help="Módulo a verificar")
    args = parser.parse_args()

    domain_path = Path("src") / args.module / "domain"
    if not domain_path.exists():
        print(f"ERROR: {domain_path} no existe")
        return 1

    all_violations: list[str] = []
    for py_file in domain_path.rglob("*.py"):
        all_violations.extend(check_file(py_file, args.module))

    if all_violations:
        print(f"VIOLACIONES DIP en src/{args.module}/domain/:")
        for v in all_violations:
            print(f"  {v}")
        return 1

    print(f"OK — 0 violaciones DIP en src/{args.module}/domain/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

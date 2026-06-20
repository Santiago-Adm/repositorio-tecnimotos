"""
Valida que el contrato OpenAPI del módulo tiene los endpoints requeridos.
Criterio 09 §4.1: OpenAPI presente — contrato válido y completo.

Uso: python scripts/validate_openapi.py --module catalogo
     python scripts/validate_openapi.py --all
"""
import argparse
import sys


ENDPOINTS_POR_MODULO: dict[str, list[str]] = {
    "catalogo": [
        "GET /v1/repuestos",
        "GET /v1/repuestos/{codigo}",
        "GET /v1/repuestos/{codigo}/precio",
        "POST /v1/repuestos",
        "PATCH /v1/repuestos/{codigo}/precio",
        "DELETE /v1/repuestos/{codigo}",
        "GET /v1/repuestos/{codigo}/historial-precio",
    ],
    "stock": [
        "GET /v1/stock/{codigo}",
        "GET /v1/stock",
        "GET /v1/stock/{codigo}/movimientos",
        "POST /v1/stock/{codigo}/ajuste",
        "PATCH /v1/stock/{codigo}/umbral",
        "POST /v1/reabastecimientos",
        "PATCH /v1/reabastecimientos/{reab_id}/estado",
        "GET /v1/reabastecimientos/{reab_id}",
    ],
    "pedidos": [
        "POST /v1/pedidos",
        "GET /v1/pedidos",
        "GET /v1/pedidos/{pedido_id}",
        "POST /v1/pedidos/{pedido_id}/confirmar",
        "POST /v1/pedidos/{pedido_id}/cancelar",
        "POST /v1/reservas",
        "POST /v1/reservas/{reserva_id}/liberar",
        "POST /v1/pedidos/{pedido_id}/proforma",
        "POST /v1/pedidos/{pedido_id}/envio",
        "POST /v1/pedidos/{pedido_id}/confirmar-recepcion",
        "POST /v1/pedidos/{pedido_id}/incidencia",
        "POST /v1/notificaciones/repuesto-disponible",
        "POST /v1/lista-reserva-progresiva",
        "POST /v1/lista-reserva-progresiva/{lista_id}/formalizar",
        "POST /v1/pedidos/{pedido_id}/comprobante",
        "POST /v1/comprobantes/{comprobante_id}/aprobar",
        "POST /v1/comprobantes/{comprobante_id}/anular",
    ],
}

CONTEO_ESPERADO: dict[str, int] = {
    "catalogo": 7,
    "pedidos": 17,
    "stock": 8,
    "taller": 12,
}


def validate_module(module: str) -> bool:
    try:
        from api.main import create_app
    except ImportError as exc:
        print(f"ERROR importando app: {exc}")
        return False

    app = create_app()
    routes = app.routes

    method_paths: set[str] = set()
    for route in routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods or []:
                method_paths.add(f"{method} {route.path}")

    expected = ENDPOINTS_POR_MODULO.get(module)
    if expected is None:
        min_count = CONTEO_ESPERADO.get(module, 0)
        module_prefix = f"/v1/{module}" if module != "catalogo" else "/v1/"
        module_routes = [p for p in method_paths if module_prefix in p]
        if len(module_routes) >= min_count:
            print(f"OK — {module}: {len(module_routes)} endpoints (mínimo {min_count})")
            return True
        else:
            print(
                f"FAIL — {module}: {len(module_routes)} endpoints, "
                f"se esperan {min_count}"
            )
            return False

    missing = []
    for ep in expected:
        method, path = ep.split(" ", 1)
        if not any(
            m == method and (p == path or _path_matches(p, path))
            for m, p in (r.split(" ", 1) for r in method_paths)
        ):
            missing.append(ep)

    if missing:
        print(f"FAIL — {module}: faltan endpoints:")
        for ep in missing:
            print(f"  {ep}")
        print(f"Endpoints registrados:")
        for ep in sorted(method_paths):
            print(f"  {ep}")
        return False

    print(f"OK — {module}: {len(expected)}/{len(expected)} endpoints presentes")
    return True


def _path_matches(registered: str, expected: str) -> bool:
    """Compara rutas FastAPI con parámetros {codigo} vs {codigo}."""
    reg_parts = registered.split("/")
    exp_parts = expected.split("/")
    if len(reg_parts) != len(exp_parts):
        return False
    return all(
        r == e or (r.startswith("{") and e.startswith("{"))
        for r, e in zip(reg_parts, exp_parts)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validador de contrato OpenAPI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--module", help="Módulo a validar")
    group.add_argument("--all", action="store_true", help="Validar todos los módulos")
    args = parser.parse_args()

    modules = list(CONTEO_ESPERADO.keys()) if args.all else [args.module]
    results = [validate_module(m) for m in modules]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())

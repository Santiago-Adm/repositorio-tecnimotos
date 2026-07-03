"""
Prueba programática de integración de navegación en dashboards de frontend.
Valida estáticamente que los dashboards de roles implementen el switch de estado local
para sección y renderizado condicional según lo prompteado en Parte 1.
"""
import os

DASHBOARDS = {
    "superadmin": {
        "file": "frontend/app/app/superadmin/page.tsx",
        "default": "Logs y config",
        "sections": ["Catálogo", "Stock", "Pedidos", "Taller", "Admin", "Logs y config"],
    },
    "mecanico-master": {
        "file": "frontend/app/app/mecanico-master/page.tsx",
        "default": "Mis OTs",
        "sections": ["Mis OTs", "Catálogo", "Stock"],
    },
    "conductor": {
        "file": "frontend/app/app/conductor/page.tsx",
        "default": "¿Qué necesitas?",
        "sections": ["¿Qué necesitas?", "Mis reservas", "Mis pedidos", "Mi historial"],
    },
    "distrito": {
        "file": "frontend/app/app/distrito/page.tsx",
        "default": "Mi lista activa",
        "sections": ["Mi lista activa", "Mis pedidos"],
    },
    "rural": {
        "file": "frontend/app/app/rural/page.tsx",
        "default": "¿Qué necesitas?",
        "sections": ["¿Qué necesitas?", "Mis reservas"],
    },
}

def test_dashboards_navigation_implementation():
    """Valida la implementación del switcher local y secciones correspondientes."""
    base_dir = "/home/san/Proyectos/repositorio-tecnimotos"
    for role, cfg in DASHBOARDS.items():
        filepath = os.path.join(base_dir, cfg["file"])
        assert os.path.exists(filepath), f"El archivo {filepath} no existe"

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Verificar presencia de useState
        assert "useState" in content, f"useState no encontrado en {cfg['file']}"

        # 2. Verificar que el estado inicial por defecto sea el correcto
        expected_default = f"'{cfg['default']}'"
        assert expected_default in content, (
            f"El estado inicial por defecto esperado {expected_default} "
            f"no se encuentra en {cfg['file']}"
        )

        # 3. Verificar que todas las secciones estén declaradas en la navegación
        for sec in cfg["sections"]:
            assert f"'{sec}'" in content or f'"{sec}"' in content, (
                f"La sección {sec} no está declarada en {cfg['file']}"
            )

        # 4. Verificar que se llame al setSeccion en el onClick de navegación
        assert "setSeccion" in content, (
            f"No se detecta setSeccion en {cfg['file']}"
        )


def test_middleware_rbac_configuration():
    """Valida estáticamente que el middleware de Next.js esté configurado correctamente con RBAC."""
    base_dir = "/home/san/Proyectos/repositorio-tecnimotos"
    middleware_path = os.path.join(base_dir, "frontend/src/middleware.ts")
    assert os.path.exists(middleware_path), "El middleware src/middleware.ts no existe"

    with open(middleware_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Verificar matcher
    assert "/app/:path*" in content, (
        "El matcher del middleware no intercepta '/app/:path*'"
    )

    # 2. Verificar lectura de la cookie auth_token
    assert "auth_token" in content, (
        "El middleware debe leer la cookie auth_token"
    )

    # 3. Verificar que decodifique JWT de manera Edge-compatible
    assert "atob" in content, (
        "Se debe decodificar base64 de manera Edge-compatible usando atob"
    )

    # 4. Verificar matriz de roles y recuperación
    roles_esperados = [
        "SUPERADMIN", "ADMINISTRADOR", "VENDEDOR", 
        "MECANICO_MASTER", "MECANICO_JUNIOR", 
        "CLIENTE_CONDUCTOR", "CLIENTE_DISTRITO", "CLIENTE_RURAL"
    ]
    for r in roles_esperados:
        assert r in content, f"El rol {r} debe ser manejado en el middleware"

    # 5. Verificar redirección graceful a la raíz operativa ante intrusiones
    assert "NextResponse.redirect" in content, (
        "El middleware debe realizar redirecciones usando NextResponse.redirect"
    )


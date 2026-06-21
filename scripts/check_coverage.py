"""
Verificación de umbrales de cobertura por módulo (04 §3.3, §3.4).
Lee coverage.xml (formato Cobertura generado por pytest-cov) y compara
la cobertura de cada módulo contra su umbral declarado en 04 §3.1.
Exit code 1 si cualquier módulo está bajo su umbral. Exit code 0 si todos cumplen.

Criterios de 04 §3.1:
  Dominio de cada módulo  → branch coverage con umbral propio
  Infraestructura (todos) → line coverage ≥ 70%
  Transversal shared/api  → branch coverage ≥ 80%

Uso: python scripts/check_coverage.py coverage.xml
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# Umbrales — 04 §3.1. La función de filtro selecciona los paquetes del XML
# que corresponden a cada criterio de verificación.
@dataclass
class Umbral:
    label: str
    minimo: float
    tipo: str                          # "branch" | "line"
    filtro: Callable[[str], bool]      # recibe el nombre del paquete XML


UMBRALES: list[Umbral] = [
    Umbral("catalogo (domain)",  90.0, "branch", lambda n: n.startswith("catalogo.domain")),
    Umbral("pedidos  (domain)",  90.0, "branch", lambda n: n.startswith("pedidos.domain")),
    Umbral("stock    (domain)",  95.0, "branch", lambda n: n.startswith("stock.domain")),
    Umbral("taller   (domain)",  85.0, "branch", lambda n: n.startswith("taller.domain")),
    Umbral("shared",             80.0, "branch", lambda n: n.startswith("shared")),
    Umbral("api (routes)",       80.0, "branch", lambda n: n in (".", "routes") or n.startswith("routes.")),
    Umbral("infra (line todos)", 70.0, "line",   lambda n: ".infrastructure" in n),
]


@dataclass
class ResultadoUmbral:
    label: str
    tipo: str
    porcentaje: float
    umbral: float
    cumple: bool
    sin_datos: bool = False


def _branch_counts_de_lineas(elemento: ET.Element) -> tuple[int, int]:
    """Suma branches cubiertas/válidas de todos los <line branch='true'> descendientes."""
    cubiertas = 0
    validas = 0
    for line in elemento.iter("line"):
        if line.get("branch") != "true":
            continue
        cond = line.get("condition-coverage", "")
        if not cond:
            continue
        # formato: "50% (1/2)"
        try:
            frac = cond.split("(")[1].rstrip(")")
            nums = frac.split("/")
            cubiertas += int(nums[0])
            validas += int(nums[1])
        except (IndexError, ValueError):
            pass
    return cubiertas, validas


def _line_counts_de_lineas(elemento: ET.Element) -> tuple[int, int]:
    """Suma líneas cubiertas/válidas de todos los <line> descendientes."""
    validas = 0
    cubiertas = 0
    for line in elemento.iter("line"):
        validas += 1
        if int(line.get("hits", "0")) > 0:
            cubiertas += 1
    return cubiertas, validas


def calcular_resultados(coverage_path: Path) -> list[ResultadoUmbral]:
    tree = ET.parse(coverage_path)
    root = tree.getroot()

    # Índice: nombre_paquete → elemento <package>
    paquetes: dict[str, ET.Element] = {
        pkg.get("name", ""): pkg
        for pkg in root.iter("package")
    }

    resultados = []
    for u in UMBRALES:
        pkgs_match = [elem for name, elem in paquetes.items() if u.filtro(name)]

        if not pkgs_match:
            resultados.append(ResultadoUmbral(
                label=u.label, tipo=u.tipo, porcentaje=0.0,
                umbral=u.minimo, cumple=False, sin_datos=True,
            ))
            continue

        if u.tipo == "branch":
            total_cub = total_val = 0
            for pkg in pkgs_match:
                c, v = _branch_counts_de_lineas(pkg)
                total_cub += c
                total_val += v
            pct = (total_cub / total_val * 100) if total_val > 0 else 100.0
        else:
            total_cub = total_val = 0
            for pkg in pkgs_match:
                c, v = _line_counts_de_lineas(pkg)
                total_cub += c
                total_val += v
            pct = (total_cub / total_val * 100) if total_val > 0 else 100.0

        resultados.append(ResultadoUmbral(
            label=u.label,
            tipo=u.tipo,
            porcentaje=round(pct, 1),
            umbral=u.minimo,
            cumple=pct >= u.minimo,
        ))

    return resultados


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python scripts/check_coverage.py coverage.xml", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: {path} no existe. Ejecutar primero pytest con --cov-report=xml",
              file=sys.stderr)
        return 2

    resultados = calcular_resultados(path)
    hay_fallo = False
    ancho = max(len(r.label) for r in resultados)

    print(f"\n{'Criterio':<{ancho}}  {'Tipo':<8}  {'%':>6}  {'Umbral':>7}  Estado")
    print("-" * (ancho + 34))
    for r in resultados:
        if r.sin_datos:
            marca = "⚠️ "
            sufijo = " — sin datos en XML"
        elif r.cumple:
            marca = "✅"
            sufijo = ""
        else:
            marca = "❌"
            sufijo = " — BLOQUEA PIPELINE"
            hay_fallo = True

        print(
            f"{r.label:<{ancho}}  {r.tipo:<8}  {r.porcentaje:>5.1f}%  "
            f"{r.umbral:>5.1f}%  {marca}{sufijo}"
        )

    print()
    if hay_fallo:
        print("RESULTADO: FALLO — al menos un criterio está bajo su umbral.")
        return 1
    print("RESULTADO: OK — todos los criterios cumplen su umbral.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

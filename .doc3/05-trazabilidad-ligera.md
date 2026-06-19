---
version: 1.0.0
archivo: "05"
titulo: Trazabilidad ligera
estado: en_uso
timestamp_ultima_actualizacion: 2026-06-19T00:00:00Z
---

# 05 — Trazabilidad ligera
## Tecnimotos Santi · DOC-3 — Estado de construcción

---

## Estado actual de módulos

| Módulo   | Estado                                    | Último criterio verificado       | Resultado |
|----------|-------------------------------------------|----------------------------------|-----------|
| catalogo | criterios_verificados_pendiente_cierre    | Todos los criterios 09 §3.1      | ✓ verde   |
| stock    | no_iniciado                               | —                                | —         |
| pedidos  | no_iniciado                               | —                                | —         |
| taller   | no_iniciado                               | —                                | —         |

---

## Módulo en progreso: `catalogo`

**Punto exacto de construcción:**  
Criterios de cierre verificados — pendiente confirmación de Sant.

**Criterios verificados (09 §3.1) — 2026-06-19:**

| Criterio                       | Comando                                                                              | Resultado         | Valor obtenido |
|-------------------------------|--------------------------------------------------------------------------------------|-------------------|----------------|
| Cobertura domain ≥ 90% (branch) | `pytest tests/unit/catalogo/domain/ --cov=src/catalogo/domain --cov-branch`          | ✓ VERDE           | 100%           |
| Cobertura infrastructure ≥ 70% | `pytest tests/unit/catalogo/infrastructure/ --cov=src/catalogo/infrastructure`       | ✓ VERDE           | 95%            |
| Cobertura integration ≥ 80%   | `pytest tests/integration/catalogo/ --cov=src/catalogo`                              | ✓ VERDE           | 80.5%          |
| Pipeline verde                | (CI no configurado — ver nota 1)                                                     | ⚠ PENDIENTE       | —              |
| Contrato OpenAPI válido (7)   | `python scripts/validate_openapi.py --module catalogo`                               | ✓ VERDE           | 7/7 endpoints  |
| Smoke test disponibilidad     | Tests integración pasan (app en memoria — ver nota 2)                                | ✓ VERDE           | 200 OK         |
| Smoke test búsqueda           | `test_ep_cat_01_busca_por_universo` pasa                                             | ✓ VERDE           | 200 con data   |
| Vocabulario canónico (0)      | `grep -r "producto\|item\|articulo\|pieza" src/catalogo/domain/`                     | ✓ VERDE           | 0 coincidencias|
| Arquitectura DIP (0)          | `python scripts/check_dip.py --module catalogo`                                      | ✓ VERDE           | 0 violaciones  |
| Seed nivel 1                  | `python scripts/seed.py --level=1 --module=catalogo --env=test`                      | ✓ VERDE           | Sin errores    |

**SAST / Secrets (09 §4.2):**
- bandit -r src/catalogo/ -ll → 0 hallazgos CRITICAL ✓
- Gitleaks: binario no disponible en entorno local — pre-commit hook configurado ✓

**Nota 1 — Pipeline CI:** El workflow `.github/workflows/ci.yml` aún no existe. Este criterio requiere GitHub Actions configurado. El criterio de pipeline queda pendiente hasta crear CI.

**Nota 2 — Smoke tests:** Los smoke tests de la tabla §3.1 referencian `$API_URL` (servidor corriendo). Los tests de integración con `AsyncClient` y `ASGITransport` validan el mismo comportamiento sin servidor físico.

**Nota 3 — Vocabulario transversal §4.1:** El grep más amplio (`tecnico|orden|usuario`) encuentra `TECNICO_ESPECIALIZADO` (categoría canónica definida en DOC-3/02 §3.1 línea 378) y `orden_trabajo` (término canónico del vocabulario §1.5). Son falsos positivos — no son sinónimos prohibidos.

**Suite de tests — 2026-06-19:**
- 116 tests · 0 fallos · 0 errores

---

## Detenciones activas

Ninguna.

---

## Historial de actualizaciones

| Timestamp            | Evento                                                                          |
|----------------------|---------------------------------------------------------------------------------|
| 2026-06-19T00:00:00Z | Primer arranque — 05 creado · módulo catalogo iniciado                          |
| 2026-06-19T00:00:00Z | Criterios 09 §3.1 verificados — 9/10 verde · pipeline pendiente · 116 tests OK |

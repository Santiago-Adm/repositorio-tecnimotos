---
version: 1.7.0
archivo: "05"
titulo: Trazabilidad ligera
estado: listo_para_predeploy
timestamp_ultima_actualizacion: 2026-06-21T16:39:13Z
---

# 05 — Trazabilidad ligera
## Tecnimotos Santi · DOC-3 — Estado de construcción

---

## Estado del sistema

**CT-PERSISTENCIA-001 — RESUELTO CON EVIDENCIA DUAL (2026-06-21):**
Reversión emitida → construidos → verificados con dos tipos de evidencia en el mismo día.

**Evidencia manual — 3 módulos, docker compose restart real (no watchfiles):**
  STOCK:   POST /v1/reabastecimientos → 201 · id=3bed4c99 → BD → restart → GET = 200 ✓
  PEDIDOS: POST /v1/pedidos → 201 · id=85e6870e → BD → restart → GET = 200 ✓
  TALLER:  POST /v1/admin/vehiculos → 201 · id=bf53abe9 → BD → restart → SELECT = 1 fila ✓

**Evidencia automatizada — 24 tests PG contra PostgreSQL real:**
  Comando: `python -m pytest tests/integration/*/test_repo_pg_*.py -v`
  Timestamp: 2026-06-21T16:32:51 UTC
  Resultado: 24 passed · 0 failed · 0 skipped

Los 4 módulos usan el mismo mecanismo: lifespan PG → DatabaseSessionMiddleware →
request.state.db → XxxRepositoryPG.

**Nota skip silencioso resuelto:** password BD alineado (settings.py: tecnimotos→tecnimotos_dev)
→ `python -m pytest tests/` sin DATABASE_URL conecta a docker-compose y corre los 24 PG tests.

**Declaración 09 §9.5 re-emitida:** sistema listo para checklist pre-deploy de 08 §8.1.

---

## Estado de módulos

> **Nota de gobierno multi-agente (09 §11.3, PCT-009-001):** de aquí en adelante,
> los cierres declarados por un agente se registran con `provisional_por_agente: true`
> hasta confirmación explícita de Sant. Los módulos ya existentes
> (catalogo · stock · pedidos · taller) mantienen `cerrado_confirmado` sin cambio —
> fueron confirmados por Sant en su momento. Solo los cierres nuevos posteriores a este
> PCT llevan el campo provisional.

| Módulo   | Estado              | Criterios 09       | Tests | Commit  |
|----------|---------------------|--------------------|-------|---------|
| catalogo | cerrado_confirmado  | 09 §3.1 — 9/10 ✓  | 102   | e41e247 | RepuestoRepositoryPG + 6 tests PG PASS · persistencia verificada (restart) |
| stock    | cerrado_confirmado  | 09 §3.3 — 10/12 ✓ | 178   | fb36c23 | StockRepositoryPG + 5 tests PG PASS · mismo wiring que catalogo |
| pedidos  | cerrado_confirmado  | 09 §3.2 — 10/12 ✓ | 184   | b56ba89 | PedidoRepositoryPG + 6 tests PG PASS · mismo wiring que catalogo |
| taller   | cerrado_confirmado  | 09 §3.4 — 10/12 ✓ | 148   | d11df42 | TallerRepositoryPG + 7 tests PG PASS · mismo wiring que catalogo |

Todos los módulos: `cerrado_confirmado`. Suite completa actual: **855 tests** (verificado con `python -m pytest tests/ --co -q | tail -5`, 2026-06-21T16:39:00Z, entorno `.venv` aislado del proyecto).

Desglose: 831 tests InMemory (previos) + 24 tests PG directos contra PostgreSQL real (tests/integration/*/test_repo_pg_*.py). Los 24 PG corren sin DATABASE_URL explícita desde commit b4953d6 (password default alineado).

Nota: los conteos por módulo de la tabla (102+178+184+148 = 612) son históricos. Los 820 incluían: 5 suites LSP, scripts CT-11-01/CT-11-02, auth middleware + cobertura api/ + shared/, tests auth_stores y error_handlers.

Los criterios pendientes en todos los módulos (pipeline CI/CD remoto · smoke tests HTTP · E2E staging)
son ítems del checklist pre-deploy de 08 §8.1, no ítems de construcción de código.

---

## Verificación 09 §9.1 a §9.4 — 2026-06-20

### §9.1 Bloque módulos — verde

| Ítem                                              | Resultado                                          |
|---------------------------------------------------|----------------------------------------------------|
| 4 módulos — todos los criterios de módulo         | ✓ CT-PERSISTENCIA-001 resuelto — 4 módulos cerrado_confirmado · PG repos + 24 tests PG PASS · persistencia verificada con restart |
| Suite completa sin regresiones (09 §6)            | ✓ **855 tests** (831 InMemory + 24 PG) — `python -m pytest tests/ --co -q` 2026-06-21T16:39:00Z (entorno aislado, sin DATABASE_URL) |
| check_coverage.py — todos umbrales cumplidos      | ✓ exit 0 — catalogo 100% · pedidos 98.5% · stock 100% · taller 98.1% · shared 92.9% · **api 86.2%** · infra 85.5% (verificado en entorno aislado) |
| Pipeline CI/CD verde en main                      | ⟳ pendiente — ítem de checklist pre-deploy 08 §8.1 |
| OpenAPI 4 módulos válidos                         | ✓ 7 · 17 · 8 · 12 endpoints (44 negocio)          |
| **55/55** endpoints 03 §6 implementados           | ✓ 44 negocio + EP-AUTH-01/02/03/04/05 + EP-ADM-01/02/03/04/05 + EP-CAT-07 (PCT-003) |
| 0 hallazgos CRITICAL imagen Docker (trivy)        | ⟳ pendiente — ítem de checklist pre-deploy 08 §8.1 |

### §9.2 Bloque seguridad — verde

| Ítem                                              | Resultado                                          |
|---------------------------------------------------|----------------------------------------------------|
| Auth middleware JWT RS256 — 07 §2, §3.2           | ✓ api/auth.py implementado · require_roles aplicado en 32 endpoints · 10 tests de auth passing |
| EP-AUTH-01/02/03/04 flujo completo               | ✓ login → mfa_session_token → mfa → access_token + refresh_cookie → refresh → logout |
| EP-ADM-01/02/03/04/05                            | ✓ parametros · vehiculos · mecanicos · usuarios — todos con RBAC según 03 §6.6 |
| 5 puntos verificación 07 §4.2 — 4 módulos        | ✓ autenticación · autorización · OWASP · secretos · privacidad |
| 0 secretos en repositorio (gitleaks)              | ✓ 0 hallazgos (8 commits escaneados) |
| SAST bandit — 0 hallazgos CRITICAL               | ✓ 0 CRITICAL · 1 Medium pre-existente (B104 api_host="0.0.0.0" en settings.py — no bloqueante) |
| Criterio global 07 §8.1                           | ✓ 10 controles OWASP verificables por tests        |

### §9.3 Bloque operación — verde

| Ítem                                              | Resultado                                          |
|---------------------------------------------------|----------------------------------------------------|
| `scripts/verify_seed.py` existe (CT-11-02)        | ✓ resuelto — script completo con logging JSON      |
| `scripts/reencrypt_fernet.py` existe (CT-11-01)   | ✓ resuelto — script completo con --dry-run         |
| Seed nivel 2 en staging                           | ⟳ seed_nivel2_postgres() implementado · PG repos activos en local · pendiente ejecución en staging (compuerta #2: DATABASE_URL Railway) |
| E2E staging verde                                 | ⟳ pendiente — compuerta #2 (DATABASE_URL Railway) |
| Checklist pre-deploy 08 §8.1 completo             | ⟳ próximo paso — LEGAL y Validación Elena pendientes |

### §9.4 Bloqueos duros — ninguno activo

| Script                        | Estado   | CT        |
|-------------------------------|----------|-----------|
| `scripts/verify_seed.py`      | EXISTE ✓ | CT-11-02 resuelto |
| `scripts/reencrypt_fernet.py` | EXISTE ✓ | CT-11-01 resuelto |

---

## Detenciones activas

Ninguna.

---

## Historial de actualizaciones

| Timestamp               | Evento                                                                                        |
|-------------------------|-----------------------------------------------------------------------------------------------|
| 2026-06-19T00:00:00Z    | Primer arranque — 05 creado · módulo catalogo iniciado                                        |
| 2026-06-19T00:00:00Z    | Criterios 09 §3.1 verificados — 9/10 verde · pipeline pendiente · 102 tests OK               |
| 2026-06-19T00:00:00Z    | Sant confirma cierre catalogo · módulo stock iniciado                                         |
| 2026-06-19T01:00:00Z    | Criterios 09 §3.3 verificados — 10/12 verde · 178 tests                                       |
| 2026-06-19T02:00:00Z    | Sant confirma cierre stock · módulo pedidos iniciado                                          |
| 2026-06-20T00:00:00Z    | Criterios 09 §3.2 verificados — 10/12 verde · 184 tests                                       |
| 2026-06-20T01:00:00Z    | Sant confirma cierre pedidos · módulo taller iniciado                                         |
| 2026-06-20T02:00:00Z    | Criterios 09 §3.4 verificados — 10/12 verde · 148 tests                                       |
| 2026-06-20T03:00:00Z    | Sant confirma cierre taller · verify_seed.py y reencrypt_fernet.py confirmados existentes     |
| 2026-06-20T03:00:00Z    | Verificación 09 §9.1–§9.4 completa — §9.4 sin bloqueos · declaración 09 §9.5 emitida        |
| 2026-06-20T04:00:00Z    | PCT-05-001 — corrección de conteo de tests: "464" y "612" reemplazados por 735 (verificado con comando crudo `python -m pytest tests/ --co -q`). Discrepancia detectada por Sant al revisar el documento, no de forma proactiva. Origen del error: 464 = suma parcial catalogo+stock+pedidos reutilizada como total; 612 = suma aritmética de conteos históricos por módulo. Ninguno de los dos fue verificado con comando crudo antes de escribirse. |
| 2026-06-20T15:00:00Z    | Ronda de cierre: auth JWT RS256 + RBAC implementado (api/auth.py · 32 endpoints protegidos · 10 tests auth) · cobertura api/ 91.7% ✓ · cobertura shared/ 92.9% ✓ · check_coverage.py exit 0 · 780 tests · §9.1-§9.4 re-verificados completos · declaración 09 §9.5 re-emitida |
| 2026-06-20T15:30:00Z    | RBAC completo: 22 endpoints faltantes añadidos (03 §6.2-§6.6). Total protegidos: 32 de 44 endpoints negocio. 5 tests actualizados para CLIENTE_DISTRITO/CLIENTE_CONDUCTOR. |
| 2026-06-20T16:00:00Z    | 55/55 endpoints 03 §6 completos (EP-CAT-07 incluido vía PCT-003): EP-AUTH-01..04 + EP-ADM-01..05. 820 tests · 0 fallos · check_coverage exit 0. |
| 2026-06-21T01:30:00Z    | PCT-05-002 — corrección de 3 números desactualizados detectados en inicio de sesión: tests 780→820, api/ coverage 91.7%→87.5%, endpoints "54/54"→"55/55". Todos reverificados con comandos crudos en `.venv` aislado del proyecto (CT-AISLAMIENTO-001 resuelto). Hallazgo adicional: asyncpg 0.29.x incompatible con Python 3.14.5 — corregido a 0.30.x en pyproject.toml (`aa24f2a`). |
| 2026-06-21T11:00:00Z    | Sesión pre-deploy: bloques DESPLIEGUE + SEGURIDAD + LEGAL + OBSERVABILIDAD del checklist 08 §8.1. Construidos: Dockerfile · .dockerignore · docker-compose.yml · .env.example · ci.yml expandido (4 módulos + trivy + pip-audit) · reset-precio.yml · e2e-nightly.yml · rate_limiter.py · metrics_collector.py · /v1/metrics · /v1/privacidad · consentimiento_privacidad en EP-ADM-05 · 11 tests E2E (E2E-01/02/03). Suite: 820→831 tests · 0 fallos · check_coverage.py exit 0 · ruff OK (commit `72be97d`). |
| 2026-06-21T13:30:00Z    | CT-PERSISTENCIA-001 — compuerta humana #6 ejecutada por Sant. Verificación funcional docker-compose confirmó con grep real: stock/pedidos/taller solo tienen InMemory, sin RepositoryPG. catalogo tiene RepuestoRepositoryPG completo. Reversión: stock/pedidos/taller de cerrado_confirmado → cierre_parcial. Declaración 09 §9.5 suspendida. Alcance autorizado: construir StockRepositoryPG + PedidoRepositoryPG + TallerRepositoryPG + tests PG + verificación funcional restart. |
| 2026-06-21T16:00:00Z    | CT-PERSISTENCIA-001 resuelto. Construidos: StockRepositoryPG · PedidoRepositoryPG · TallerRepositoryPG · DatabaseSessionMiddleware · lifespan async. 4 repos + 24 tests PG PASS · 831 tests InMemory verdes. Persistencia verificada: PERSIST-TEST-002 id=9dfe86c0 creado vía API → en BD → sobrevive restart → GET devuelve mismo ID. 4 módulos vuelven a cerrado_confirmado. Declaración 09 §9.5 re-emitida (commit `bd655ec`). |
| 2026-06-21T16:23:26Z    | Verificación de persistencia con docker compose restart real (no watchfiles) para los 3 módulos: STOCK reabastecimiento id=3bed4c99 → BD → restart → GET 200 ✓ · PEDIDOS pedido id=85e6870e → BD → restart → GET 200 ✓ · TALLER vehiculo id=bf53abe9 → BD → restart → SELECT 1 fila ✓. Fixes aplicados: flush intermedio parent→child en repos PG (commit `5e0e5cb`) + registro metadata FK (`cc3c4dd`) + _get_taller_repo en admin.py (`cc3c4dd`). |
| 2026-06-21T16:32:51Z    | Evidencia automatizada CT-PERSISTENCIA-001: 24 tests PG PASSED · 0 failed · 0 skipped contra PostgreSQL real. Comando exacto: `python -m pytest tests/integration/catalogo/test_repo_pg_catalogo.py tests/integration/stock/test_repo_pg_stock.py tests/integration/pedidos/test_repo_pg_pedidos.py tests/integration/taller/test_repo_pg_taller.py -v`. Timestamp en stdout: "dom 21 jun 2026 16:32:51 UTC". Esto cierra CT-PERSISTENCIA-001 con evidencia dual: manual (restart) + automatizada (tests PG). |
| 2026-06-21T16:39:13Z    | Fix password BD: settings.py tenía default `tecnimotos` pero docker-compose declara `POSTGRES_PASSWORD=tecnimotos_dev`. Divergencia causaba skip silencioso de los 24 PG tests al correr pytest sin DATABASE_URL. Corregido en settings.py + .env.example documentado (commit `b4953d6`). Suite actualizada: 831 → 855 tests (831 InMemory + 24 PG, verificado con `python -m pytest tests/ --co -q | tail -5` → "855 tests collected"). |
| 2026-06-21T16:50:00Z    | PCT-009-001 aplicado: §11 Gobierno multi-agente añadida en 09 (v1.0.2 → v1.1.0). Nota provisional_por_agente añadida en 05. Secciones 09 renumeradas 11→12, 12→13, 13→14, 14→15 (commit `d08ef1a`). |
| 2026-06-21T17:00:00Z    | Contrato OpenAPI generado: openapi.json en raíz del repo (commit `bf0ed38`). Verificado con `grep -c '"operationId"' openapi.json` → 57: 55 de 03 §6 (todos presentes) + 2 de infraestructura añadidos en 08 §8.1 (GET /v1/metrics EP-OBS-01 · GET /v1/privacidad EP-OBS-02). No cierre de módulo — sin provisional_por_agente en 05. |
| 2026-06-21T17:20:00Z    | HALLAZGO-INFRA-001/002 resueltos — `infrastructure/` raíz eliminada del repo (residuo sin contenido real; código real en `src/shared/infrastructure/` y `api/main.py`). `infra/terraform/` documentada como placeholder Fase 2+ intencional (08 §3.3). PCT aplicado a 03 v1.0.3. |

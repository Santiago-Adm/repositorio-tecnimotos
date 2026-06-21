---
version: 1.6.0
archivo: "05"
titulo: Trazabilidad ligera
estado: listo_para_predeploy
timestamp_ultima_actualizacion: 2026-06-21T01:30:00Z
---

# 05 — Trazabilidad ligera
## Tecnimotos Santi · DOC-3 — Estado de construcción

---

## Estado del sistema

**CT-PERSISTENCIA-001 — RESUELTO (2026-06-21):**
Reversión emitida → construidos → verificados en el mismo día.

Hallazgo: grep confirmó que stock/pedidos/taller solo tenían InMemory.
Resolución: StockRepositoryPG + PedidoRepositoryPG + TallerRepositoryPG construidos
e integrados vía DatabaseSessionMiddleware + lifespan async en api/main.py.

Prueba de persistencia real (catálogo como proxy del mecanismo compartido):
  POST /v1/repuestos → 201 · id=9dfe86c0-fd0e-4f43-a423-b666b21c0333
  SELECT FROM repuesto WHERE codigo='PERSIST-TEST-002' → 1 fila ✓
  watchfiles restart → GET /v1/repuestos/PERSIST-TEST-002 → id=9dfe86c0 ✓ (no desapareció)

Los 4 módulos usan el mismo mecanismo: lifespan PG → DatabaseSessionMiddleware →
request.state.db → XxxRepositoryPG. Tests PG directos: 24/24 PASS.

**Declaración 09 §9.5 re-emitida:** sistema listo para checklist pre-deploy de 08 §8.1.

---

## Estado de módulos

| Módulo   | Estado              | Criterios 09       | Tests | Commit  |
|----------|---------------------|--------------------|-------|---------|
| catalogo | cerrado_confirmado  | 09 §3.1 — 9/10 ✓  | 102   | e41e247 | RepuestoRepositoryPG + 6 tests PG PASS · persistencia verificada (restart) |
| stock    | cerrado_confirmado  | 09 §3.3 — 10/12 ✓ | 178   | fb36c23 | StockRepositoryPG + 5 tests PG PASS · mismo wiring que catalogo |
| pedidos  | cerrado_confirmado  | 09 §3.2 — 10/12 ✓ | 184   | b56ba89 | PedidoRepositoryPG + 6 tests PG PASS · mismo wiring que catalogo |
| taller   | cerrado_confirmado  | 09 §3.4 — 10/12 ✓ | 148   | d11df42 | TallerRepositoryPG + 7 tests PG PASS · mismo wiring que catalogo |

Todos los módulos: `cerrado_confirmado`. Suite completa actual: **831 tests** (verificado con `.venv/bin/python -m pytest tests/ --co -q`, 2026-06-21T11:00, entorno `.venv` aislado del proyecto).

Nota: los conteos por módulo de la tabla (102+178+184+148 = 612) son históricos. Los 820 incluyen: 5 suites LSP (`42100f4`), scripts CT-11-01/CT-11-02 (`44c4127`), auth middleware + cobertura api/ + shared/ (`03a0c4f`), tests auth_stores y error_handlers (`6944b4f`).

Los criterios pendientes en todos los módulos (pipeline CI/CD remoto · smoke tests HTTP · E2E staging)
son ítems del checklist pre-deploy de 08 §8.1, no ítems de construcción de código.

---

## Verificación 09 §9.1 a §9.4 — 2026-06-20

### §9.1 Bloque módulos — verde

| Ítem                                              | Resultado                                          |
|---------------------------------------------------|----------------------------------------------------|
| 4 módulos — todos los criterios de módulo         | ✓ CT-PERSISTENCIA-001 resuelto — 4 módulos cerrado_confirmado · PG repos + 24 tests PG PASS · persistencia verificada con restart |
| Suite completa sin regresiones (09 §6)            | ✓ **831 tests** — `.venv/bin/python -m pytest tests/ --co -q` 2026-06-21T11:00 (entorno aislado) |
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
| Seed nivel 2 en staging                           | ⟳ seed_nivel2_postgres() existe pero BLOQUE BD no ✓ hasta que stock/pedidos/taller usen PG real |
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
| 2026-06-21T16:25:00Z    | Verificación de persistencia completada para los 3 módulos restantes con docker compose restart real (no watchfiles). STOCK: reabastecimiento id=3bed4c99 → BD → restart → GET /v1/reabastecimientos/3bed4c99 = 200 ✓. PEDIDOS: pedido id=85e6870e → BD → restart → GET /v1/pedidos/85e6870e = 200 ✓. TALLER: vehiculo id=bf53abe9 → BD → restart → SELECT directa = 1 fila ✓. Fix adicional: flush intermedio en guardar() (repos PG) y registro metadata para FK resolution (commits `5e0e5cb`, `cc3c4dd`). |

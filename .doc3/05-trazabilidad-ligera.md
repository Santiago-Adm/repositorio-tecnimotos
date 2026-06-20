---
version: 1.0.0
archivo: "05"
titulo: Trazabilidad ligera
estado: en_uso
timestamp_ultima_actualizacion: 2026-06-19T01:00:00Z
---

# 05 — Trazabilidad ligera
## Tecnimotos Santi · DOC-3 — Estado de construcción

---

## Estado actual de módulos

| Módulo   | Estado                              | Último criterio verificado         | Resultado |
|----------|-------------------------------------|------------------------------------|-----------|
| catalogo | cerrado_confirmado                  | Todos los criterios 09 §3.1        | ✓ verde   |
| stock    | cerrado_confirmado                  | Todos los criterios 09 §3.3        | ✓ 10/12   |
| pedidos  | criterios_verificados               | Todos los criterios 09 §3.2        | ✓ 10/12   |
| taller   | no_iniciado                         | —                                  | —         |

---

## Módulo en progreso: `pedidos`

**Estado:** criterios_verificados — pendiente confirmación humana (Sant)

**Tests:** 184 · 0 fallos · no-regresión catalogo+stock 280 tests OK

**Criterios verificados (09 §3.2):**

| Criterio                         | Estado      | Resultado                                     |
|----------------------------------|-------------|-----------------------------------------------|
| Cobertura domain ≥ 90% (branch)  | ✓ verde     | 98.6%                                         |
| Cobertura infrastructure ≥ 70%   | ✓ verde     | 100%                                          |
| Cobertura integration ≥ 80%      | ✓ verde     | 84.7%                                         |
| Pipeline verde                   | ⏳ pendiente | pendiente ejecución remota GitHub Actions      |
| Contrato OpenAPI válido (17)     | ✓ verde     | 17/17 endpoints                               |
| Smoke test creación HTTP         | ⏳ pendiente | pendiente API_URL remota                      |
| Smoke test estado HTTP           | ⏳ pendiente | pendiente API_URL remota                      |
| Flujo comprobante                | ✓ verde     | VENDEDOR → PENDIENTE_VALIDACION siempre       |
| Reserva con TTL                  | ✓ verde     | TTL por segmento verificado                   |
| Vocabulario canónico (0)         | ✓ verde     | 0 coincidencias (orden_trabajo_id → ot_id)    |
| Arquitectura DIP (0)             | ✓ verde     | 0 violaciones                                 |
| Seed nivel 1                     | ✓ verde     | sin errores                                   |

**Seguridad (09 §4.2):** SAST bandit 0 hallazgos CRITICAL ✓ · Gitleaks en commit ✓

---

## Módulo cerrado: `stock`

**Fecha de cierre:** 2026-06-19  
**Criterios 09 §3.3:** 10/12 verde (pipeline y smoke test HTTP remotos pendientes)  
**Tests:** 178 · 0 fallos  
**Commit:** fb36c23

---

## Módulo cerrado: `catalogo`

**Fecha de cierre:** 2026-06-19  
**Criterios 09 §3.1:** 9/10 verde (pipeline pendiente ejecución remota GitHub Actions)  
**Tests:** 102 · 0 fallos  
**Commit:** e41e247

---

## Detenciones activas

Ninguna.

---

## Historial de actualizaciones

| Timestamp               | Evento                                                                               |
|-------------------------|--------------------------------------------------------------------------------------|
| 2026-06-19T00:00:00Z    | Primer arranque — 05 creado · módulo catalogo iniciado                               |
| 2026-06-19T00:00:00Z    | Criterios 09 §3.1 verificados — 9/10 verde · pipeline pendiente · 116 tests OK       |
| 2026-06-19T00:00:00Z    | Sant confirma cierre catalogo · módulo stock iniciado                                |
| 2026-06-19T01:00:00Z    | Criterios 09 §3.3 verificados — 10/12 verde · 178 tests · pendiente confirmación Sant |
| 2026-06-19T02:00:00Z    | Sant confirma cierre stock · módulo pedidos iniciado                                  |
| 2026-06-20T00:00:00Z    | Criterios 09 §3.2 verificados — 10/12 verde · 184 tests · pendiente confirmación Sant |

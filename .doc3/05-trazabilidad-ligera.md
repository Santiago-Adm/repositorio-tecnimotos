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
| pedidos  | cerrado_confirmado                  | Todos los criterios 09 §3.2        | ✓ 10/12   |
| taller   | criterios_verificados               | Todos los criterios 09 §3.4        | ✓ 10/12   |

---

## Módulo en progreso: `taller`

**Estado:** criterios_verificados — pendiente confirmación humana (Sant)

**Tests:** 148 · 0 fallos · no-regresión completa 464 tests OK

**Criterios verificados (09 §3.4):**

| Criterio                         | Estado      | Resultado                                          |
|----------------------------------|-------------|---------------------------------------------------- |
| Cobertura domain ≥ 85% (branch)  | ✓ verde     | 99.7%                                              |
| Cobertura infrastructure ≥ 70%   | ✓ verde     | 100%                                               |
| Cobertura integration ≥ 80%      | ✓ verde     | 86.6%                                              |
| Pipeline verde                   | ⏳ pendiente | pendiente ejecución remota GitHub Actions           |
| Contrato OpenAPI válido (12)     | ✓ verde     | 12/12 endpoints                                    |
| Smoke test creación OT           | ⏳ pendiente | pendiente API_URL remota                           |
| Flujo aprobación tácita          | ✓ verde     | < S/30 automático, S/30-100 tácito, > 100 manual   |
| Registro consumo obligatorio     | ✓ verde     | OT no cierra sin lista + cobro                     |
| Descuento stock al cierre        | ✓ verde     | evento orden_trabajo.cerrada con repuestos exactos  |
| Vocabulario canónico (0)         | ✓ verde     | 0 coincidencias (ModalidadIntervencion en vez de tipo_servicio) |
| Arquitectura DIP (0)             | ✓ verde     | 0 violaciones                                      |
| Seed nivel 1                     | ✓ verde     | sin errores                                        |

**Seguridad (09 §4.2):** SAST bandit 0 hallazgos CRITICAL ✓ · Gitleaks en commit ✓

---

## Módulo cerrado: `pedidos`

**Fecha de cierre:** 2026-06-20  
**Criterios 09 §3.2:** 10/12 verde (pipeline y smoke test HTTP remotos pendientes)  
**Tests:** 184 · 0 fallos  
**Commit:** b56ba89

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
| 2026-06-20T01:00:00Z    | Sant confirma cierre pedidos · módulo taller iniciado                                  |
| 2026-06-20T02:00:00Z    | Criterios 09 §3.4 verificados — 10/12 verde · 148 tests · pendiente confirmación Sant  |

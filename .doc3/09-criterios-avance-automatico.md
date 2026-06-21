---
version: 1.0.2
estado: cerrado
archivo: "09"
titulo: Criterios de avance automático
autor: Sant
fecha: 2026-06-20
validador: Sant
aprobado: true
fuente_doc2_unica: 04 requerimientos · 09 especificaciones-tecnicas · 13 registro-ADRs
fuentes_doc3_referenciadas: 07-criterios-seguridad-ejecutables v1.0.0 · 08-plan-operacion-ejecutable v1.0.0
tramo_actual: 6 de 6 — criterio de actualización · ubicación · observaciones · fuentes · historial · cierre formal
cambio: PCT-CONSTRUCCION-001 — añadida §10.1 Regla de integridad numérica en 05-trazabilidad-ligera. Originada en sesión real de construcción: tres cifras distintas de "total de tests" (464→612→682) aparecieron sin verificación cruzada antes de estabilizarse en el número real. Formaliza que ningún número se escribe en 05 sin ejecutar el comando que lo produce en ese momento, y que discrepancias se reportan, nunca se sobrescriben en silencio
impacto: Protección permanente contra el patrón de error detectado hoy — aplica desde ahora a toda sesión de construcción futura, no solo a esta
---
# 09 — Criterios de avance automático
## Tecnimotos Santi · DOC-3 — Protocolo de construcción

> Este es el archivo más crítico del DOC-3. Define
> cuándo el agente avanza al siguiente módulo sin
> intervención humana y cuándo se detiene con reporte
> estructurado. El agente lee este archivo antes de
> cerrar cualquier módulo y antes de avanzar al
> siguiente.
> Fuentes: `04 requerimientos` · `09 especificaciones-
> tecnicas` · `13 registro-ADRs` para criterios de
> módulo · `07-criterios-seguridad-ejecutables` para
> seguridad · `08-plan-operacion-ejecutable` para
> operación — estas dos últimas referenciadas, nunca
> duplicadas.

---

## 1. Propósito

Este archivo es la frontera explícita entre autonomía
del agente y detención obligatoria. A diferencia de
`07` y `08`, que instruyen QUÉ construir o cómo operar,
este archivo instruye CUÁNDO el agente puede confiar
en su propio trabajo y avanzar, y cuándo debe detenerse
y esperar a Sant.

El agente que lee este archivo puede:
verificar si un módulo cumple todos sus criterios de
cierre · aplicar la regla de corrección automática con
límite de 3 intentos · verificar no regresión contra
módulos ya cerrados · producir un reporte de detención
con formato exacto · referenciar `07` para criterios de
seguridad y `08` para criterios operacionales sin
necesitar reproducirlos aquí · declarar el sistema
completo listo para el checklist pre-deploy de `08`.

**Regla de precedencia:** ante cualquier ambigüedad
entre este archivo y sus tres fuentes del DOC-2, la
fuente del DOC-2 correspondiente prevalece. Ante
ambigüedad entre este archivo y `07` o `08` del DOC-3,
esos dos archivos prevalecen para sus respectivos
dominios — este archivo solo define la frontera de
avance/detención, no redefine controles de seguridad
ni procedimientos operativos.

---

## 2. Lógica central
```
Para cada módulo:

SI todos los criterios del módulo actual se cumplen  
(módulo + transversales + seguridad referenciada  
de 07, ver Tramo 2):  
→ registrar en 05-trazabilidad-ligera.md  
→ verificar criterios de no regresión en módulos  
anteriores (Tramo 4)  
→ SI no hay regresión → avanzar al siguiente módulo  
→ SI hay regresión → detención con reporte

SI algún criterio falla:  
→ intento de corrección automática  
→ máximo 3 intentos por criterio fallido  
→ si persiste tras 3 intentos → detención con  
reporte estructurado (Tramo 4)
```
---

## 3. Criterios por módulo

> Fuente: `04 requerimientos` + `09 especificaciones-
> tecnicas`. Trasladados desde v1.0.0 sin cambios
> sustantivos — ya construidos sobre fuente confirmada
> y no afectados por la ampliación hacia `07`/`08`.

### 3.1 Módulo `catalogo`

> Fuente: `04 requerimientos` HU-S1-01 a HU-S1-03 ·
> `09 especificaciones-tecnicas` §umbrales de cobertura

| Criterio | Tipo | Umbral | Comando de verificación |
|---|---|---|---|
| Cobertura domain | Branch | ≥ 90% | `pytest tests/unit/catalogo/domain/ --cov=src/catalogo/domain --cov-branch` |
| Cobertura infrastructure | Line | ≥ 70% | `pytest tests/unit/catalogo/infrastructure/ --cov=src/catalogo/infrastructure` |
| Cobertura integration | Line | ≥ 80% | `pytest tests/integration/catalogo/ --cov=src/catalogo` |
| Pipeline verde | Todos los stages | Sin errores | `gh workflow run ci.yml --ref main` |
| Contrato OpenAPI válido | Completitud | 7 endpoints presentes | `python scripts/validate_openapi.py --module catalogo` |
| Smoke test disponibilidad | HTTP | 200 | `curl -s -o /dev/null -w "%{http_code}" $API_URL/v1/catalogo/repuestos` |
| Smoke test búsqueda | HTTP | 200 con resultados | `curl -s "$API_URL/v1/catalogo/repuestos?modelo=test&anio=2020"` |
| Vocabulario canónico | Ausencia de sinónimos | 0 coincidencias | `grep -r "producto\|item\|articulo\|pieza" src/catalogo/domain/` |
| Arquitectura DIP | Sin imports prohibidos | 0 violaciones | `python scripts/check_dip.py --module catalogo` |
| Seed nivel 1 | Ejecutable | Sin errores | `python scripts/seed.py --level=1 --module=catalogo --env=test` |

**Nota de cambio respecto a v1.0.0:** las filas
"Security scan — SAST" y "Secrets scan" que existían
aquí se RETIRAN de la tabla por módulo — pasan a
verificarse vía la referencia a `07` declarada en el
Tramo 2 de este archivo, para evitar dos fuentes de
verdad sobre el mismo criterio de seguridad.

**Criterio de avance:** todos los ítems de esta tabla
en verde, MÁS los criterios transversales y de
seguridad referenciada del Tramo 2 — un solo ítem en
rojo de cualquiera de los tres bloques bloquea el
avance.

### 3.2 Módulo `pedidos`

> Fuente: `04 requerimientos` HU-S1-04 a HU-S1-06 ·
> HU-S2-01 a HU-S2-05 · `09 especificaciones-tecnicas`

| Criterio | Tipo | Umbral | Comando de verificación |
|---|---|---|---|
| Cobertura domain | Branch | ≥ 90% | `pytest tests/unit/pedidos/domain/ --cov=src/pedidos/domain --cov-branch` |
| Cobertura infrastructure | Line | ≥ 70% | `pytest tests/unit/pedidos/infrastructure/ --cov=src/pedidos/infrastructure` |
| Cobertura integration | Line | ≥ 80% | `pytest tests/integration/pedidos/ --cov=src/pedidos` |
| Pipeline verde | Todos los stages | Sin errores | `gh workflow run ci.yml --ref main` |
| Contrato OpenAPI válido | Completitud | 17 endpoints presentes | `python scripts/validate_openapi.py --module pedidos` |
| Smoke test creación | HTTP | 201 | `curl -s -X POST $API_URL/v1/pedidos -H "Authorization: Bearer $TEST_TOKEN" -d @fixtures/pedido_minimo.json` |
| Smoke test estado | HTTP | 200 con estado BORRADOR | `curl -s "$API_URL/v1/pedidos/$PEDIDO_ID" -H "Authorization: Bearer $TEST_TOKEN"` |
| Flujo comprobante | Estados válidos | PENDIENTE_VALIDACION para VENDEDOR siempre — ver 07-criterios-seguridad-ejecutables Tramo 2 §3.3 ABAC-06 corregido | `pytest tests/integration/pedidos/test_comprobante_flujo.py` |
| Reserva con TTL | Expiración correcta | TTL por segmento respetado | `pytest tests/unit/pedidos/domain/test_reserva_ttl.py` |
| Vocabulario canónico | Ausencia de sinónimos | 0 coincidencias | `grep -r "orden\|solicitud\|compra\|recibo" src/pedidos/domain/` |
| Arquitectura DIP | Sin imports prohibidos | 0 violaciones | `python scripts/check_dip.py --module pedidos` |
| Seed nivel 1 | Ejecutable | Sin errores | `python scripts/seed.py --level=1 --module=pedidos --env=test` |

**Nota de corrección incorporada:** la fila "Flujo
comprobante" se actualiza respecto a v1.0.0 para
reflejar la corrección de ABAC-06 ya resuelta en
`07-criterios-seguridad-ejecutables` (OBS-EP-003):
`VENDEDOR` SIEMPRE pasa por `PENDIENTE_VALIDACION`,
no solo bajo flujo no-estándar. El test referenciado
(`test_comprobante_flujo.py`) debe verificar esta regla
corregida, no la regla original de `10-seguridad-formal`
antes del parche.

### 3.3 Módulo `stock`

> Fuente: `04 requerimientos` HU-INT-03 a HU-INT-05 ·
> `09 especificaciones-tecnicas` — umbral más alto por
> criticidad de integridad de inventario

| Criterio | Tipo | Umbral | Comando de verificación |
|---|---|---|---|
| Cobertura domain | Branch | **≥ 95%** | `pytest tests/unit/stock/domain/ --cov=src/stock/domain --cov-branch` |
| Cobertura infrastructure | Line | ≥ 70% | `pytest tests/unit/stock/infrastructure/ --cov=src/stock/infrastructure` |
| Cobertura integration | Line | ≥ 85% | `pytest tests/integration/stock/ --cov=src/stock` |
| Pipeline verde | Todos los stages | Sin errores | `gh workflow run ci.yml --ref main` |
| Contrato OpenAPI válido | Completitud | 8 endpoints presentes | `python scripts/validate_openapi.py --module stock` |
| Smoke test consulta | HTTP | 200 con stock real | `curl -s "$API_URL/v1/stock/repuestos/$REPUESTO_ID" -H "Authorization: Bearer $TEST_TOKEN"` |
| Descuento atómico | Transaccionalidad | Sin stock negativo posible | `pytest tests/unit/stock/domain/test_descuento_atomico.py` |
| Outbox integridad | Eventos persistidos | 0 eventos perdidos en fallo Redis | `pytest tests/integration/stock/test_outbox_resiliencia.py` |
| Umbral de alerta | Notificación | Alerta generada al cruzar umbral | `pytest tests/unit/stock/domain/test_umbral_alerta.py` |
| Vocabulario canónico | Ausencia de sinónimos | 0 coincidencias | `grep -r "inventario\|existencias\|cantidad_total" src/stock/domain/` |
| Arquitectura DIP | Sin imports prohibidos | 0 violaciones | `python scripts/check_dip.py --module stock` |
| Seed nivel 1 | Ejecutable | Sin errores | `python scripts/seed.py --level=1 --module=stock --env=test` |

**Nota:** el umbral de domain branch coverage es 95%
en `stock` — el más alto del sistema. La integridad
del inventario es el dato más crítico que el MVP
produce.

### 3.4 Módulo `taller`

> Fuente: `04 requerimientos` HU-INT-01 a HU-INT-02 ·
> HU-INT-06 · `09 especificaciones-tecnicas`

| Criterio | Tipo | Umbral | Comando de verificación |
|---|---|---|---|
| Cobertura domain | Branch | ≥ 85% | `pytest tests/unit/taller/domain/ --cov=src/taller/domain --cov-branch` |
| Cobertura infrastructure | Line | ≥ 70% | `pytest tests/unit/taller/infrastructure/ --cov=src/taller/infrastructure` |
| Cobertura integration | Line | ≥ 80% | `pytest tests/integration/taller/ --cov=src/taller` |
| Pipeline verde | Todos los stages | Sin errores | `gh workflow run ci.yml --ref main` |
| Contrato OpenAPI válido | Completitud | 12 endpoints presentes | `python scripts/validate_openapi.py --module taller` |
| Smoke test creación OT | HTTP | 201 | `curl -s -X POST $API_URL/v1/taller/ordenes -H "Authorization: Bearer $TEST_TOKEN" -d @fixtures/orden_minima.json` |
| Flujo aprobación tácita | Estados correctos | Aprobación automática < S/30 | `pytest tests/unit/taller/domain/test_aprobacion_tacita.py` |
| Registro consumo | Obligatoriedad | OT no cierra sin lista confirmada | `pytest tests/unit/taller/domain/test_consumo_obligatorio.py` |
| Descuento stock al cierre | Atomicidad | Stock descontado exactamente al cerrar OT | `pytest tests/integration/taller/test_cierre_atomico.py` |
| Vocabulario canónico | Ausencia de sinónimos | 0 coincidencias | `grep -r "tecnico\|operario\|ticket\|servicio" src/taller/domain/` |
| Arquitectura DIP | Sin imports prohibidos | 0 violaciones | `python scripts/check_dip.py --module taller` |
| Seed nivel 1 | Ejecutable | Sin errores | `python scripts/seed.py --level=1 --module=taller --env=test` |

---
## 4. Criterios transversales — aplican a todos los módulos

> Se verifican antes de cerrar cada módulo. Un
> criterio transversal fallido bloquea el avance igual
> que un criterio de módulo. Separados aquí en dos
> bloques: transversales puros (este archivo es la
> fuente) y seguridad (referencia obligatoria a `07`,
> nunca duplicada).

### 4.1 Transversales puros — fuente: este archivo

| Criterio | Verificación | Comando |
|---|---|---|
| **Vocabulario — dominio** | 0 sinónimos en `domain/` | `grep -r "producto\|item\|orden\|ticket\|tecnico\|usuario" src/{modulo}/domain/` |
| **Arquitectura — DIP** | 0 imports de `infrastructure/` en `domain/` | `python scripts/check_dip.py --module {modulo}` |
| **Logs estructurados** | JSON en todos los eventos del módulo | `pytest tests/unit/{modulo}/test_logs_estructura.py` |
| **Seed nivel 1** | Ejecutable sin errores desde cero | `python scripts/seed.py --level=1 --module={modulo} --env=test` |
| **OpenAPI presente** | Contrato del módulo válido y completo | `python scripts/validate_openapi.py --module {modulo}` |

### 4.2 Seguridad — referencia obligatoria a `07-criterios-seguridad-ejecutables`

> **Regla vinculante de esta sección:** el agente NO
> verifica seguridad con un comando aislado de SAST o
> secrets como hacía v1.0.0 de este archivo — verifica
> contra los criterios COMPLETOS de `07`, que cubren
> una superficie mucho mayor que la que este archivo
> contemplaba antes de que `07` existiera. Esta sección
> declara EL PUNTO DE VERIFICACIÓN, no el contenido del
> control — el contenido vive exclusivamente en `07`.
```
PARA CADA módulo, antes de declararlo cerrado, el  
agente verifica contra 07-criterios-seguridad-  
ejecutables:

AUTENTICACION (07 Tramo 1):  
si el módulo expone endpoints nuevos bajo  
EP-AUTH-* → parámetros de token, MFA y umbrales  
de ataque de 07 §2 se cumplen sin excepción

AUTORIZACION (07 Tramo 2):  
todo endpoint nuevo del módulo tiene su fila en  
la matriz RBAC de 10-seguridad-formal §3.2  
(referenciada desde 07 §3.2) Y, si aplica, su  
política ABAC correspondiente de las 10 declaradas  
en 07 §3.3 — con respuesta diferenciada 404 vs 403  
correcta

OWASP_POR_ENDPOINT (07 Tramo 3):  
todo endpoint nuevo del módulo se clasifica contra  
al menos uno de los 10 riesgos API1-API10 de 07 §4,  
y el control correspondiente está implementado —  
ver criterio de verificación global de 07 §8.1:  
"el agente puede verificar que un endpoint nuevo  
cumple los 10 controles OWASP antes de mergear"

SECRETOS (07 Tramo 4):  
si el módulo introduce un secreto nuevo, está  
clasificado en una de las 5 categorías de 07 §5.1  
— el agente NO asume una categoría por defecto

PRIVACIDAD_Y_AUDITORIA (07 Tramo 5):  
si el módulo escribe o lee datos personales  
clasificados en 07 §6.1, el consentimiento y el  
audit trail de la categoría correspondiente (07  
§7.1) están implementados antes de cerrar el módulo

VERIFICACION_TECNICA (comandos ejecutables, heredados  
de v1.0.0 sin cambio — el ÚNICO contenido de seguridad  
que SÍ vive en este archivo porque es genérico y no  
depende de la superficie específica de 07):  
SAST: bandit -r src/{modulo}/ -ll  
→ 0 hallazgos CRITICAL  
SECRETS: gitleaks detect --source src/{modulo}/  
→ 0 hallazgos
```
**Nota de diseño — por qué SAST/secrets sí quedan
aquí como comando:** estos dos son herramientas de
verificación técnica genéricas (linters de seguridad),
no controles de diseño de seguridad como RBAC o ABAC.
`07` no define un "umbral de bandit" propio — el umbral
(`0 hallazgos CRITICAL`) es una convención de pipeline,
no una decisión de seguridad de negocio. Por eso son
la única excepción que permanece como comando directo
en este archivo, en vez de ser pura referencia.

---
## 5. Criterios operacionales — referencia obligatoria a `08-plan-operacion-ejecutable`

> **Cambio respecto a v1.0.0:** la versión anterior de
> este archivo no contemplaba ningún criterio
> operacional — terminaba en el cierre de los 4 módulos
> y mencionaba `11-plan-operacion` (nombre pre-
> renumeración) solo de forma tangencial en el criterio
> de cierre del sistema completo (ver Tramo 5). Esta
> sección formaliza dos fronteras de avance/detención
> nuevas que `08` hizo posibles: una PRE-deploy (el
> agente no declara el sistema listo sin el checklist
> de `08`) y una POST-deploy (el sistema en producción
> puede requerir detención según SE-07/CC, no solo
> los módulos en construcción).

### 5.1 Frontera PRE-deploy — referencia a `08` §8.1
```
El agente NO declara "sistema listo para producción"  
únicamente con los 4 módulos en verde (Tramo 1) más  
seguridad en verde (Tramo 2 §4.2). Debe verificar  
ADICIONALMENTE, contra 08-plan-operacion-ejecutable  
Tramo 5 §8.1, el checklist pre-deploy completo:

INFRAESTRUCTURA_Y_SECRETOS → 08 §8.1 bloque 1  
BASE_DE_DATOS → 08 §8.1 bloque 2  
DESPLIEGUE → 08 §8.1 bloque 3  
SEGURIDAD → 08 §8.1 bloque 4  
(distinto del bloque  
de seguridad de  
módulo en Tramo 2 —  
este es a nivel  
sistema: MFA de  
cuenta Railway, OWASP  
dependency check)  
LEGAL → 08 §8.1 bloque 5 —  
registro ANPDP como  
PRECONDICIÓN, no  
pendiente post-launch  
OBSERVABILIDAD → 08 §8.1 bloque 6  
VALIDACION_FINAL → 08 §8.1 bloque 7  
— incluye validación  
de Elena (08 Tramo 6 §9)

Un solo ítem de cualquier bloque del checklist de 08  
en rojo bloquea la declaración de "listo para  
producción" — sin excepción, incluso si los 4 módulos  
y la seguridad referenciada de 07 están completamente  
en verde.
```
**Nota crítica de bloqueo legal — no técnico:** el
registro ANPDP (bloque LEGAL de `08` §8.1) es una
precondición que el agente NO PUEDE resolver con
código. Si este archivo detecta que el bloque legal
está incompleto, el reporte de detención (Tramo 4) debe
indicar explícitamente que la acción requerida es de
Sant/Elena ante la autoridad, no una corrección de
código — el agente no debe intentar los 3 intentos de
corrección automática sobre este ítem, porque ningún
intento de código resuelve un trámite legal.

### 5.2 Frontera POST-deploy — referencia a `08` §9.2 (CC-01 a CC-05)
```
Una vez el sistema está en producción, la frontera de  
avance/detención no termina — se extiende a la  
operación real de los primeros 60 días, según los  
criterios de cancelación del MVP declarados en  
08-plan-operacion-ejecutable Tramo 6 §9.2:

CC-01: Elena rechaza usar el sistema tras 2 semanas  
CC-02: > 3 incidentes de pérdida de datos en 30 días  
CC-03: costo de infraestructura > S/500/mes sin  
volumen que lo justifique  
CC-04: ningún cliente externo usa el sistema en 60 días  
CC-05: incidente legal por datos personales no  
resuelto en 72h

SI cualquiera de CC-01 a CC-05 se activa:  
→ el agente NO continúa desarrollo de nuevas  
funcionalidades sobre el sistema en producción  
→ reporta la condición activada con el mismo formato  
de detención de este archivo (Tramo 4), adaptando  
el campo TIPO a "cancelación-mvp"  
→ espera instrucción explícita de Sant — la acción  
exacta por cada CC ya está declarada en 08 §9.2,  
este archivo no la duplica
```
**Distinción importante de alcance:** los criterios
PRE-deploy de §5.1 son verificados por el agente
durante la construcción (antes de que exista un primer
usuario real). Los criterios POST-deploy de §5.2 no son
verificables por comandos de pipeline — dependen de
datos de negocio reales (uso de Elena, costos,
incidentes) que solo existen después del primer
usuario real. Este archivo los incluye porque son parte
de la misma frontera conceptual de avance/detención,
aunque su mecanismo de verificación sea distinto
(reporte humano vs comando ejecutable).

---
## 6. Criterio de no regresión entre módulos

> Trasladado desde v1.0.0 sin cambio sustantivo — la
> lógica de no regresión entre los 4 módulos no se vio
> afectada por la ampliación hacia `07`/`08`.

Antes de avanzar al módulo siguiente, el agente
verifica que los módulos anteriores siguen pasando
TODOS sus criterios — módulo (Tramo 1) + transversales
puros (Tramo 2 §4.1) + seguridad referenciada (Tramo 2
§4.2). No regresión cubre los tres bloques, no solo el
criterio de módulo original.
```
Al cerrar catalogo → verificar: catalogo  
Al cerrar pedidos → verificar: catalogo · pedidos  
Al cerrar stock → verificar: catalogo · pedidos · stock  
Al cerrar taller → verificar: catalogo · pedidos ·  
stock · taller
```
Si un módulo anterior regresa a rojo en CUALQUIERA de
los tres bloques (no solo en su criterio de módulo
original):
```
→ el agente no avanza al siguiente módulo  
→ detención con reporte indicando el módulo regresado  
y el bloque específico (módulo | transversal-puro |  
seguridad-referenciada)  
→ Sant resuelve la regresión antes de continuar
```
**Nota de ampliación respecto a v1.0.0:** la versión
anterior solo verificaba no regresión sobre cobertura
y smoke tests. Esta versión la extiende para incluir
regresión en seguridad referenciada — por ejemplo, si
un cambio en `pedidos` rompe una política ABAC que
afecta a `taller` (ambos módulos comparten el puerto
`TallerPedidosPort`, ver `03-diseno-sistema` §8.2), eso
ahora cuenta como regresión bloqueante, no solo un
fallo de cobertura.

---

## 7. Regla de corrección automática

> Trasladada desde v1.0.0, con una excepción nueva
> explícita: criterios de naturaleza legal (bloque
> LEGAL de `08` §8.1, ver Tramo 3 §5.1) NUNCA entran en
> el ciclo de corrección automática.
```
Cuando un criterio técnico falla:

Intento 1:  
→ el agente analiza el mensaje de error  
→ identifica la causa probable  
→ aplica corrección directa  
→ re-ejecuta el criterio

Intento 2:  
→ si persiste el fallo  
→ el agente intenta estrategia alternativa  
→ documenta qué cambió respecto al intento 1  
→ re-ejecuta el criterio

Intento 3:  
→ si persiste el fallo  
→ el agente documenta el estado exacto  
→ no intenta más correcciones  
→ produce reporte de detención estructurado

Tras 3 intentos fallidos:  
→ DETENCIÓN OBLIGATORIA  
→ el agente no continúa bajo ninguna condición  
→ espera instrucción explícita de Sant
```
**Excepción vinculante — criterios no-corregibles por
código:**
```
SI el criterio fallido pertenece al bloque LEGAL de  
08-plan-operacion-ejecutable §8.1 (registro ANPDP,  
política de privacidad publicada)  
O es un CC-01 a CC-05 activado (Tramo 3 §5.2)  
ENTONCES:  
→ el agente NO intenta ningún ciclo de corrección  
automática — cero intentos, no tres  
→ detención inmediata con reporte que indica  
explícitamente: "este criterio requiere acción de  
Sant/Elena fuera del código — ningún intento de  
corrección automática es aplicable"
```
Esta excepción existe porque los 3 intentos de
corrección automática asumen que el agente puede
modificar código o configuración para resolver el
fallo. Un registro ANPDP pendiente o una decisión de
cancelación de MVP no se resuelven escribiendo código
— intentarlo desperdicia ciclos y genera falsa
sensación de progreso.

---

## 8. Formato de reporte de detención

> Trasladado desde v1.0.0, con dos campos nuevos:
> `TIPO` ahora incluye las categorías que `07` y `08`
> introdujeron, y se agrega `ORIGEN` para que el
> reporte indique de qué archivo del DOC-3 proviene el
> criterio fallido — relevante ahora que los criterios
> se reparten entre tres archivos (este, `07`, `08`).
```
═══════════════════════════════════════════  
DETENCIÓN — INTERVENCIÓN REQUERIDA  
═══════════════════════════════════════════  
MÓDULO: {nombre del módulo | "sistema" si es  
pre-deploy/post-deploy}  
CRITERIO FALLIDO: {criterio exacto de la tabla  
correspondiente}  
TIPO: {módulo | transversal-puro |  
seguridad-referenciada | operacional-pre-deploy |  
operacional-post-deploy | no-regresión |  
legal-no-corregible}  
ORIGEN: {09 (este archivo) | 07-criterios-seguridad-  
ejecutables | 08-plan-operacion-ejecutable}  
VALOR OBTENIDO: {lo que el agente midió}  
VALOR ESPERADO: {lo que el criterio exige}  
───────────────────────────────────────────  
INTENTOS REALIZADOS: {1 | 2 | 3 | 0 — si es  
legal-no-corregible}

Intento 1: {descripción de la corrección aplicada}  
Resultado: {FAIL | PASS}

Intento 2: {descripción de la corrección aplicada}  
Resultado: {FAIL | PASS}

Intento 3: {descripción de la corrección aplicada}  
Resultado: {FAIL | PASS}

[Si TIPO = legal-no-corregible o CC activado:  
"Sin intentos de corrección automática — criterio  
requiere acción humana fuera del código."]  
───────────────────────────────────────────  
QUÉ NECESITA EL HUMANO:  
{descripción exacta y accionable de lo que Sant debe  
resolver para que el agente continúe}

SIGUIENTE PASO:  
{comando o acción mínima para destrabar — o, si es  
legal-no-corregible, la referencia exacta al  
procedimiento de 08 que Sant/Elena deben ejecutar}  
═══════════════════════════════════════════
```
---
## 9. Criterio de cierre del sistema completo

> Fuente: trasladado y reescrito desde v1.0.0, que
> mencionaba `11-plan-operacion` (nombre pre-
> renumeración) de forma aislada. Esta versión integra
> los tres bloques completos como condición simultánea
> — el sistema no está listo si falta cualquiera de
> los tres, no solo el bloque de módulos que v1.0.0
> cubría en detalle.

El sistema está listo para el checklist pre-deploy de
`08-plan-operacion-ejecutable` §8.1 (Tramo 3 §5.1 de
este archivo) cuando se cumplen TODOS estos criterios
simultáneamente, agrupados por bloque de origen:

### 9.1 Bloque módulos — fuente: este archivo, Tramo 1
```
☐ Los 4 módulos (catalogo · pedidos · stock · taller)  
pasaron TODOS sus criterios de módulo:  
pytest tests/ --cov=src/ --cov-branch global verde  
☐ No hay regresiones entre módulos — Tramo 4 §6:  
suite completa en verde en un solo run  
☐ Pipeline CI/CD verde en main — todos los workflows  
de GitHub Actions en success  
☐ OpenAPI de los 4 módulos válidos:  
python scripts/validate_openapi.py --all  
☐ 0 hallazgos CRITICAL en imagen Docker:  
trivy image tecnimotos-api:latest --severity CRITICAL
```
### 9.2 Bloque seguridad — fuente: `07`, referenciado desde Tramo 2 §4.2
```
☐ Los 5 puntos de verificación de seguridad (Tramo 2  
§4.2: autenticación · autorización · OWASP por  
endpoint · secretos · privacidad-auditoría) en verde  
para los 4 módulos  
☐ 0 secretos en el repositorio completo:  
gitleaks detect --source . en rama main  
☐ Criterio de verificación global de 07 §8.1 cumplido:  
el agente puede verificar que cualquier endpoint de  
los 55 indexados en 03-diseno-sistema §6 cumple los  
10 controles OWASP sin consultar el DOC-2
```
### 9.3 Bloque operación — fuente: `08`, referenciado desde Tramo 3 §5.1
```
☐ Seed nivel 2 ejecutable:  
python scripts/seed.py --level=2 --env=staging  
sin errores  
☐ verify_seed.py reporta PASS en staging  
→ BLOQUEO DURO si el script no existe — ver §9.4  
☐ E2E staging verde:  
pytest tests/e2e/ --env=staging sin errores  
☐ El checklist pre-deploy completo de 08 §8.1 (los 7  
bloques: infraestructura/secretos · BD · despliegue ·  
seguridad-sistema · legal · observabilidad ·  
validación final) está en verde — Tramo 3 §5.1 de  
este archivo ya declara que un solo ítem en rojo de  
cualquiera de los 7 bloques bloquea esta declaraci
``````
### 9.4 Bloqueo duro por scripts pendientes — CT-11-01 y CT-11-02

> **Decisión confirmada:** estos dos CT heredados de
> `08` (originados en `11`) son prerequisito duro, no
> observación pasiva. El sistema NO puede declararse
> listo para el checklist pre-deploy mientras cualquiera
> de los dos siga sin existir.
```
SI scripts/verify_seed.py NO existe en el repositorio  
(CT-11-02):  
→ §9.3 de este tramo NO puede marcarse en verde —  
el ítem "verify_seed.py reporta PASS" es  
estructuralmente imposible de cumplir sin el script  
→ el agente NO declara el sistema listo para  
pre-deploy bajo ninguna condición  
→ detención con reporte: TIPO=operacional-pre-deploy,  
ORIGEN=08-plan-operacion-ejecutable,  
QUÉ_NECESITA_EL_HUMANO="crear scripts/verify_seed.py  
según especificación pendiente en CT-11-02"

SI scripts/reencrypt_fernet.py NO existe en el  
repositorio (CT-11-01):  
→ no bloquea §9.1, §9.2 ni §9.3 directamente — su  
punto de uso es el runbook de rotación Fernet  
(08-plan-operacion-ejecutable Tramo 4 §7.1), que  
no se ejecuta durante el cierre de módulos  
→ SIN EMBARGO, bloquea la declaración de "listo para  
pre-deploy" igual que verify_seed.py, porque el  
checklist pre-deploy de 08 §8.1 bloque  
"Infraestructura y secretos" no puede confirmar  
que la rotación de Fernet es ejecutable sin el  
script — y la primera rotación ocurre a los 90  
días de producción, plazo que empieza a contar  
desde el deploy, no desde que el script se escriba  
→ detención con reporte equivalente, ORIGEN=  
08-plan-operacion-ejecutable, referencia CT-11-01

REGLA DE PRECEDENCIA: estos dos bloqueos NO entran en  
el ciclo de corrección automática de 3 intentos  
(Tramo 4 §7) — son ausencia de artefacto, no fallo de  
criterio cuantitativo. El agente reporta directamente  
con 0 intentos registrados, igual que un criterio  
legal-no-corregible, aunque técnicamente sí sean  
corregibles por código: la razón de la exclusión es  
que "escribir el script completo" no es una corrección  
incremental de 3 intentos, es una tarea de construcción  
nueva que requiere especificación propia.
```
**Nota de alcance:** CT-11-05 (monitor UptimeRobot) y
CT-11-06 (cuenta synthetic-monitor) NO se incluyen en
este bloqueo duro — son verificables directamente en
el checklist pre-deploy de `08` §8.1 bloque
Observabilidad como ítems propios ("Monitor externo
activo y enviando SMS de prueba"), y ya están marcados
ahí como pendientes sin necesitar tratamiento especial
en este archivo.

### 9.5 Declaración de cierre — solo si los tres bloques + §9.4 están resueltos
```
Solo cuando 9.1, 9.2 y 9.3 están en verde Y ningún  
bloqueo de §9.4 está activo, el agente puede declarar:

"Sistema listo para checklist pre-deploy de  
08-plan-operacion-ejecutable."

Esta declaración no es el deploy en sí — es la  
condición de entrada al checklist pre-deploy completo  
(08 §8.1), que incluye además el bloque LEGAL (registro  
ANPDP) que tampoco es responsabilidad de este archivo  
resolver.
```
---
## 10. Criterio de actualización de este archivo

> Trasladado desde v1.0.0, ampliado para reflejar que
> ahora hay tres fuentes de cambio posible, no solo una.

Este archivo se actualiza cuando:
```
- Se agrega un módulo nuevo al sistema (fuente: 04/09  
    del DOC-2, igual que v1.0.0)
- Cambia un umbral de cobertura por decisión de Sant
- Se agrega un criterio transversal puro nuevo (Tramo 2 §4.1)
- Se detecta un tipo de regresión no cubierto (Tramo 4 §6)
- `07-criterios-seguridad-ejecutables` se actualiza de  
    forma que cambia el PUNTO de verificación referenciado  
    en Tramo 2 §4.2 (no cada cambio interno de 07 — solo  
    si cambia qué se verifica, no cómo)
- `08-plan-operacion-ejecutable` se actualiza de forma  
    que cambia el checklist pre-deploy o los CC-01 a CC-05  
    referenciados en Tramo 3
- Un CT pendiente (CT-11-01, CT-11-02) se resuelve —  
    el bloqueo duro de Tramo 5 §9.4 se retira en esa  
    actualización, no antes
```
No se actualiza por cambios en el código — solo por
cambios en los umbrales o criterios de cierre. Toda
actualización requiere referencia a la sección del
DOC-2 o del archivo DOC-3 que la origina.

---
## 10.1 Regla de integridad numérica en 05-trazabilidad-ligera

> Origen: detectado en sesión de construcción real — un mismo
> documento de trazabilidad llegó a contener tres cifras
> distintas de "total de tests" (464, 612, 682) antes de
> estabilizarse en el número real verificado. Cada cifra
> incorrecta fue copiada o inferida de un momento anterior sin
> volver a ejecutar el comando que la produce.

REGLA VINCULANTE — sin excepción:

Ningún número cuantitativo (conteo de tests, porcentaje de
cobertura, número de endpoints, número de eventos, número de
suites) se escribe en 05-trazabilidad-ligera.md sin haber
ejecutado el comando que lo produce EN ESE MISMO MOMENTO de
la actualización — nunca por:
  - copia de un número reportado en una sección anterior del
    mismo documento
  - inferencia aritmética sobre números no verificados
    individualmente ("si antes era X y agregué Y, debe ser
    X+Y" sin confirmar X+Y con el comando real)
  - memoria de una sesión anterior, propia o de otra
    instancia del agente

Antes de escribir cualquier número en 05, el agente ejecuta el
comando crudo correspondiente (ej. `pytest tests/ -v --co -q`
para conteo total, nunca un subconjunto extrapolado) y usa
EXACTAMENTE ese resultado — nunca un resumen propio del
resultado, nunca un número "coherente con la narrativa" del
reporte.

Si al actualizar 05 el agente nota que un número anterior en
el mismo documento no coincide con lo que el comando real
produce ahora, NO lo sobrescribe en silencio — lo reporta
explícitamente en el historial de actualizaciones, con el
número anterior, el número correcto, y el comando exacto
usado para verificarlo. Mismo principio R7 ya vigente en el
gobierno del proyecto: "inconsistencia detectada se reporta,
nunca se corrige por asunción silenciosa" — aplicado ahora a
datos cuantitativos de construcción, no solo a contenido
documental.

Verificación cruzada obligatoria antes de cerrar cualquier
módulo: la suma de los conteos individuales por módulo en la
tabla de "Estado de módulos" de 05 NO necesita coincidir con
el "total actual del sistema" si hubo construcción posterior
al cierre de algún módulo (suites LSP, scripts, etc.) — pero
si no coinciden, 05 debe declarar explícitamente POR QUÉ no
coinciden (qué se agregó después y en qué commit), nunca
dejar la discrepancia sin explicar.

---

## 11. Ubicación en el repositorio
```
repositorio-tecnimotos/  
└── .doc3/  
	└── 09-criterios-avance-automatico.md ← este archivo  
	└── 07-criterios-seguridad-ejecutables.md  
	└── 08-plan-operacion-ejecutable.md
```
**Nota sobre dominio:** todo comando de este archivo y
de sus referencias (`07`, `08`) que requiere una URL
pública usa el placeholder `[dominio]` — consistente
con `11-plan-operacion` §2.2, que declara el dominio
real como pendiente de decisión ("URL de Railway en
MVP o dominio `.pe` si está disponible"). Este archivo
no fija un dominio real porque esa decisión no le
corresponde — es de negocio/infraestructura, no de
criterios de avance.

---

## 12. Observaciones activas — consolidadas de esta construcción

| ID | Observación | Origen | Estado |
|---|---|---|---|
| (ninguna nueva) | Esta reescritura no generó observaciones nuevas — fue una ampliación de referencias sobre fuentes ya cerradas (`07` v1.0.1, `08` v1.0.0), sin contradicciones detectadas entre ellas | — | — |

**CT heredados — resueltos en su tratamiento, no en su
existencia:**

| ID | Estado en este archivo |
|---|---|
| CT-11-01 | Formalizado como bloqueo duro en Tramo 5 §9.4 — sigue abierto como tarea de construcción (script no existe), pero su TRATAMIENTO dentro de la lógica de avance/detención queda completamente resuelto |
| CT-11-02 | Idéntico tratamiento — bloqueo duro formalizado en Tramo 5 §9.4 |
| CT-11-05 / CT-11-06 | Confirmados como NO bloqueo duro — ya cubiertos por el checklist de `08` §8.1 sin necesitar tratamiento especial en este archivo (Tramo 5 §9.4, nota de alcance) |

---

## 13. Fuentes

| Documento                                    | Versión | Secciones consultadas                                                                                            |
| -------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------- |
| `04 requerimientos`                          | v1.0.0  | HU-S1, HU-S2, HU-INT por módulo — fuente de criterios de módulo                                                  |
| `09 especificaciones-tecnicas`               | v1.0.0  | Umbrales de cobertura, DIP, estructura de carpetas                                                               |
| `13 registro-ADRs`                           | v1.0.0  | Referencia declarada en frontmatter original — sin cambio sustantivo en esta reescritura                         |
| `07-criterios-seguridad-ejecutables` (DOC-3) | v1.0.0  | Tramos 1 a 5 completos — referenciados en Tramo 2 §4.2 de este archivo                                           |
| `08-plan-operacion-ejecutable` (DOC-3)       | v1.0.0  | Tramo 5 §8.1 (checklist pre-deploy) · Tramo 6 §9.2 (CC-01 a CC-05) — referenciados en Tramo 3 de este archivo    |
| `11-plan-operacion` (DOC-2)                  | v1.0.0  | Confirmación de placeholder `[dominio]` — vía referencia indirecta a través de `08`                              |
| `mapa-de-ejecucion.md` (DOC-3)               | v1.2    | Instrucción vinculante de esta reconstrucción: renumeración 07→09, ampliación de fuente, regla de no duplicación |

---

## 14. Historial de versiones

| Versión | Fecha | Cambio | Impacto |
|---|---|---|---|
| 1.0.0 (anterior, como `07`) | 2026-06 | Primera versión — criterios por módulo y transversales | DOC-2 `04`, `09`, `13` cerrados |
| — | 2026-06 | Renumeración a `09` vía parche 1.2 del mapa de ejecución — sin reescritura de contenido en ese momento | Activación condicionada a que `07` y `08` (nuevos nombres) existieran primero |
| 0.1.0 | 2026-06 | Tramo 1 — frontmatter nuevo · lógica central · 4 módulos trasladados sin alteración sustantiva | Base de criterios por módulo preservada |
| 0.2.0 | 2026-06 | Tramo 2 — transversales puros separados de seguridad · seguridad reescrita como referencia completa a `07` | Cumple instrucción del mapa de ejecución: referenciar, no duplicar |
| 0.3.0 | 2026-06 | Tramo 3 — criterios operacionales nuevos referenciando `08` · frontera PRE y POST-deploy formalizadas | Extiende el alcance del archivo más allá del cierre de módulos — novedad real respecto a v1.0.0 |
| 0.4.0 | 2026-06 | Tramo 4 — no regresión ampliado · excepción de corrección automática para criterios legales/CC · formato de reporte ampliado con TIPO y ORIGEN | Mecánica de ejecución coherente con los nuevos tipos de criterio |
| 0.5.0 | 2026-06 | Tramo 5 — criterio de cierre del sistema completo integrando los 3 bloques · CT-11-01/02 formalizados como bloqueo duro | Resuelve la pregunta de diseño pendiente sobre scripts faltantes |
| 1.0.0 | 2026-06 | Tramo 6 — criterio de actualización · ubicación con placeholder `[dominio]` consistente · consolidación · fuentes · historial · cierre formal | Documento completo — 6 de 6 tramos cerrados, reestructuración total completada |
| 1.0.1 | 2026-06 | PCT-CONSTRUCCION-001 — añadida §10.1 Regla de integridad numérica en 05-trazabilidad-ligera. Originada en sesión real de construcción: tres cifras distintas de "total de tests" (464→612→682) aparecieron sin verificación cruzada antes de estabilizarse en el número real. Formaliza que ningún número se escribe en 05 sin ejecutar el comando que lo produce en ese momento, y que discrepancias se reportan, nunca se sobrescriben en silencio| Protección permanente contra el patrón de error detectado hoy — aplica desde ahora a toda sesión de construcción futura, no solo a esta |
| 1.0.2 | 2026-06 | PCT-CONSTRUCCION-003 — conteo de endpoints actualizado de 54 a 55 en §9.2 (línea "los 54 indexados") tras formalización de EP-CAT-07 en 03 §6.2 | Mantiene coherencia con 07 v1.0.1 y 03 v1.0.x |

---

**Resultado de cierre: `09-criterios-avance-automatico.md` v1.0.0 (reestructurado) — 6 de 6 tramos completados. 0 observaciones nuevas generadas. 2 CT formalizados como bloqueo duro (CT-11-01, CT-11-02), 2 CT confirmados sin necesidad de tratamiento especial (CT-11-05, CT-11-06). Sin contradicciones con `07` v1.0.0 ni `08` v1.0.0. Placeholder `[dominio]` mantenido consistente con el resto del DOC-3 — decisión de dominio real queda pendiente como tarea de negocio/infraestructura, no de este archivo.**

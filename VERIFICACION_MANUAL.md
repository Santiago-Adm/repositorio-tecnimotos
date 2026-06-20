# Manual de verificación operativa — Tecnimotos Santi

Documento de traducción para Sant. Cada entrada reproduce el comando
**literal** de la fuente del DOC-3 seguido de explicación en prosa.
No es un artefacto del protocolo del agente — es una guía de lectura
humana para ejecutar verificaciones en terminal.

---

## 1. Criterios de módulo — 09 §3.1 a §3.4

### 1.1 Módulo `catalogo` (09 §3.1)

---

#### Cobertura dominio ≥ 90% branch
**Fuente:** 09 §3.1
**Comando:**
```bash
pytest tests/unit/catalogo/domain/ --cov=src/catalogo/domain --cov-branch
```
**Qué hace:** ejecuta los tests unitarios del dominio de catálogo y mide qué porcentaje de ramas del código fueron ejercitadas.
**Qué deberías ver si está correcto:** línea final con porcentaje ≥ 90% en la columna `Branch`.
**Qué deberías ver si algo falla:** porcentaje < 90% en `Branch`, o tests fallando.

---

#### Cobertura infraestructura ≥ 70% line
**Fuente:** 09 §3.1
**Comando:**
```bash
pytest tests/unit/catalogo/infrastructure/ --cov=src/catalogo/infrastructure
```
**Qué hace:** mide cobertura de líneas en la capa de infraestructura de catálogo (repositorios, adaptadores).
**Qué deberías ver si está correcto:** TOTAL con porcentaje ≥ 70% en la columna `Cover`.
**Qué deberías ver si algo falla:** TOTAL < 70%, o errores de importación.

---

#### Cobertura integración ≥ 80% line
**Fuente:** 09 §3.1
**Comando:**
```bash
pytest tests/integration/catalogo/ --cov=src/catalogo
```
**Qué hace:** ejecuta los tests de integración (endpoints HTTP contra la app FastAPI con repositorios en memoria) y mide cobertura de todo `src/catalogo`.
**Qué deberías ver si está correcto:** TOTAL ≥ 80% en `Cover`.
**Qué deberías ver si algo falla:** TOTAL < 80%, o algún endpoint retorna 4xx/5xx inesperado.

---

#### Pipeline verde
**Fuente:** 09 §3.1
**Comando:**
```bash
gh workflow run ci.yml --ref main
```
**Qué hace:** lanza manualmente el workflow de CI en GitHub Actions sobre la rama `main`.
**Qué deberías ver si está correcto:** en GitHub → Actions → `ci.yml` → último run: estado `success` en todos los jobs.
**Qué deberías ver si algo falla:** cualquier job con estado `failure` o `cancelled`.

---

#### Contrato OpenAPI válido — 7 endpoints
**Fuente:** 09 §3.1
**Comando:**
```bash
python scripts/validate_openapi.py --module catalogo
```
**Qué hace:** monta la app FastAPI e inspecciona sus rutas registradas para confirmar que los 7 endpoints de catálogo están presentes.
**Qué deberías ver si está correcto:** `OK — catalogo: 7/7 endpoints presentes`
**Qué deberías ver si algo falla:** `FAIL — catalogo: N endpoints, se esperan 7` y lista de los faltantes.

---

#### Smoke test disponibilidad HTTP 200
**Fuente:** 09 §3.1
**Comando:**
```bash
curl -s -o /dev/null -w "%{http_code}" $API_URL/v1/catalogo/repuestos
```
**Qué hace:** hace un GET al endpoint de listado de repuestos contra la URL del sistema desplegado y reporta el código HTTP.
**Qué deberías ver si está correcto:** `200`
**Qué deberías ver si algo falla:** cualquier código distinto de `200` (típico: `502` si el servidor está caído, `404` si la ruta cambió).

---

#### Smoke test búsqueda con resultados
**Fuente:** 09 §3.1
**Comando:**
```bash
curl -s "$API_URL/v1/catalogo/repuestos?modelo=test&anio=2020"
```
**Qué hace:** ejecuta una búsqueda por modelo y año contra el sistema desplegado.
**Qué deberías ver si está correcto:** respuesta JSON con estructura `{"data": [...], "meta": {...}}` y código 200.
**Qué deberías ver si algo falla:** respuesta de error, array vacío cuando debería haber datos de seed, o estructura de respuesta incorrecta.

---

#### Vocabulario canónico — 0 sinónimos en domain/
**Fuente:** 09 §3.1
**Comando:**
```bash
grep -r "producto\|item\|articulo\|pieza" src/catalogo/domain/
```
**Qué hace:** busca sinónimos prohibidos del vocabulario canónico (02 §1.1) en el código de dominio de catálogo.
**Qué deberías ver si está correcto:** ninguna salida (cero coincidencias).
**Qué deberías ver si algo falla:** líneas con las palabras prohibidas — cada una es una violación que hay que corregir antes de cerrar el módulo.

---

#### Arquitectura DIP — 0 violaciones
**Fuente:** 09 §3.1
**Comando:**
```bash
python scripts/check_dip.py --module catalogo
```
**Qué hace:** analiza los imports de `src/catalogo/domain/` y falla si algún archivo del dominio importa desde `infrastructure/` o desde otro módulo.
**Qué deberías ver si está correcto:** `OK — 0 violaciones DIP en src/catalogo/domain/`
**Qué deberías ver si algo falla:** lista de archivos con imports prohibidos y el módulo que importan.

---

#### Seed nivel 1 ejecutable sin errores
**Fuente:** 09 §3.1
**Comando:**
```bash
python scripts/seed.py --level=1 --module=catalogo --env=test
```
**Qué hace:** ejecuta el seed mínimo (5 registros de catálogo) en el entorno de test.
**Qué deberías ver si está correcto:** mensaje de completado sin trazas de error. Exit code 0.
**Qué deberías ver si algo falla:** traza de excepción Python, o mensaje de error de conexión/datos.

---

### 1.2 Módulo `pedidos` (09 §3.2)

---

#### Cobertura dominio ≥ 90% branch
**Fuente:** 09 §3.2
**Comando:**
```bash
pytest tests/unit/pedidos/domain/ --cov=src/pedidos/domain --cov-branch
```
**Qué hace:** mide cobertura de ramas del dominio de pedidos.
**Qué deberías ver si está correcto:** TOTAL ≥ 90% en columna `Branch`.
**Qué deberías ver si algo falla:** TOTAL < 90% o tests fallando.

---

#### Cobertura infraestructura ≥ 70% line
**Fuente:** 09 §3.2
**Comando:**
```bash
pytest tests/unit/pedidos/infrastructure/ --cov=src/pedidos/infrastructure
```
**Qué hace:** mide cobertura de líneas de la infraestructura de pedidos.
**Qué deberías ver si está correcto:** TOTAL ≥ 70%.
**Qué deberías ver si algo falla:** TOTAL < 70%.

---

#### Cobertura integración ≥ 80% line
**Fuente:** 09 §3.2
**Comando:**
```bash
pytest tests/integration/pedidos/ --cov=src/pedidos
```
**Qué hace:** tests de integración de los 17 endpoints de pedidos, mide cobertura total de `src/pedidos`.
**Qué deberías ver si está correcto:** TOTAL ≥ 80%.
**Qué deberías ver si algo falla:** TOTAL < 80% o fallos en endpoints críticos (comprobante, reserva).

---

#### Pipeline verde
**Fuente:** 09 §3.2
**Comando:**
```bash
gh workflow run ci.yml --ref main
```
**Qué hace:** lanza CI en GitHub Actions sobre `main`.
**Qué deberías ver si está correcto:** todos los jobs en `success`.
**Qué deberías ver si algo falla:** job en `failure`.

---

#### Contrato OpenAPI válido — 17 endpoints
**Fuente:** 09 §3.2
**Comando:**
```bash
python scripts/validate_openapi.py --module pedidos
```
**Qué hace:** verifica que los 17 endpoints de pedidos (EP-PED-01..17) están registrados en la app.
**Qué deberías ver si está correcto:** `OK — pedidos: 17/17 endpoints presentes`
**Qué deberías ver si algo falla:** `FAIL` con lista de endpoints faltantes.

---

#### Smoke test creación HTTP 201
**Fuente:** 09 §3.2
**Comando:**
```bash
curl -s -X POST $API_URL/v1/pedidos -H "Authorization: Bearer $TEST_TOKEN" -d @fixtures/pedido_minimo.json
```
**Qué hace:** crea un pedido mínimo contra el sistema desplegado.
**Qué deberías ver si está correcto:** respuesta con `"estado": "BORRADOR"` y código 201.
**Qué deberías ver si algo falla:** código 401 (token), 422 (validación), 500 (error interno).

---

#### Smoke test estado HTTP 200 con BORRADOR
**Fuente:** 09 §3.2
**Comando:**
```bash
curl -s "$API_URL/v1/pedidos/$PEDIDO_ID" -H "Authorization: Bearer $TEST_TOKEN"
```
**Qué hace:** consulta el estado de un pedido recién creado.
**Qué deberías ver si está correcto:** `"estado": "BORRADOR"` en la respuesta y código 200.
**Qué deberías ver si algo falla:** 404 (pedido no encontrado), o estado distinto de `BORRADOR`.

---

#### Flujo comprobante — VENDEDOR siempre PENDIENTE_VALIDACION
**Fuente:** 09 §3.2
**Comando:**
```bash
pytest tests/integration/pedidos/test_comprobante_flujo.py
```
**Qué hace:** ejecuta la suite que verifica que VENDEDOR **siempre** genera comprobante en `PENDIENTE_VALIDACION` (corrección ABAC-06 de 07).
**Qué deberías ver si está correcto:** todos los tests `PASSED`.
**Qué deberías ver si algo falla:** algún test `FAILED` indicando que el flujo de comprobante no aplica la regla ABAC-06.

---

#### Reserva con TTL — por segmento
**Fuente:** 09 §3.2
**Comando:**
```bash
pytest tests/unit/pedidos/domain/test_reserva_ttl.py
```
**Qué hace:** verifica que el TTL de reserva es diferenciado por segmento de cliente (presencial 1 día, distrito/rural 3 días, motolineal 2 días).
**Qué deberías ver si está correcto:** todos los tests `PASSED`.
**Qué deberías ver si algo falla:** test `FAILED` indicando que el TTL no corresponde al segmento esperado.

---

#### Vocabulario canónico — 0 sinónimos
**Fuente:** 09 §3.2
**Comando:**
```bash
grep -r "orden\|solicitud\|compra\|recibo" src/pedidos/domain/
```
**Qué hace:** busca sinónimos prohibidos de `Pedido` en el dominio de pedidos.
**Qué deberías ver si está correcto:** cero coincidencias.
**Qué deberías ver si algo falla:** líneas con palabras prohibidas — recordar que `ot_id` (referencia a OrdenTrabajo) fue el caso canónico resuelto renombrando el campo.

---

#### Arquitectura DIP — 0 violaciones
**Fuente:** 09 §3.2
**Comando:**
```bash
python scripts/check_dip.py --module pedidos
```
**Qué hace:** verifica que el dominio de pedidos no importa desde infrastructure ni desde otros módulos.
**Qué deberías ver si está correcto:** `OK — 0 violaciones DIP en src/pedidos/domain/`
**Qué deberías ver si algo falla:** lista de imports prohibidos.

---

#### Seed nivel 1
**Fuente:** 09 §3.2
**Comando:**
```bash
python scripts/seed.py --level=1 --module=pedidos --env=test
```
**Qué hace:** seed mínimo de pedidos en entorno test.
**Qué deberías ver si está correcto:** completado sin errores.
**Qué deberías ver si algo falla:** traza de excepción o mensaje de error.

---

### 1.3 Módulo `stock` (09 §3.3)

---

#### Cobertura dominio ≥ 95% branch — umbral más alto
**Fuente:** 09 §3.3
**Comando:**
```bash
pytest tests/unit/stock/domain/ --cov=src/stock/domain --cov-branch
```
**Qué hace:** mide cobertura de ramas del dominio de stock. El umbral es 95% — el más alto del sistema por la criticidad del inventario.
**Qué deberías ver si está correcto:** TOTAL ≥ 95% en `Branch`.
**Qué deberías ver si algo falla:** TOTAL < 95%. No hay margen de tolerancia aquí.

---

#### Cobertura infraestructura ≥ 70% line
**Fuente:** 09 §3.3
**Comando:**
```bash
pytest tests/unit/stock/infrastructure/ --cov=src/stock/infrastructure
```
**Qué hace:** mide cobertura de líneas de la infraestructura de stock.
**Qué deberías ver si está correcto:** TOTAL ≥ 70%.
**Qué deberías ver si algo falla:** TOTAL < 70%.

---

#### Cobertura integración ≥ 85% line
**Fuente:** 09 §3.3
**Comando:**
```bash
pytest tests/integration/stock/ --cov=src/stock
```
**Qué hace:** tests de integración de los 8 endpoints de stock más tests de servicio, mide cobertura total de `src/stock`.
**Qué deberías ver si está correcto:** TOTAL ≥ 85%.
**Qué deberías ver si algo falla:** TOTAL < 85% — tipicamente indica que test_servicio_stock.py no cubre las rutas de descuento atómico.

---

#### Pipeline verde
**Fuente:** 09 §3.3
**Comando:**
```bash
gh workflow run ci.yml --ref main
```
**Qué hace:** lanza CI en GitHub Actions.
**Qué deberías ver si está correcto:** todos los jobs en `success`.
**Qué deberías ver si algo falla:** job en `failure`.

---

#### Contrato OpenAPI válido — 8 endpoints
**Fuente:** 09 §3.3
**Comando:**
```bash
python scripts/validate_openapi.py --module stock
```
**Qué hace:** verifica que los 8 endpoints de stock están registrados (5 bajo `/v1/stock/` y 3 bajo `/v1/reabastecimientos/`).
**Qué deberías ver si está correcto:** `OK — stock: 8/8 endpoints presentes`
**Qué deberías ver si algo falla:** `FAIL` — nota que los endpoints de reabastecimiento tienen prefijo diferente, por eso se usa lista explícita.

---

#### Smoke test consulta HTTP 200 con stock real
**Fuente:** 09 §3.3
**Comando:**
```bash
curl -s "$API_URL/v1/stock/repuestos/$REPUESTO_ID" -H "Authorization: Bearer $TEST_TOKEN"
```
**Qué hace:** consulta el stock de un repuesto específico contra el sistema desplegado.
**Qué deberías ver si está correcto:** respuesta con `cantidad_disponible`, `esta_agotado`, etc. Código 200.
**Qué deberías ver si algo falla:** 404 (repuesto sin stock inicializado), 401 (token inválido).

---

#### Descuento atómico — sin stock negativo posible
**Fuente:** 09 §3.3
**Comando:**
```bash
pytest tests/unit/stock/domain/test_descuento_atomico.py
```
**Qué hace:** verifica que el descuento atómico (todos-o-ninguno) funciona correctamente y que ningún escenario puede dejar el stock en negativo.
**Qué deberías ver si está correcto:** todos los tests `PASSED`.
**Qué deberías ver si algo falla:** test de rollback o de no-negativo fallando — indica una regresión crítica en la lógica de inventario.

---

#### Outbox integridad — 0 eventos perdidos en fallo
**Fuente:** 09 §3.3
**Comando:**
```bash
pytest tests/integration/stock/test_outbox_resiliencia.py
```
**Qué hace:** verifica que los eventos de stock (agotado, bajo_umbral, disponible) se publican correctamente antes de retornar y que no se pierden eventos en escenarios de múltiples ajustes.
**Qué deberías ver si está correcto:** todos los tests `PASSED`.
**Qué deberías ver si algo falla:** test de eventos perdidos fallando.

---

#### Umbral de alerta — notificación al cruzar umbral
**Fuente:** 09 §3.3
**Comando:**
```bash
pytest tests/unit/stock/domain/test_umbral_alerta.py
```
**Qué hace:** verifica que la alerta `stock.bajo_umbral` se genera exactamente cuando el disponible cruza el umbral mínimo configurado.
**Qué deberías ver si está correcto:** todos los tests `PASSED`.
**Qué deberías ver si algo falla:** test de alerta fallando — puede indicar que el evento no se publica o se publica en el momento incorrecto.

---

#### Vocabulario canónico — 0 sinónimos
**Fuente:** 09 §3.3
**Comando:**
```bash
grep -r "inventario\|existencias\|cantidad_total" src/stock/domain/
```
**Qué hace:** busca sinónimos prohibidos de `Stock` en el dominio. Nota: `stock_total()` es el nombre canónico correcto.
**Qué deberías ver si está correcto:** cero coincidencias.
**Qué deberías ver si algo falla:** aparición de palabras prohibidas — recordar que `cantidad_total` fue el caso resuelto renombrando a `stock_total`.

---

#### Arquitectura DIP — 0 violaciones
**Fuente:** 09 §3.3
**Comando:**
```bash
python scripts/check_dip.py --module stock
```
**Qué hace:** verifica que el dominio de stock no importa desde infrastructure ni desde otros módulos.
**Qué deberías ver si está correcto:** `OK — 0 violaciones DIP en src/stock/domain/`
**Qué deberías ver si algo falla:** lista de imports prohibidos.

---

#### Seed nivel 1
**Fuente:** 09 §3.3
**Comando:**
```bash
python scripts/seed.py --level=1 --module=stock --env=test
```
**Qué hace:** seed mínimo de stock en entorno test.
**Qué deberías ver si está correcto:** completado sin errores.
**Qué deberías ver si algo falla:** traza de excepción.

---

### 1.4 Módulo `taller` (09 §3.4)

---

#### Cobertura dominio ≥ 85% branch
**Fuente:** 09 §3.4
**Comando:**
```bash
pytest tests/unit/taller/domain/ --cov=src/taller/domain --cov-branch
```
**Qué hace:** mide cobertura de ramas del dominio de taller.
**Qué deberías ver si está correcto:** TOTAL ≥ 85% en `Branch`.
**Qué deberías ver si algo falla:** TOTAL < 85%.

---

#### Cobertura infraestructura ≥ 70% line
**Fuente:** 09 §3.4
**Comando:**
```bash
pytest tests/unit/taller/infrastructure/ --cov=src/taller/infrastructure
```
**Qué hace:** mide cobertura de líneas de la infraestructura de taller.
**Qué deberías ver si está correcto:** TOTAL ≥ 70%.
**Qué deberías ver si algo falla:** TOTAL < 70%.

---

#### Cobertura integración ≥ 80% line
**Fuente:** 09 §3.4
**Comando:**
```bash
pytest tests/integration/taller/ --cov=src/taller
```
**Qué hace:** tests de integración de los 12 endpoints de taller más tests de cierre atómico.
**Qué deberías ver si está correcto:** TOTAL ≥ 80%.
**Qué deberías ver si algo falla:** TOTAL < 80%.

---

#### Pipeline verde
**Fuente:** 09 §3.4
**Comando:**
```bash
gh workflow run ci.yml --ref main
```
**Qué hace:** lanza CI en GitHub Actions.
**Qué deberías ver si está correcto:** todos los jobs en `success`.
**Qué deberías ver si algo falla:** job en `failure`.

---

#### Contrato OpenAPI válido — 12 endpoints
**Fuente:** 09 §3.4
**Comando:**
```bash
python scripts/validate_openapi.py --module taller
```
**Qué hace:** verifica que los 12 endpoints de taller (EP-TAL-01..12) están registrados.
**Qué deberías ver si está correcto:** `OK — taller: 12/12 endpoints presentes`
**Qué deberías ver si algo falla:** `FAIL` con lista de endpoints faltantes.

---

#### Smoke test creación OT HTTP 201
**Fuente:** 09 §3.4
**Comando:**
```bash
curl -s -X POST $API_URL/v1/taller/ordenes -H "Authorization: Bearer $TEST_TOKEN" -d @fixtures/orden_minima.json
```
**Qué hace:** abre una orden de trabajo mínima contra el sistema desplegado.
**Qué deberías ver si está correcto:** respuesta con `"estado": "ABIERTA"` y código 201.
**Qué deberías ver si algo falla:** 404 (vehículo no existe en el fixture), 422 (campos faltantes), 500.

---

#### Flujo aprobación tácita — < S/30 automático
**Fuente:** 09 §3.4
**Comando:**
```bash
pytest tests/unit/taller/domain/test_aprobacion_tacita.py
```
**Qué hace:** verifica los tres tramos de precio: < S/30 = automático, S/30–S/100 = espera tácita 30 min, > S/100 = bloqueo manual.
**Qué deberías ver si está correcto:** todos los tests `PASSED`.
**Qué deberías ver si algo falla:** test de tramo fallando — indica que la lógica de precios adicionales no aplica el umbral correcto.

---

#### Registro consumo obligatorio — OT no cierra sin lista confirmada
**Fuente:** 09 §3.4
**Comando:**
```bash
pytest tests/unit/taller/domain/test_consumo_obligatorio.py
```
**Qué hace:** verifica que una OT no puede cerrarse sin lista de consumo confirmada y cobro registrado.
**Qué deberías ver si está correcto:** todos los tests `PASSED`.
**Qué deberías ver si algo falla:** test de cierre sin consumo fallando.

---

#### Descuento stock al cierre — atomicidad
**Fuente:** 09 §3.4
**Comando:**
```bash
pytest tests/integration/taller/test_cierre_atomico.py
```
**Qué hace:** verifica que al cerrar una OT se publica el evento `orden_trabajo.cerrada` con la lista exacta de repuestos consumidos, y que el cierre falla si no hay cobro confirmado.
**Qué deberías ver si está correcto:** todos los tests `PASSED`.
**Qué deberías ver si algo falla:** test de evento faltante o de cierre sin cobro fallando.

---

#### Vocabulario canónico — 0 sinónimos
**Fuente:** 09 §3.4
**Comando:**
```bash
grep -r "tecnico\|operario\|ticket\|servicio" src/taller/domain/
```
**Qué hace:** busca sinónimos prohibidos de `OrdenTrabajo` y `Mecanico` en el dominio de taller. Nota: `ModalidadIntervencion` reemplazó `tipo_servicio`.
**Qué deberías ver si está correcto:** cero coincidencias.
**Qué deberías ver si algo falla:** aparición de palabras prohibidas en docstrings o nombres de campo.

---

#### Arquitectura DIP — 0 violaciones
**Fuente:** 09 §3.4
**Comando:**
```bash
python scripts/check_dip.py --module taller
```
**Qué hace:** verifica que el dominio de taller no importa desde infrastructure ni desde otros módulos.
**Qué deberías ver si está correcto:** `OK — 0 violaciones DIP en src/taller/domain/`
**Qué deberías ver si algo falla:** lista de imports prohibidos.

---

#### Seed nivel 1
**Fuente:** 09 §3.4
**Comando:**
```bash
python scripts/seed.py --level=1 --module=taller --env=test
```
**Qué hace:** seed mínimo de taller en entorno test.
**Qué deberías ver si está correcto:** completado sin errores.
**Qué deberías ver si algo falla:** traza de excepción.

---

## 2. Criterios transversales — 09 §4.1 y §4.2

### 2.1 Vocabulario canónico — todos los módulos (09 §4.1)

**Fuente:** 09 §4.1
**Comando:**
```bash
grep -r "producto\|item\|orden\|ticket\|tecnico\|usuario" src/{modulo}/domain/
```
**Qué hace:** grep general de sinónimos prohibidos sobre el dominio del módulo indicado. Sustituir `{modulo}` por `catalogo`, `pedidos`, `stock` o `taller`.
**Qué deberías ver si está correcto:** cero coincidencias.
**Qué deberías ver si algo falla:** líneas con las palabras — hay casos históricos de falsos positivos: `TECNICO_ESPECIALIZADO` (categoría canónica de catalogo) y `ot_id` (referencia canónica a OrdenTrabajo en pedidos). Si aparecen, verificar que son falsos positivos documentados antes de declarar fallo.

---

### 2.2 Logs estructurados JSON (09 §4.1)

**Fuente:** 09 §4.1
**Comando:**
```bash
pytest tests/unit/{modulo}/test_logs_estructura.py
```
**Qué hace:** verifica que el JSONFormatter emite los 5 campos obligatorios (timestamp, level, service, version, environment) más request_id en cada log.
**Qué deberías ver si está correcto:** todos los tests `PASSED`.
**Qué deberías ver si algo falla:** test de campo faltante fallando — indica que el formatter no cumple 02 §1.6.

---

### 2.3 SAST — 0 hallazgos CRITICAL (09 §4.2)

**Fuente:** 09 §4.2
**Comando:**
```bash
bandit -r src/{modulo}/ -ll
```
**Qué hace:** análisis estático de seguridad sobre el código fuente del módulo. `-ll` muestra LOW y superior.
**Qué deberías ver si está correcto:** `Total issues (by severity): High: 0` y sin hallazgos CRITICAL.
**Qué deberías ver si algo falla:** cualquier hallazgo con `Severity: HIGH` o `CRITICAL`. Los hallazgos `LOW` y `MEDIUM` no bloquean pero deben revisarse.

---

### 2.4 Secrets scan — 0 hallazgos (09 §4.2)

**Fuente:** 09 §4.2
**Comando:**
```bash
gitleaks detect --source src/{modulo}/
```
**Qué hace:** escanea el código del módulo en busca de secretos hardcodeados (tokens, contraseñas, claves API).
**Qué deberías ver si está correcto:** `No leaks detected.` o similar según versión de Gitleaks.
**Qué deberías ver si algo falla:** lista de archivos y líneas con secretos detectados — si es un falso positivo, debe agregarse al allowlist en `.gitleaks.toml` y reportarse a Sant antes de continuar.

---

## 3. Suite completa — 09 §9.1

### 3.1 Suite completa con cobertura global

**Fuente:** 09 §9.1
**Comando:**
```bash
pytest tests/ --cov=src/ --cov-branch global verde
```
**Qué hace:** ejecuta los 735 tests del repositorio (unit + contracts + integration + scripts) y mide cobertura branch de todo `src/`.
**Qué deberías ver si está correcto:** `N passed, 0 failed` con TOTAL ≥ 96%.
**Qué deberías ver si algo falla:** cualquier `FAILED`, o TOTAL por debajo del umbral.

---

### 3.2 OpenAPI todos los módulos

**Fuente:** 09 §9.1
**Comando:**
```bash
python scripts/validate_openapi.py --all
```
**Qué hace:** valida los 44 endpoints de los 4 módulos en un solo comando.
**Qué deberías ver si está correcto:** 4 líneas `OK` — catalogo 7/7, pedidos 17/17, stock 8/8, taller 12/12.
**Qué deberías ver si algo falla:** cualquier línea `FAIL`.

---

### 3.3 Scan de secretos en repositorio completo

**Fuente:** 09 §9.2
**Comando:**
```bash
gitleaks detect --source . en rama main
```
**Qué hace:** escanea todo el repositorio (no solo `src/`) en busca de secretos en cualquier archivo incluido el historial de git visible.
**Qué deberías ver si está correcto:** `No leaks detected.`
**Qué deberías ver si algo falla:** hallazgos con ruta y número de línea — requiere rotación inmediata del secreto y limpieza del historial git antes de continuar.

---

### 3.4 Scan de imagen Docker — 0 CRITICAL

**Fuente:** 09 §9.1
**Comando:**
```bash
trivy image tecnimotos-api:latest --severity CRITICAL
```
**Qué hace:** escanea la imagen Docker construida en busca de vulnerabilidades CVE de severidad CRITICAL.
**Qué deberías ver si está correcto:** `Total: 0 (CRITICAL: 0)`
**Qué deberías ver si algo falla:** lista de CVEs CRITICAL con número de vulnerabilidad y paquete afectado — hay que actualizar las dependencias o aceptar con excepción documentada.

---

## 4. Estrategia de pruebas — 04 §2

### 4.1 Suite de contratos LSP — base de la pirámide

**Fuente:** 04 §2.2
**Comando:**
```bash
pytest tests/contracts/ -v
```
**Qué hace:** ejecuta las 7 suites LSP (70 tests) que verifican que cada implementación concreta respeta el mismo contrato que el Fake. Debe correr **antes** que las pruebas unitarias e integración.
**Qué deberías ver si está correcto:** `70 passed, 0 failed` con tests distribuidos en los 7 archivos de contrato.
**Qué deberías ver si algo falla:** un test `FAILED` en la variante `[real]` pero no en `[inmemory]` indica que la implementación real no respeta el contrato — bloquea deploy.

---

### 4.2 Pruebas unitarias

**Fuente:** 04 §2.2
**Comando:**
```bash
pytest tests/unit/ -v --cov=src --cov-report=term-missing
```
**Qué hace:** ejecuta todos los tests unitarios del dominio e infraestructura (sin BD real) y muestra qué líneas específicas no están cubiertas.
**Qué deberías ver si está correcto:** todos los tests pasando, sin líneas críticas del dominio en `Missing`.
**Qué deberías ver si algo falla:** tests fallando o líneas de lógica de negocio en `Missing`.

---

### 4.3 Pruebas de integración

**Fuente:** 04 §2.2
**Comando:**
```bash
pytest tests/integration/ -v
```
**Qué hace:** ejecuta los tests de integración HTTP contra la app FastAPI con repositorios en memoria.
**Qué deberías ver si está correcto:** todos los tests pasando.
**Qué deberías ver si algo falla:** endpoint retornando código incorrecto o respuesta malformada.

---

### 4.4 Suite completa con reporte HTML

**Fuente:** 04 §2.2
**Comando:**
```bash
pytest tests/unit/ tests/contracts/ tests/integration/ \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  --cov-report=xml:coverage.xml
```
**Qué hace:** ejecuta toda la suite (excluyendo `tests/unit/scripts/`) y genera tres reportes: terminal con líneas faltantes, HTML navegable en `htmlcov/`, XML para CI.
**Qué deberías ver si está correcto:** todos los tests pasando, reporte `htmlcov/index.html` generado.
**Qué deberías ver si algo falla:** tests fallando o directorio `htmlcov/` no generado.

---

### 4.5 Verificación por módulo individual

**Fuente:** 04 §2.3
**Comando:**
```bash
pytest tests/unit/{modulo}/ tests/contracts/test_contrato_{modulo}*.py \
  --cov=src/{modulo} \
  --cov-report=term-missing
```
**Qué hace:** mide cobertura de un solo módulo incluyendo sus contratos LSP. Sustituir `{modulo}` por `catalogo`, `pedidos`, `stock` o `taller`.
**Qué deberías ver si está correcto:** cobertura por encima del umbral del módulo (ver 04 §3.1).
**Qué deberías ver si algo falla:** cobertura por debajo del umbral.

---

### 4.6 Verificación de umbral por módulo en pipeline

**Fuente:** 04 §3.4
**Comando:**
```bash
pytest tests/unit/ tests/contracts/ \
  --cov=src \
  --cov-branch \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov
python scripts/check_coverage.py coverage.xml
```
**Qué hace:** genera el reporte XML y luego verifica que cada módulo cumple su umbral mínimo declarado en 04 §3.1. Bloquea con exit code 1 si algún módulo falla.
**Qué deberías ver si está correcto:** `stock 96.9% branch ✅ (umbral 95%)` etc. Exit code 0.
**Qué deberías ver si algo falla:** línea con ❌ y exit code 1 — el pipeline se bloquea.

---

### 4.7 Seeds por nivel

**Fuente:** 04 §5.4
**Comando (nivel mínimo):**
```bash
python scripts/seed/seed_minimo.py
```
**Qué hace:** carga 5 repuestos, 3 pedidos, 2 clientes, 2 OT, 1 reabastecimiento.
**Qué deberías ver si está correcto:** completado sin errores.
**Qué deberías ver si algo falla:** error de conexión a BD o error de inserción.

---

**Fuente:** 04 §5.4
**Comando (nivel estándar):**
```bash
python scripts/seed/seed_estandar.py
```
**Qué hace:** carga el volumen estándar con cobertura de todos los estados del ciclo de vida (04 §5.2).
**Qué deberías ver si está correcto:** completado sin errores, y `verify_seed.py --level=2` reporta PASS.
**Qué deberías ver si algo falla:** error de inserción o `verify_seed.py` reporta FAIL en alguna tabla.

---

**Fuente:** 04 §5.4
**Comando (nivel completo):**
```bash
python scripts/seed/seed_completo.py
```
**Qué hace:** carga el volumen completo para pruebas de rendimiento.
**Qué deberías ver si está correcto:** completado sin errores.
**Qué deberías ver si algo falla:** timeout o error de conexión por volumen.

---

## 5. Scripts de operación recién construidos (CT-11-01, CT-11-02)

### 5.1 Verificar integridad del seed (CT-11-02)

**Fuente:** 08 §6.9 · 04 §5.1 · 04 §5.2
**Comando:**
```bash
python scripts/verify_seed.py --env=staging
```
*(nota: el DOC-3 lo referencia así en 08 §6.9 — en la implementación requiere también `--level`)*

**Forma completa ejecutable:**
```bash
python scripts/verify_seed.py --level=2 --env=staging
```
**Qué hace:** verifica que el seed cargado cumple los conteos mínimos de 04 §5.1 (repuestos, pedidos, clientes, OT, reabastecimientos para el nivel) Y las reglas de contenido de 04 §5.2 (estados de disponibilidad, ciclo de vida OT, segmentos de cliente, estados de pedido). Reporta PASS/FAIL por tabla con logging JSON.
**Qué deberías ver si está correcto:** todas las líneas con `PASS`, y la línea final `PASS — todos los criterios verificados`. Exit code 0.
**Qué deberías ver si algo falla:** línea `FAIL` con el criterio fallido (ej. `FAIL — orden_trabajo — estado=REVISION_FINAL — esperado=presente obtenido=ausente`). Exit code 1.

---

### 5.2 Re-cifrado Fernet en seco (dry-run) (CT-11-01)

**Fuente:** 07 §5.4 · 08 §7.1 · 03 §5.7
**Comando:**
```bash
python scripts/reencrypt_fernet.py \
  --old-key $FERNET_KEY_OLD \
  --new-key $FERNET_KEY_NEW \
  --dry-run
```
**Qué hace:** simula el re-cifrado de los 21 campos de la lista cerrada de 03 §5.7 (8 tablas: usuario, usuario_perfil, mecanico_perfil, repuesto, reabastecimiento_item, pedido, vehiculo, envio) sin modificar nada en la BD. Reporta cuántas filas se procesarían por campo.
**Qué deberías ver si está correcto:** líneas con `[dry-run] tabla.campo — procesadas=N omitidas=0 OK`. Exit code 0.
**Qué deberías ver si algo falla:** línea con `ERROR: ...` indicando qué campo falló al descifrar — puede indicar que `--old-key` no es la clave correcta.

---

### 5.3 Re-cifrado Fernet real (CT-11-01)

**Fuente:** 07 §5.4 · 08 §7.1 · 03 §5.7
**Comando:**
```bash
python scripts/reencrypt_fernet.py \
  --old-key $FERNET_KEY_OLD \
  --new-key $FERNET_KEY_NEW
```
**Qué hace:** re-cifra en real todos los campos de 03 §5.7. Opera en transacción por campo (rollback por campo si falla, no rollback global). **Ejecutar siempre después de `--dry-run` exitoso y con la BD en modo solo-lectura** (ver procedimiento completo en 08 §7.1).
**Qué deberías ver si está correcto:** líneas `tabla.campo — procesadas=N omitidas=0 OK` para los 21 campos, y línea final `Re-cifrado real completado`. Exit code 0.
**Qué deberías ver si algo falla:** línea `ERROR: ...` para el campo que falló — los campos anteriores ya fueron re-cifrados, los siguientes no. Anotar exactamente cuál campo falló para retomar.

---

## 6. Checklists operativos — 08 §8

### 6.1 Restauración de seed en staging corrupto (08 §6.9)

**Fuente:** 08 §6.9

**Paso 1 — Confirmar entorno:**
```bash
echo $ENVIRONMENT
```
**Qué deberías ver si está correcto:** `staging`. Si dice `production`: DETENER INMEDIATAMENTE.

**Paso 2 — Reiniciar BD staging:**
```bash
psql -U postgres -c "DROP DATABASE IF EXISTS tecnimotos_staging;"
psql -U postgres -c "CREATE DATABASE tecnimotos_staging;"
```
**Qué deberías ver si está correcto:** `DROP DATABASE` y `CREATE DATABASE` sin errores.

**Paso 3 — Migraciones:**
```bash
alembic upgrade head
```
**Qué deberías ver si está correcto:** `Running upgrade ... -> [revision]` hasta la revisión head. Sin errores.

**Paso 4 — Aplicar seed estándar:**
```bash
python scripts/seed.py --level=2 --env=staging
```
**Qué deberías ver si está correcto:** completado sin errores.

**Paso 5 — Verificar seed:**
```bash
python scripts/verify_seed.py --env=staging
```
**Qué deberías ver si está correcto:** `PASS — todos los criterios verificados`. Exit code 0.

**Paso 6 — Relanzar E2E:**
```bash
gh workflow run e2e-nightly.yml --ref main
```
**Qué deberías ver si está correcto:** workflow lanzado, y en GitHub Actions → resultado `success`.

---

### 6.2 Backup lógico diario (08 §5.4)

**Fuente:** 08 §5.4

**Dump:**
```bash
pg_dump $DATABASE_URL \
  --format=custom \
  --compress=9 \
  --file=backup_$(date +%Y%m%d).dump
```
**Qué deberías ver si está correcto:** archivo `backup_YYYYMMDD.dump` creado sin mensajes de error.

**Subida a object storage:**
```bash
rclone copy backup_$(date +%Y%m%d).dump \
  backblaze:tecnimotos-backups/daily/
```
**Qué deberías ver si está correcto:** transferencia completada sin errores. Verificar en Backblaze B2 que el archivo existe.

---

### 6.3 Verificación de restauración trimestral (08 §5.5)

**Fuente:** 08 §5.5
**Comando:**
```bash
pg_restore --dbname=tecnimotos_staging \
  --clean --if-exists \
  backup_YYYYMMDD.dump
```
**Qué hace:** restaura el backup en la BD de staging para verificar que la restauración funciona (no solo que el archivo existe). Se ejecuta cada 90 días según el checklist trimestral.
**Qué deberías ver si está correcto:** restauración completada sin errores. A continuación verificar count de registros en tablas críticas.
**Qué deberías ver si algo falla:** error de formato incompatible o corrupción de datos — incidente Severidad 1, investigar causa antes de continuar.

---

### 6.4 Rotación de secretos — estándar (08 §7.1)

**Fuente:** 08 §7.1

**Generar nuevo JWT RS256:**
```bash
openssl genrsa -out jwt_private.pem 2048
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem
```

**Generar password o API key:**
```bash
openssl rand -base64 32
```

**Actualizar en Railway (Fase 1):**
```bash
railway variables set SECRET_NAME=nuevo_valor
```

**Cambiar password en PostgreSQL (si aplica):**
```bash
ALTER USER tecnimotos_user PASSWORD 'nuevo';
```

**Qué deberías ver si está correcto:** `railway variables set` sin errores. Redeploy exitoso. `curl $API_URL/health` responde 200.
**Qué deberías ver si algo falla:** api-server no arranca por variable faltante o inválida — revisar logs del redeploy.

---

### 6.5 Rotación Fernet — ventana de mantenimiento (08 §7.1)

**Fuente:** 08 §7.1

**Activar modo solo-lectura:**
```bash
railway variables set READ_ONLY_MODE=true
```

**Dry-run primero:**
```bash
python scripts/reencrypt_fernet.py \
  --old-key $FERNET_KEY_OLD \
  --new-key $FERNET_KEY_NEW \
  --dry-run
```

**Ejecución real (solo si dry-run OK):**
```bash
python scripts/reencrypt_fernet.py \
  --old-key $FERNET_KEY_OLD \
  --new-key $FERNET_KEY_NEW
```

**Qué deberías ver si está correcto:** dry-run con todas las filas procesadas, ejecución real con exit code 0 y todos los campos re-cifrados. A continuación verificar que Elena puede iniciar sesión y ver precios de costo.
**Qué deberías ver si algo falla:** línea `ERROR` en algún campo — anotar cuál exactamente, verificar que la old-key es correcta, y retomar desde ese campo con ejecución manual.

---

## 7. Cierre del sistema — 09 §9.1 y §9.3

### 7.1 Suite completa en un solo run

**Fuente:** 09 §9.1
**Comando:**
```bash
pytest tests/ --cov=src/ --cov-branch global verde
```
**Qué hace:** ejecuta los 735 tests en un solo run para confirmar que no hay regresiones entre módulos.
**Qué deberías ver si está correcto:** `735 passed, 0 failed`.
**Qué deberías ver si algo falla:** cualquier `FAILED` con nombre del test y traza de error.

---

### 7.2 Seed nivel 2 en staging

**Fuente:** 09 §9.3
**Comando:**
```bash
python scripts/seed.py --level=2 --env=staging
```
**Qué hace:** carga el seed estándar en staging como preparación para E2E y validación de Elena.
**Qué deberías ver si está correcto:** completado sin errores.
**Qué deberías ver si algo falla:** error de conexión (BD staging no disponible) o datos incoherentes.

---

### 7.3 Verificación del seed en staging

**Fuente:** 09 §9.3
**Comando:**
```bash
python scripts/verify_seed.py --env=staging
```
**Qué hace:** verifica que el seed de staging cumple conteos y reglas de contenido de 04 §5.1/§5.2.
**Qué deberías ver si está correcto:** `PASS — todos los criterios verificados`. Exit code 0.
**Qué deberías ver si algo falla:** líneas `FAIL` indicando qué tablas o estados faltan — recargar el seed y volver a verificar.

---

### 7.4 E2E en staging

**Fuente:** 09 §9.3
**Comando:**
```bash
pytest tests/e2e/ --env=staging sin errores
```
**Qué hace:** ejecuta los 3 flujos E2E críticos (consulta+reserva, ciclo OT+cobro, pedido remoto con proforma) contra el entorno de staging real.
**Qué deberías ver si está correcto:** todos los tests pasando.
**Qué deberías ver si algo falla:** flujo E2E fallando con traza — puede indicar problema de datos de seed o de configuración de staging.

---

## 8. Verificación de scripts construidos (CT-11-01, CT-11-02) — §9.4 confirmado

### 8.1 Confirmar que los scripts existen

**Fuente:** 09 §9.4
**Comando:**
```bash
ls scripts/verify_seed.py scripts/reencrypt_fernet.py
```
**Qué deberías ver si está correcto:** ambos archivos listados sin error.
**Qué deberías ver si algo falla:** `No such file or directory` — el bloqueo duro de §9.4 está activo.

---

### 8.2 Tests unitarios de los scripts

**Fuente:** implementación CT-11-01 y CT-11-02
**Comando:**
```bash
pytest tests/unit/scripts/ -v
```
**Qué hace:** ejecuta los 53 tests unitarios de ambos scripts con backends en memoria (sin BD real ni Fernet real en la mayoría).
**Qué deberías ver si está correcto:** `53 passed, 0 failed`.
**Qué deberías ver si algo falla:** test fallando — indica que la lógica del script no cumple la especificación de 04 §5.1/§5.2 o 03 §5.7.

---

## 9. No-regresión entre módulos — 09 §6

El protocolo declara ejecutar estos pasos al cerrar cada módulo. Se listan aquí como referencia completa.

**Al cerrar catalogo:**
```bash
pytest tests/unit/catalogo/ tests/contracts/ tests/integration/catalogo/ -k "catalogo or contrato_catalogo" -v --cov=src/catalogo --cov-branch
```

**Al cerrar pedidos:**
```bash
pytest tests/unit/catalogo/ tests/unit/pedidos/ tests/contracts/ tests/integration/catalogo/ tests/integration/pedidos/ -v --cov=src/catalogo --cov=src/pedidos --cov-branch
```

**Al cerrar stock:**
```bash
pytest tests/unit/catalogo/ tests/unit/pedidos/ tests/unit/stock/ tests/contracts/ tests/integration/catalogo/ tests/integration/pedidos/ tests/integration/stock/ -v --cov=src/catalogo --cov=src/pedidos --cov=src/stock --cov-branch
```

**Al cerrar taller (suite completa):**
```bash
pytest tests/unit/catalogo/ tests/unit/pedidos/ tests/unit/stock/ tests/unit/taller/ tests/contracts/ tests/integration/catalogo/ tests/integration/pedidos/ tests/integration/stock/ tests/integration/taller/ -v --cov=src/catalogo --cov=src/pedidos --cov=src/stock --cov=src/taller --cov-branch
```

**Qué deberías ver si está correcto:** número exacto de tests ≥ al paso anterior, 0 fallos. Si el número de tests de un módulo anterior baja → regresión real → detención.
**Qué deberías ver si algo falla:** cualquier test `FAILED`, o el conteo de tests de catalogo/pedidos/stock es menor que en el paso anterior.

---

## 10. Tabla de umbrales de referencia rápida (04 §3.1)

| Módulo | Capa | Umbral mínimo | Tipo |
|---|---|---|---|
| `stock` | Dominio | **≥ 95%** | Branch |
| `catalogo` | Dominio | ≥ 90% | Branch |
| `pedidos` | Dominio | ≥ 90% | Branch |
| `taller` | Dominio | ≥ 85% | Branch |
| Infraestructura (todos) | `infrastructure/` | ≥ 70% | Line |
| Transversal | `shared/` · `api/` | ≥ 80% | Branch |

---

## 11. Tabla de conteos de seed por nivel (04 §5.1)

| Entidad | Nivel 1 (mínimo) | Nivel 2 (estándar) | Nivel 3 (completo) |
|---|---|---|---|
| Repuesto | 5 | 25 | 55 |
| Pedido | 3 | 15 | 50 |
| Cliente | 2 | 10 | 30 |
| OrdenTrabajo | 2 | 8 | 20 |
| Reabastecimiento | 1 | 5 | 10 |

---

## 12. Lista cerrada de campos Fernet (03 §5.7)

Exactamente 21 campos en 8 tablas. `reencrypt_fernet.py` opera sobre estos y **solo** estos.

| Tabla | Campos cifrados |
|---|---|
| `usuario` | `email` · `mfa_secret` |
| `usuario_perfil` | `nombres` · `apellidos` · `dni` · `telefono_principal` · `telefono_secundario` · `direccion` |
| `mecanico_perfil` | `dni` · `nombres` · `apellidos` · `telefono` · `direccion` · `fecha_nacimiento` |
| `repuesto` | `precio_costo` |
| `reabastecimiento_item` | `precio_costo_unitario` |
| `pedido` | `descuento_aplicado` · `notas_internas` |
| `vehiculo` | `placa` · `tarjeta_propiedad` |
| `envio` | `direccion_destino` |

---

> **Nota de versión:** Generado a partir de DOC-3 v1.0 (`.doc3/04`, `.doc3/07`, `.doc3/08`, `.doc3/09`) — si esos archivos cambian de versión, este manual debe regenerarse, no parchearse a mano.

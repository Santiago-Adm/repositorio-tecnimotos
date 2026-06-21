---
version: 1.0.1
estado: cerrado
bloque: E
seccion: "04"
titulo: Estrategia de pruebas
autor: Sant
fecha: 2026-06
validador: Sant
aprobado: true
fuentes:
  - 09 especificaciones-tecnicas v1.0.0
ct_pendientes: []
alimenta_doc3: true
tramo_actual: 1 de 6 — frontmatter · propósito · comandos de ejecución por módulo
cambio: Tramo 1 — frontmatter inicial · propósito · comandos ejecutables de pruebas
impacto: Activa la construcción del segundo archivo objetivo de esta sesión DOC-3
---

# 04 — Estrategia de pruebas
## Tecnimotos Santi · DOC-3 — Protocolo de construcción

> Este archivo responde al agente: ¿cómo verifico que lo
> que construí es correcto y cumple los umbrales?
> Fuente: `09 especificaciones-tecnicas` v1.0.0 §6.
> El agente consulta este archivo para ejecutar pruebas,
> verificar umbrales y generar evidencia de cobertura.

---

## 1. Propósito

Este archivo instruye al agente sobre cómo ejecutar la
suite de pruebas completa, qué umbral corresponde a cada
módulo y cómo generar evidencia verificable — tanto para
el pipeline automatizado como para revisión humana directa.

El agente que lee este archivo puede:
ejecutar la suite completa con un comando por capa de la
pirámide · verificar que cada módulo cumple su umbral de
cobertura · generar un reporte navegable sin depender de
herramientas externas a Python.

Este archivo no explica por qué se eligió cada umbral
— esa justificación vive en `09 especificaciones-tecnicas`
§6.3. Este archivo dice qué ejecutar, en qué orden y cómo
verificar el resultado. Referencia: P6 — lenguaje ejecutable.

---

## 2. Comandos de ejecución de pruebas por módulo

### 2.1 Regla de orden de ejecución

La suite de contratos LSP corre primero — un contrato roto
invalida toda prueba que dependa de esa implementación.
Fuente: `09` §6.2 — pirámide de pruebas.
```
1. Contratos LSP
2. Unitarias (dominio)
3. Integración
4. E2E (pipeline nocturno separado — no bloquea cada commit)
```
### 2.2 Comandos ejecutables por capa

```bash
# 1. Suite de contratos LSP — base de la pirámide
pytest tests/contracts/ -v

# 2. Pruebas unitarias — dominio sin infraestructura real
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# 3. Pruebas de integración — PostgreSQL y Redis reales
pytest tests/integration/ -v

# 4. Suite completa con cobertura consolidada
pytest tests/unit/ tests/contracts/ tests/integration/ \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  --cov-report=xml:coverage.xml
```

### 2.3 Comando por módulo individual — verificación dirigida

```bash
# Ejecutar y medir cobertura de un solo módulo
pytest tests/unit/{modulo}/ tests/contracts/test_contrato_{modulo}*.py \
  --cov=src/{modulo} \
  --cov-report=term-missing
```

Sustituir `{modulo}` por `catalogo` · `pedidos` · `stock` ·
`taller` según el módulo bajo verificación.

### 2.4 Reporte de cobertura navegable — evidencia para revisión humana

> Distinción de audiencia explícita: el reporte XML
> (`coverage.xml`) es para el pipeline automatizado —
> SonarQube, badges, gates de CI. El reporte HTML es
> para revisión humana directa, incluyendo a Elena, sin
> que requiera conocimiento técnico para interpretarlo.

```bash
# Generar el reporte HTML — ya incluido en el comando de §2.2
# Output en directorio htmlcov/ con index.html navegable

# Servir localmente para revisión — comando ejecutable
python -m http.server 8080 --directory htmlcov

# Acceder desde navegador:
# http://localhost:8080
```

**Regla de uso:** este servidor HTTP simple es para revisión
puntual — no es infraestructura de producción ni se despliega
permanentemente. Sant lo levanta en su máquina o en `tecnimoto`
cuando necesita mostrar evidencia de cobertura a Elena de forma
visual, sin pedirle que interprete output de terminal.

**Contenido que Elena puede verificar sin conocimiento técnico:**
porcentaje de cobertura por archivo coloreado (verde/rojo) ·
qué líneas específicas no están cubiertas · navegación por
módulo igual que navega carpetas. No requiere que Elena lea
código — el color y el porcentaje son suficientes como señal
de salud del sistema.

**Regla de no producción:** `htmlcov/` se genera localmente o
en el pipeline como artefacto descartable — nunca se commitea
al repositorio ni se expone públicamente, dado que el código
fuente y nombres de funciones internas quedan visibles en
el reporte. Fuente: P1 — sin datos sensibles en superficie
potencialmente pública.

---
## 3. Umbrales de cobertura — ejecutables por módulo

> Fuente: `09 especificaciones-tecnicas` v1.0.0 §6.3.
> El pipeline bloquea deploy si cualquier módulo cae bajo
> su umbral mínimo — RNF-20. Este tramo no repite la
> justificación de cada umbral — esa vive en `09` §6.3.
> Aquí se declara la configuración ejecutable que el agente
> aplica en el pipeline de CI.

### 3.1 Tabla de umbrales — referencia ejecutable

| Módulo | Capa | Umbral mínimo | Tipo de cobertura |
|---|---|---|---|
| `stock` | Dominio | ≥ 95% | Branch |
| `catalogo` | Dominio | ≥ 90% | Branch |
| `pedidos` | Dominio | ≥ 90% | Branch |
| `taller` | Dominio | ≥ 85% | Branch |
| Infraestructura (todos los módulos, incluyendo `shared`) | `infrastructure/` | ≥ 70% | Line |
| `shared` | Dominio (`shared/domain/`) | ≥ 80% | Branch |
| `api` | — | ≥ 80% | Branch (pendiente de confirmar ubicación real — ver investigación en curso) |

Nota de corrección (2026-06-20): el umbral original trataba
"shared" como bloque único de 80% branch, sin distinguir
dominio de infraestructura — inconsistente con el patrón ya
aplicado a los 4 módulos de negocio, donde infraestructura
real (conexiones DB, Redis, Fernet) está excluida de medición
branch por requerir recursos reales no disponibles en tests
unitarios (mismo criterio que excluye
`infrastructure/repositories/models/*` en pyproject.toml §3.2
de 03-diseno-sistema). shared/domain/ (ports puros) sí alcanza
80%+ branch en unitarios sin dependencias externas — verificado
en 100% real durante construcción. shared/infrastructure/
(event_bus.py, database.py, fernet.py) se mide bajo el mismo
criterio de line ≥ 70% que el resto de infraestructura, no
branch — sus ramas de manejo de error de Redis/PostgreSQL/
Fernet requieren integración real, nunca unitarios con fakes.

### 3.2 Configuración ejecutable — `pyproject.toml`

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "src/*/infrastructure/repositories/models/*",
    "tests/*",
]

[tool.coverage.report]
precision = 1
show_missing = true
skip_covered = false

[tool.coverage.html]
directory = "htmlcov"

[tool.coverage.xml]
output = "coverage.xml"
```

### 3.3 Script de verificación de umbral por módulo — ejecutable

> El agente genera este script en `scripts/check_coverage.py`
> porque `coverage.py` nativo no soporta umbrales distintos
> por módulo en un solo comando — cada módulo requiere su
> propia medición y comparación contra su umbral declarado.

```python
"""
scripts/check_coverage.py
Verifica que cada módulo cumple su umbral de cobertura
declarado en 04-estrategia-pruebas §3.1.
Bloquea con exit code 1 si algún módulo está bajo su umbral.
"""

UMBRALES = {
    "src/catalogo": {"minimo": 90.0, "tipo": "branch"},
    "src/pedidos": {"minimo": 90.0, "tipo": "branch"},
    "src/stock": {"minimo": 95.0, "tipo": "branch"},
    "src/taller": {"minimo": 85.0, "tipo": "branch"},
    "src/shared": {"minimo": 80.0, "tipo": "branch"},
    "src/api": {"minimo": 80.0, "tipo": "branch"},
    "src/infrastructure": {"minimo": 70.0, "tipo": "line"},
}

# El agente implementa la lógica de lectura de coverage.xml
# (formato Cobertura XML, generado por pytest-cov) y compara
# el porcentaje de cada path declarado contra su umbral.
# Salida esperada por módulo:
#
# stock        95.2% branch  ✅ (umbral 95%)
# catalogo     91.0% branch  ✅ (umbral 90%)
# pedidos      87.3% branch  ❌ (umbral 90%) — BLOQUEA PIPELINE
# taller       86.1% branch  ✅ (umbral 85%)
#
# Exit code 1 si cualquier módulo está bajo su umbral.
# Exit code 0 si todos cumplen.
```

### 3.4 Integración en pipeline — comando ejecutable

```bash
# Etapa 3 del pipeline — pruebas unitarias (09 §7.3)
pytest tests/unit/ tests/contracts/ \
  --cov=src \
  --cov-branch \
  --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov

# Verificación de umbral por módulo — bloquea si falla
python scripts/check_coverage.py coverage.xml
```

**Regla de bloqueo:** si `check_coverage.py` retorna exit
code 1, la etapa 3 del pipeline falla y el merge se bloquea
— sin excepción, sin override manual en módulos de negocio
críticos (`pedidos` · `stock` · `taller`). Fuente: `09` §6.3 ·
RNF-20 · `07.5` pre-commit hooks (mismo principio de no
override).

### 3.5 Caso de excepción documentada — `taller` con coordinación legítima

> Referencia cruzada con `09` §2.2 DEC-CL02: si una función
> de `taller/application/use_cases/` supera 20 líneas por
> coordinación legítima entre módulos (no por mezcla de
> lógica), la excepción se documenta en el PR. Esto no
> afecta el umbral de cobertura — la función sigue
> requiriendo el mismo 85% de branch coverage que el resto
> del módulo. Una excepción de longitud no es una excepción
> de cobertura.

---
## 4. Dobles de prueba — estándar ejecutable por dependencia

> Fuente: `09 especificaciones-tecnicas` v1.0.0 §6.5.
> Este tramo declara qué tipo de doble usa el agente para
> cada dependencia externa al dominio, con la regla de
> decisión detrás de cada elección — para que el agente
> no sustituya un tipo por otro sin criterio cuando aparezca
> una dependencia nueva no listada aquí.

### 4.1 Regla de decisión — cuándo usar cada tipo

| Tipo de doble | Usar cuando | No usar cuando |
|---|---|---|
| **Fake** | Se necesita una implementación funcional simplificada, reutilizable en toda la suite | La interacción específica con la dependencia es lo que se está verificando |
| **Mock** | Lo que importa es verificar que la dependencia fue llamada — con qué argumentos, cuántas veces | Solo se necesita un valor de retorno fijo |
| **Stub** | Solo se necesita controlar qué retorna la dependencia, sin verificar la interacción | Se necesita lógica real, aunque sea simplificada |
| **Spy** | Se necesita la implementación real funcionando + verificar qué pasó | La dependencia real es costosa o no determinística en test |
| **Dummy** | El test no usa la dependencia en absoluto — solo satisface la firma del constructor | La dependencia tiene cualquier efecto en el resultado del test |

### 4.2 Tabla ejecutable — doble por dependencia del sistema

| Dependencia | Doble | Justificación |
|---|---|---|
| Repositorios de dominio (`RepuestoRepository`, `PedidoRepository`, etc.) | **Fake** — `InMemoryRepository` | Reutilizable en toda la suite unitaria · debe pasar la misma suite de contrato LSP que la implementación PostgreSQL |
| `NotificacionPort` | **Mock** | La interacción importa — verificar que se notificó al cliente en cada escenario que lo requiere |
| WhatsApp Business API (vía `WhatsAppAdapter`) | **Stub** | Solo se necesita controlar la respuesta — sin llamadas reales a Meta |
| SMS — Twilio / AWS SNS (vía `SMSAdapter`) | **Stub** | Mismo criterio — sin costo por SMS en tests |
| EventBus Redis Streams | **Spy** | Envuelve la implementación real — verifica que los eventos correctos fueron publicados sin perder la lógica real del bus |
| `ParametrosSistemaPort` | **Fake** — `InMemoryParametros` | Retorna valores configurables por test · permite verificar comportamiento ante distintos parámetros sin Redis real |
| Logger · métricas | **Dummy** | No afecta el resultado del test — solo satisface la firma |
| Claude API (`LLMClientPort`) | **Mock** | Sin llamadas reales — solo aplica cuando se integre en runtime, fuera de alcance del MVP |
| Worker de temporización (reservas, deuda, reset de contador) | **Fake** — ejecución síncrona | Ejecutar síncronamente en tests sin esperar intervalos reales de minutos u horas |

### 4.3 Regla de ubicación en código
```
tests/  
├── unit/  
│ └── {modulo}/  
│ └── conftest.py ← fixtures de Fake/Stub/Dummy por módulo  
├── contracts/  
│ └── test_contrato_*.py ← valida Fake e implementación real  
│ contra el mismo Protocol  
└── integration/  
└── conftest.py ← fixtures de Spy sobre infraestructura real
```
**Regla de reutilización:** un `Fake` declarado para un módulo
no se reimplementa en otro test del mismo módulo — vive una
sola vez en `conftest.py` y se inyecta como fixture de pytest.
Referencia: DEC-CL08 — Boy Scout Rule, evitar duplicación.

### 4.4 Caso crítico — Spy del EventBus y verificación de CT-08-01

> El Spy del EventBus es el doble más usado en pruebas de
> integración porque es el único mecanismo que permite
> verificar simultáneamente: que el evento correcto fue
> publicado, en el tópico correcto, y que el consumer
> group correcto lo recibió — sin mockear la lógica real
> de Redis Streams que se está validando.

```python
# Patrón ejecutable — no implementación completa
class EventBusSpy:
    """
    Envuelve el EventBus real. Registra cada evento
    publicado sin alterar su comportamiento. Permite
    aserciones del tipo:
    spy.fue_publicado("reserva.creada")
    spy.fue_publicado_en_topico("reserva.creada", "reserva")
    spy.conteo_publicaciones("reserva.creada") == 1
    """
```

Este Spy es el doble requerido para el caso de prueba
CT-08-01 (`pedidos-group` con 8 tópicos) declarado en
`09 especificaciones-tecnicas` §6.7 — se retoma con su
escenario completo en el tramo 5 de este documento.

---
## 5. Seeds de prueba — tres niveles ejecutables

> Fuente: `09 especificaciones-tecnicas` v1.0.0 §6.6 ·
> `07 modelo-datos` v1.0.0 §6 — estrategia de seed completa.
> Este tramo sintetiza ambas fuentes en comandos ejecutables
> por nivel, sin reproducir el proceso completo de importación
> Excel Bajaj/TVS que `07` §6.2 ya documenta — esa referencia
> se mantiene íntegra en `07`, no se duplica aquí.

### 5.1 Tabla de niveles — volumen por entidad

| Nivel | Repuestos | Pedidos | Clientes | OT taller | Reabastecimientos | Propósito |
|---|---|---|---|---|---|---|
| Mínimo | 5 | 3 | 2 | 2 | 1 | Smoke tests · verificación rápida post-deploy |
| Estándar | 25 | 15 | 10 | 8 | 5 | Suite de integración completa · pipeline CI |
| Completo | 55 | 50 | 30 | 20 | 10 | Pruebas de rendimiento — RNF-01 a RNF-04 |

### 5.2 Reglas de contenido obligatorio por nivel

> Estas reglas son más estrictas que el volumen — un seed
> con el conteo correcto pero sin esta cobertura de estados
> no cumple el criterio de verificación.

```
Seed Estándar — contenido obligatorio:  
□ Al menos un repuesto por cada estado de disponibilidad:  
disponible · no_disponible · bajo_pedido  
□ Al menos una orden_trabajo por cada estado del ciclo  
de vida: ABIERTA · LISTA_REPUESTOS · EN_EJECUCION ·  
REVISION_FINAL · CERRADA · CANCELADA  
□ Clientes de los tres segmentos activos: S1 · S2 · S4  
□ Al menos un pedido en cada estado: BORRADOR ·  
CONFIRMADO · EN_PREPARACION · DESPACHADO · ENTREGADO ·  
INCIDENCIA · CANCELADO
```
Fuente: `09` §6.6 · estados declarados en `07` §2.3 y §2.4.

### 5.3 Estructura de archivos de seed — ejecutable
```
scripts/seed/  
├── seed_minimo.py ← nivel mínimo · CI · smoke tests  
├── seed_estandar.py ← nivel estándar · staging · integración  
├── seed_completo.py ← nivel completo · rendimiento  
├── fixtures/  
│ ├── repuestos.py ← generadores Faker por universo  
│ ├── clientes.py ← generadores Faker por segmento  
│ ├── ordenes_trabajo.py ← generadores Faker por estado de ciclo de vida  
│ └── pedidos.py ← generadores Faker por estado  
└── importacion_excel/  
└── (proceso de 07 modelo-datos §6.2 — no se duplica aquí)
```
### 5.4 Comandos ejecutables por nivel

```bash
# Nivel mínimo — CI, cada pipeline run
python scripts/seed/seed_minimo.py

# Nivel estándar — staging, antes de validación de Elena
python scripts/seed/seed_estandar.py

# Nivel completo — solo para pruebas de rendimiento dirigidas
python scripts/seed/seed_completo.py
```

### 5.5 Regla de datos sintéticos — vinculante sin excepción
```
□ Todos los seeds usan Faker — librería faker (Python)  
□ Ningún dato corresponde a clientes o transacciones  
reales de Tecnimotos — RNF-25 · Ley 29733  
□ Nombres, teléfonos, DNI generados con Faker localizado  
a Perú (es_PE) cuando el provider lo soporte — sin  
coincidencia accidental con personas reales  
□ Ningún seed de prueba se ejecuta contra la base de  
datos de producción bajo ninguna condición
```
**Regla crítica de separación de entornos:** el script de
seed verifica la variable de entorno `ENVIRONMENT` antes de
ejecutar — si `ENVIRONMENT == "production"`, el script aborta
con exit code 1 sin tocar la base de datos. Esto previene que
un comando de seed ejecutado por error sobrescriba datos
reales de Elena. Referencia: P1 — sin datos sensibles ·
RNF-25.

### 5.6 Conexión con cobertura de presentación — tramo 1

El seed estándar es el que debe estar cargado cuando Sant
levanta el reporte HTML de cobertura (§2.4 de este documento)
para mostrar a Elena — un seed con cobertura de todos los
estados del ciclo de vida permite que las pruebas de
integración ejerciten las rutas de código que el reporte
HTML muestra como cubiertas o no cubiertas de forma
representativa, no artificial.

---
## 6. Suites de contrato LSP — prioritarias en MVP

> Fuente: `09 especificaciones-tecnicas` v1.0.0 §6.8 ·
> `08 contratos-interfaces` §4. Cada suite valida que toda
> implementación de un Protocol cumple el mismo contrato
> de comportamiento — corre contra la implementación en
> memoria (Fake) y contra la implementación real (PostgreSQL
> o adaptador externo) con los mismos casos de prueba.

### 6.1 Regla de ejecución de una suite de contrato
```
1. La suite define los casos de prueba UNA SOLA VEZ,  
    parametrizados por implementación.
2. Se ejecuta en CI contra: implementación Fake (memoria).
3. Se ejecuta en staging contra: implementación real  
    (PostgreSQL, WhatsApp/SMS adapter según el Protocol).
4. Pasa en memoria + pasa en real → LSP cumplido.
5. Pasa en memoria + falla en real → LSP violado →  
    bloquea deploy — la implementación real no respeta  
    el contrato que el dominio espera.
```
Fuente: `09` §3.2 LSP — criterio de verificación.

### 6.2 Tabla ejecutable — 7 suites del MVP

| Suite | Archivo | Protocol | Implementaciones validadas |
|---|---|---|---|
| Catálogo-Pedidos | `tests/contracts/test_contrato_catalogo_pedidos.py` | `CatalogoPedidosPort` | `InMemoryCatalogo` · `CatalogoPostgres` |
| Catálogo-Taller | `tests/contracts/test_contrato_catalogo_taller.py` | `CatalogoTallerPort` | `InMemoryCatalogo` · `CatalogoPostgres` |
| Stock-Pedidos | `tests/contracts/test_contrato_stock_pedidos.py` | `StockPedidosPort` | `InMemoryStock` · `StockPostgres` |
| Stock-Taller | `tests/contracts/test_contrato_stock_taller.py` | `StockTallerPort` | `InMemoryStock` · `StockPostgres` |
| Taller-Pedidos | `tests/contracts/test_contrato_taller_pedidos.py` | `TallerPedidosPort` | `InMemoryTaller` · `TallerPostgres` |
| Notificación | `tests/contracts/test_contrato_notificacion.py` | `NotificacionPort` | `WhatsAppAdapter` · `SMSAdapter` |
| Parámetros | `tests/contracts/test_contrato_parametros.py` | `ParametrosSistemaPort` | `InMemoryParametros` · `ParametrosPostgresRedis` |

**Regla de generación de archivo nuevo:** cuando se declare
un Protocol nuevo en `08 contratos-interfaces` §4 vía parche
futuro, el agente genera su suite siguiendo el patrón
`test_contrato_{origen}_{destino}.py` — sin excepción, sin
Protocol sin suite.

---

## 7. Pruebas E2E — flujos críticos del MVP

> Fuente: `09` §6.4. Ejecutan en pipeline nocturno separado
> — no bloquean cada commit, pero bloquean el release semanal
> si fallan. Fuente del trigger: `09` §7.4 `e2e-nightly.yml`.

### 7.1 Tabla ejecutable — 3 flujos críticos

| ID | Flujo | Criterio de éxito ejecutable | HU origen |
|---|---|---|---|
| E2E-01 | Consulta de catálogo y reserva de repuesto | Cliente busca repuesto → verifica disponibilidad → crea reserva → `stock_repuesto.cantidad_apartada` refleja el cambio en ≤ 3 pasos desde simulación de móvil Android | HU-S1-01 · HU-S1-02 |
| E2E-02 | Ciclo completo de orden_trabajo con cobro | Mecánico abre OT → lista aprobada → ejecución → revisión final → cobro → cierre → `stock_repuesto` descontado atómicamente sin discrepancia | HU-INT-02 · HU-INT-03 · HU-INT-04 |
| E2E-03 | Pedido remoto de distrito con proforma y envío | S2 consulta lista → crea pedido → recibe proforma ajustada por Elena → confirma → `envio` registrado → notificación WhatsApp enviada (Stub verificado) | HU-S2-02 · HU-S2-04 |

### 7.2 Comando ejecutable

```bash
pytest tests/e2e/ -v --tb=short
```

### 7.3 Trigger de ejecución — referencia cruzada

Ejecuta vía workflow `e2e-nightly.yml` a las 02:00 UTC
(21:00 UTC-5). Si falla, bloquea el release semanal — la
acción concreta ante fallo nocturno se define en
`11 plan-operacion` (CT-09-07, ya delegado desde `09`).

---

## 8. Casos de prueba obligatorios — CT salientes de `08`

> Fuente: `09 especificaciones-tecnicas` §6.7. Estos 16 casos
> ya están descritos en detalle en `09` — este tramo no los
> reproduce campo por campo (violaría P2), sino que declara
> el índice ejecutable de qué archivo de test implementa
> cada uno y su estado de resolución, para que el agente
> sepa exactamente dónde generar cada prueba sin reabrir `09`
> para los 10 casos ya resueltos directamente ahí.

### 8.1 Índice ejecutable — ubicación de cada CT obligatorio

| CT       | Archivo de test                                                            | Tipo                         | Resuelto directamente o delega                                             |
| -------- | -------------------------------------------------------------------------- | ---------------------------- | -------------------------------------------------------------------------- |
| CT-08-01 | `tests/integration/test_pedidos_group_topicos.py`                          | Integración                  | Directo — ver `09` §6.7                                                    |
| CT-08-02 | `tests/unit/taller/test_ep_tal_11_response_dual.py` + `tests/integration/` | Unitaria + integración       | Directo                                                                    |
| CT-08-03 | `tests/integration/test_outbox_fallo_redis.py`                             | Integración — SDD            | Directo                                                                    |
| CT-08-04 | `tests/integration/test_idempotencia_evento_duplicado.py`                  | Integración — SDD            | Directo                                                                    |
| CT-08-05 | `tests/unit/catalogo/test_reset_precio_utc5.py` + integración              | Unitaria + integración — SDD | Directo                                                                    |
| CT-08-06 | `tests/integration/test_descuento_atomico_fallo_parcial.py`                | Integración — SDD            | Directo — requiere PostgreSQL real, sin Fake                               |
| CT-08-07 | —                                                                          | Seguridad                    | Delega a `10 seguridad-formal`                                             |
| CT-08-08 | `tests/integration/test_bloqueo_ip_login.py`                               | Integración — SDD            | Directo                                                                    |
| CT-08-09 | —                                                                          | Seguridad                    | Delega a `10 seguridad-formal`                                             |
| CT-08-10 | `tests/integration/test_monto_descuento_control_servidor.py`               | Integración                  | Directo                                                                    |
| CT-08-11 | —                                                                          | Seguridad                    | Delega a `10 seguridad-formal`                                             |
| CT-08-12 | `tests/integration/test_replay_detection_refresh_token.py`                 | Integración — SDD            | Directo                                                                    |
| CT-08-13 | —                                                                          | Operacional                  | Delega a `11 plan-operacion`                                               |
| CT-08-14 | —                                                                          | Operacional                  | Delega a `11 plan-operacion` (ver `reset-precio.yml` en tramo de pipeline) |
| CT-08-15 | —                                                                          | Operacional                  | Delega a `11 plan-operacion`                                               |
| CT-08-16 | `tests/integration/test_consistencia_post_fallo_consumidor.py`             | Integración — SDD            | Directo                                                                    |

**Resultado: 10 casos con archivo de test ejecutable directo ·
6 casos delegados a `10` o `11` — consistente con el cierre
de `09` §8.3.**

### 8.2 Regla de bloqueo por CT obligatorio

Un CT obligatorio sin su archivo de test correspondiente
implementado significa que el sistema no puede considerarse
validado, incluso si los umbrales de cobertura del tramo 2
están cumplidos. Cobertura alta sin estos 10 casos directos
cubiertos es cobertura incompleta en el sentido que importa.
Fuente: `09` §6.7 — nota introductoria.

---
## 9. Definition of Done — verificación ejecutable por funcionalidad

> Fuente: `09 especificaciones-tecnicas` v1.0.0 §6.9.
> Una funcionalidad no se considera terminada sin cumplir
> cada ítem de esta lista — el agente verifica esto antes
> de marcar cualquier HU como completada en
> `05-trazabilidad-ligera`.

### 9.1 Checklist ejecutable
```
□ Pruebas unitarias escritas con TDD o en paralelo al código  
□ Escenarios BDD de la HU correspondiente ejecutables y pasando  
□ Cobertura de branch ≥ umbral del módulo — tramo 2 §3.1  
□ Todos los tests pasan en el pipeline de CI  
□ SAST sin hallazgos de severidad alta  
□ Sin datos reales en fixtures de prueba — Faker obligatorio,  
tramo 4 §5.5  
□ Suite de contrato LSP del Protocol afectado pasa en memoria  
— tramo 5 §6  
□ Contrato de API en 08 no requiere modificación — o el  
parche está documentado  
□ Smoke tests pasan en staging después del deploy  
□ CT saliente de 08 correspondiente cubierto, si la  
funcionalidad lo tiene asignado — tramo 5 §8
```
### 9.2 Regla de verificación cruzada entre tramos

Este checklist no es independiente de los tramos anteriores
de este documento — cada ítem referencia exactamente dónde
se ejecuta su verificación. Un agente que complete este
checklist necesitó ejecutar comandos del tramo 1, umbrales
del tramo 2, dobles del tramo 3, seeds del tramo 4 y suites
del tramo 5 — la Definition of Done es la síntesis operativa
de todo el documento, no una sección aislada.

---

## 10. Criterio de pipeline verde

> Define cuándo el conjunto completo de pruebas se considera
> "verde" para efectos de DEC-P06 — deploy automático a
> staging. Fuente: `09` §7.1 DEC-P06 · §7.3 etapas 3 y 4.

### 10.1 Condición ejecutable de pipeline verde
```
Pipeline verde SI Y SOLO SI:

1. Suite de contratos LSP — 7/7 suites pasan (tramo 5 §6.2)
2. Pruebas unitarias — 100% de tests pasan
3. check_coverage.py — exit code 0 (tramo 2 §3.3)
4. Pruebas de integración — 100% de tests pasan
5. Los 10 CT directos de §8.1 — todos con su test  
    correspondiente pasando
6. SAST y SCA — sin hallazgos bloqueantes (DEC-P04)

Si cualquier condición falla → pipeline rojo →  
merge bloqueado → no hay deploy a staging.
```
### 10.2 Relación con pruebas E2E — no bloquean cada commit

Las pruebas E2E (tramo 5 §7) NO forman parte del criterio
de pipeline verde por commit — corren en `e2e-nightly.yml`
y su fallo bloquea el release semanal, no el merge individual.
Esta distinción es intencional: E2E son lentas y su fallo
nocturno no debe detener el flujo de desarrollo diario.
Fuente: `09` §6.4 · §7.4.

---

## 11. Observaciones activas

### 11.1 Observación heredada — verificación de resolución

Este documento no recibió observaciones heredadas explícitas
en su activación (a diferencia de `03-diseno-sistema`, que
heredó 5 de `02-definicion-funcional`). Su única fuente,
`09 especificaciones-tecnicas`, no generó observaciones
pendientes hacia `04` en su cierre — solo generó CT hacia
`10` y `11`, ya indexados en tramo 5 §8.1 de este documento.

### 11.2 Observación generada en esta construcción — gap de matriz DOC-3

| ID | Observación | Naturaleza | Acción recomendada |
|---|---|---|---|
| OBS-EP-001 | `10 seguridad-formal` y `11 plan-operacion` del DOC-2 están cerrados con contenido ejecutable real (OWASP Top 10, JWT+MFA+RBAC+ABAC, Ley 29733 en `10`; despliegue por fases, RTO/RPO, runbooks, backups 3-2-1 en `11`), pero la matriz de archivos vivos del DOC-3 no declara un archivo equivalente que tome esos documentos como fuente. Los 6 CT delegados en tramo 5 §8.1 (CT-08-07/09/11/13/14/15) quedan sin destino ejecutable en DOC-3 hasta que esto se resuelva | Gap de cobertura en el mapa de ejecución del DOC-3 — no en DOC-2, que está completo | Revisar `mapa-de-ejecucion.md` del DOC-3 inmediatamente después del cierre de este documento, antes de iniciar `05-trazabilidad-ligera`. Posible necesidad de declarar archivos nuevos — por ejemplo `08-criterios-seguridad-ejecutables` y `09-plan-operacion-ejecutable` |

---

## 12. Fuentes

| Documento | Versión | Secciones consultadas |
|---|---|---|
| `09 especificaciones-tecnicas` | v1.0.0 | §6 estrategia de pruebas completa · §6.1 a §6.9 · §7.1 DEC-P06 · §7.3 · §7.4 · §8.3 |
| `07 modelo-datos` | v1.0.0 | §6 estrategia de seed |
| `03-diseno-sistema` (DOC-3) | v1.0.0 | §5 esquema de datos — referencia de tablas para fixtures de seed |

---

## 13. Historial de versiones

| Versión | Fecha   | Cambio                                                                                                                                                                                     | Impacto                                                               |
| ------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| 0.1.0   | 2026-06 | Tramo 1 — frontmatter · propósito · comandos de ejecución por módulo · reporte HTML para revisión humana                                                                                   | Base ejecutable + audiencia no técnica contemplada                    |
| 0.2.0   | 2026-06 | Tramo 2 — umbrales de cobertura ejecutables · script de verificación por módulo                                                                                                            | Bloqueo de pipeline automatizable                                     |
| 0.3.0   | 2026-06 | Tramo 3 — 9 dobles de prueba indexados con regla de decisión                                                                                                                               | Estándar de testing sin ambigüedad                                    |
| 0.4.0   | 2026-06 | Tramo 4 — 3 niveles de seed con reglas de contenido obligatorio, no solo volumen                                                                                                           | Datos de prueba representativos y seguros                             |
| 0.5.0   | 2026-06 | Tramo 5 — 7 suites LSP · 3 flujos E2E · 16 CT indexados (10 directos · 6 delegados)                                                                                                        | Verificación de contratos y casos obligatorios completa               |
| 0.9.0   | 2026-06 | Tramo 6 — DoD · criterio de pipeline verde · OBS-EP-001 registrada                                                                                                                         | Documento completo — pendiente cierre formal                          |
| 1.0.0   | 2026-06 | Tramo de cierre formal — confirmación de Sant como validador, campo `aprobado` corregido de `false` a `true`. Historial interno sincronizado con frontmatter (previamente reflejaba 0.9.0) | Documento cerrado y aprobado — listo para verificación cruzada global |

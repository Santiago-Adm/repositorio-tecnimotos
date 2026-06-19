---
version: 1.0.0
estado: cerrado
bloque: E
seccion: "03"
titulo: Diseño del sistema
autor: Sant
fecha: 2026-06
validador: Sant
aprobado: true
fuentes:
  - 06 arquitectura-sistema v1.0.0
  - 07 modelo-datos v1.0.0
  - 08 contratos-interfaces v1.0.0
ct_pendientes: []
alimenta_doc3: true
tramo_actual: 1 de 7 — frontmatter · propósito · estructura de módulos
cambio: Tramo 1 — frontmatter inicial · propósito · estructura de módulos con árbol ejecutable
impacto: Activa la construcción del archivo objetivo de la sesión DOC-3
---

# 03 — Diseño del sistema
## Tecnimotos Santi · DOC-3 — Protocolo de construcción

> Este archivo responde al agente: ¿cómo está organizado
> lo que voy a construir y qué contratos debo respetar?
> Fuente: `06 arquitectura-sistema` v1.0.0 ·
> `07 modelo-datos` v1.0.0 · `08 contratos-interfaces` v1.0.0.
> El agente consulta este archivo para tareas de estructura,
> stack y setup. Para esquema de datos detallado, contratos
> OpenAPI/AsyncAPI y puertos internos, este archivo referencia
> las secciones siguientes — no las repite aquí en tramo 1.

---

## 1. Propósito

Este archivo instruye al agente sobre la organización
física del sistema y los contratos estructurales que
debe respetar antes de escribir una sola línea de código.

El agente que lee este archivo puede:
levantar el entorno de desarrollo desde cero ·
crear el árbol de directorios exacto del `api-server` ·
identificar qué módulo es dueño de qué responsabilidad ·
verificar que la estructura no viola las fronteras
declaradas en `06 arquitectura-sistema` ADR-001.

Este archivo no explica por qué se tomó cada decisión
— esa justificación vive en `06`, `07` y `08` del DOC-2.
Este archivo dice qué construir, en qué orden y cómo
verificarlo. Referencia: P6 — lenguaje ejecutable.

---

## 2. Estructura de módulos

### 2.1 Regla de organización — vinculante

El sistema es un **Modular Monolith** — un único proceso
desplegable `api-server` con cuatro módulos de dominio
con fronteras explícitas. Ningún módulo importa directamente
desde otro módulo. Toda comunicación entre módulos pasa por:
puertos hexagonales declarados en `08 contratos-interfaces` §4
para comunicación síncrona · eventos Redis Streams declarados
en `08 contratos-interfaces` §5 para comunicación asíncrona.

Fuente: `06 arquitectura-sistema` §2 ADR-001.

### 2.2 Árbol de directorios ejecutable — raíz del repositorio
```
repositorio-tecnimotos/  
├── .doc3/  
│ └── (protocolo de construcción — no se modifica desde código)  
├── src/  
│ ├── shared/  
│ │ ├── domain/  
│ │ ├── events/  
│ │ └── infrastructure/  
│ ├── catalogo/  
│ ├── pedidos/  
│ ├── stock/  
│ └── taller/  
├── api/  
│ ├── routes/  
│ └── dependencies.py  
├── infrastructure/  
│ ├── database/  
│ ├── redis/  
│ ├── notifications/  
│ ├── llm/  
│ │ └── prompts/  
│ └── factories.py  
├── scripts/  
│ ├── check_dip.py  
│ └── seed/  
├── tests/  
│ ├── unit/  
│ ├── contracts/  
│ ├── integration/  
│ └── e2e/  
├── infra/  
│ └── terraform/  
├── .github/  
│ └── workflows/  
├── docker-compose.yml  
├── docker-compose.dev.yml  
├── docker-compose.prod.yml  
└── pyproject.toml
```
**Verificación de esta estructura:** `scripts/check_dip.py`
ejecuta sobre `src/` y bloquea el pipeline si algún archivo
en `{modulo}/domain/` importa desde `{modulo}/infrastructure/`
o desde otro módulo. Fuente: `09 especificaciones-tecnicas` §3.2 DIP.

### 2.3 Árbol de directorios ejecutable — por módulo de dominio

Aplica idéntico a `catalogo` · `pedidos` · `stock` · `taller`.
Sustituir `{modulo}` por el nombre exacto del módulo.
```
src/{modulo}/  
├── domain/  
│ ├── models/  
│ ├── ports/  
│ └── services/  
├── application/  
│ └── use_cases/  
└── infrastructure/  
├── repositories/  
└── adapters/
```
**Regla de contenido por capa:**

| Capa | Contiene | No contiene |
|---|---|---|
| `domain/models/` | Entidades · Value Objects como `@dataclass(frozen=True)` | Ningún import de FastAPI, SQLAlchemy ni Redis |
| `domain/ports/` | Protocols mínimos — un Protocol por necesidad real del use case | Implementaciones concretas |
| `domain/services/` | Reglas de negocio puras | Acceso a base de datos o red |
| `application/use_cases/` | Un archivo por caso de uso — orquestación | Lógica de negocio que debería vivir en `domain/services/` |
| `infrastructure/repositories/` | Implementaciones SQLAlchemy de los Protocols de `domain/ports/` | Reglas de negocio |
| `infrastructure/adapters/` | Implementaciones de servicios externos (WhatsApp, SMS) | Reglas de negocio |

Fuente: `09 especificaciones-tecnicas` §3.3.

### 2.4 Mapa de responsabilidad por módulo

| Módulo | Responsabilidad única | Tablas que posee | No accede directamente a |
|---|---|---|---|
| `catalogo` | Registro maestro de repuestos · precio de venta · disponibilidad | `repuesto` · `historial_precio_repuesto` | Tablas de `pedidos`, `stock`, `taller` |
| `pedidos` | Ciclo de vida comercial — pedido, reserva, proforma, envío, comprobante | `pedido` · `pedido_item` · `reserva` · `lista_reserva_progresiva` · `lista_reserva_progresiva_item` · `proforma` · `envio` · `comprobante` · `deuda_activa` · `cliente` | Tablas de `catalogo`, `stock`, `taller` |
| `stock` | Verdad del inventario físico en tres estados | `stock_repuesto` · `movimiento_stock` · `reabastecimiento` · `reabastecimiento_item` · `notificacion_stock_cliente` | Tablas de `catalogo`, `pedidos`, `taller` |
| `taller` | Ciclo de vida de intervención técnica sobre vehículo | `vehiculo` · `mecanico` · `mecanico_perfil` · `orden_trabajo` · `lista_repuestos_ot` · `costo_adicional_ot` · `historial_intervencion` · `entrada` · `historial_cobro_mecanico` · `rendicion_mecanico` | Tablas de `catalogo`, `pedidos`, `stock` |
| `shared` | Identidad, sesiones, parámetros, outbox — infraestructura transversal | `usuario` · `usuario_perfil` · `sesion` · `parametros_sistema` · `outbox_events` | — accesible por todos los módulos vía puerto declarado |

Fuente: `07 modelo-datos` §1.1 — Dueño único de dato ·
`06 arquitectura-sistema` §7 mapa de puertos.

**Regla de acceso cruzado:** ningún módulo lee ni escribe
directamente sobre una tabla que no posee. Todo acceso
cruzado pasa por el puerto declarado en `08 contratos-interfaces`
§4 — la tabla 4.8 mapa de dependencias entre puertos es
la fuente de verdad de qué módulo puede llamar a cuál.

---
## 3. Stack con versiones exactas

> Fuente: `06 arquitectura-sistema` §6 stack tecnológico
> justificado por capa. Este tramo no repite la
> justificación — esa vive en `06`. Aquí se declara
> únicamente la versión exacta y el comando de
> instalación o configuración ejecutable.

### 3.1 Capa de dominio y aplicación

| Tecnología | Versión exacta | Comando de instalación |
|---|---|---|
| Python | `3.12` | `pyenv install 3.12 && pyenv local 3.12` |
| FastAPI | `>=0.115,<0.116` | `pip install "fastapi[standard]>=0.115,<0.116"` |
| Pydantic | `>=2.9,<3.0` | incluido en `fastapi[standard]` |
| SQLAlchemy | `>=2.0,<2.1` | `pip install "sqlalchemy[asyncio]>=2.0,<2.1"` |
| Alembic | `>=1.13,<1.14` | `pip install "alembic>=1.13,<1.14"` |

### 3.2 Capa de infraestructura de datos

| Tecnología | Versión exacta | Comando de instalación |
|---|---|---|
| PostgreSQL | `16` | imagen Docker `postgres:16` |
| Redis | `7` | imagen Docker `redis:7` |
| asyncpg | `>=0.29,<0.30` | `pip install "asyncpg>=0.29,<0.30"` |
| redis-py | `>=5.0,<6.0` | `pip install "redis>=5.0,<6.0"` |

### 3.3 Capa de presentación

| Tecnología | Versión exacta | Comando de instalación |
|---|---|---|
| Node.js | `20 LTS` | `nvm install 20 && nvm use 20` |
| Next.js | `14.2` | `npx create-next-app@14.2 --typescript --tailwind --app` |
| TypeScript | `>=5.4,<5.5` | incluido en `create-next-app` |
| Tailwind CSS | `>=3.4,<3.5` | incluido en `create-next-app` |
| React Query | `>=5.0,<6.0` | `npm install @tanstack/react-query@^5.0` |

**Nota de bloqueo:** la configuración de tema Tailwind
(colores, tipografía, tokens) no se ejecuta en este tramo.
Depende de la identidad visual del sistema — sección
pendiente fuera de alcance de `03-diseno-sistema`.
El agente instala Tailwind con configuración por defecto
y no debe inventar paleta ni tipografía sin esa fuente.

### 3.3.1 Identidad visual — tokens ejecutables (resuelve bloqueo previo)

> Fuente: decisión de marca SANTI (Sistema de Asistencia y
> Núcleo Técnico Integral), validada en sesión paralela de
> identidad visual. Nombre de marca SANTI es de presentación
> únicamente — el DOC-3 y el código interno NO usan "SANTI"
> como nombre de dominio, servicio o variable; el sistema
> interno sigue siendo "Tecnimotos Santi" en toda referencia
> de negocio y dominio.

**Paleta de colores — tokens CSS (Tailwind theme.extend.colors):**

| Token | Valor hex | Uso |
|---|---|---|
| `--color-teal` | `#0D9488` | Color primario — botones de acción confirmatoria ("Autorizar Reparación", "Stock Disponible"), logo, estado positivo |
| `--color-electric` | `#8B5CF6` | Color secundario — urgencia/asistencia, acentos de atención, estados de alerta no críticos |
| `--color-surface-dark` | `#0F172A` | Fondo "Modo Taller" — interfaz interna de mecánicos y ventas (reduce fatiga visual, oculta suciedad de UI en campo) |
| `--color-surface-light` | `#F8FAFC` | Fondo "Interfaz Pública" — catálogo de clientes, proformas PDF |

**Regla de aplicación por superficie — vinculante:**
```
INTERFAZ INTERNA (catalogo admin, taller, stock):  
fondo: --color-surface-dark  
acento primario: --color-teal  
acento secundario: --color-electric

INTERFAZ PÚBLICA (catálogo cliente, proformas PDF):  
fondo: --color-surface-light  
acento primario: --color-teal  
texto: slate oscuro — sin valor hex aún, usar  
default de Tailwind slate-800 hasta nueva  
especificación
```
**Tipografía — Google Fonts, pesos ejecutables:**

| Fuente | Uso | Variable CSS |
|---|---|---|
| `Quicksand` | Logotipo, H1/H2, títulos de proformas PDF, pantallas de carga | `--font-display` |
| `Nunito Sans` | Párrafos, navegación, botones, mensajes WhatsApp/SMS | `--font-body` |
| `Fira Code` | Códigos de repuesto (`codigo` en `Repuesto`), placas de vehículo, teléfonos, precios en tablas | `--font-mono` |

**Comando de instalación — reemplaza la configuración por defecto declarada antes:**
```bash
npm install @next/font
# o vía Google Fonts CDN en next/font/google:
# Quicksand, Nunito_Sans, Fira_Code
```

**Logo y assets:** el agente NO genera el logo — los archivos SVG (variantes: positivo, negativo, isotipo, ícono de app) son entregados como assets estáticos en `frontend/public/brand/` por Sant. El agente solo referencia las rutas, no genera el diseño.

**Regla de no invención:** el agente no introduce colores, tipografías ni variantes de logo fuera de esta tabla sin parche formal sobre este archivo.
### 3.4 Capa de infraestructura operativa

| Tecnología | Versión exacta | Comando de instalación |
|---|---|---|
| Docker | `>=24.0` | instalación de sistema — fuera de pip/npm |
| Docker Compose | `v2` | incluido en Docker Desktop o `docker-compose-plugin` |
| Ruff | `>=0.6,<0.7` | `pip install "ruff>=0.6,<0.7"` |
| Mypy | `>=1.11,<1.12` | `pip install "mypy>=1.11,<1.12"` |
| pytest | `>=8.3,<8.4` | `pip install "pytest>=8.3,<8.4" pytest-asyncio` |
| pre-commit | `>=3.8,<3.9` | `pip install "pre-commit>=3.8,<3.9"` |

### 3.5 Capa de integración externa

| Tecnología | Configuración | Variable de entorno requerida |
|---|---|---|
| WhatsApp Business API | Token en variable de entorno | `WHATSAPP_API_TOKEN` |
| SMS — Twilio o AWS SNS | Credenciales en variable de entorno | `SMS_PROVIDER` · `SMS_API_KEY` |
| Fernet | `cryptography>=43.0,<44.0` | `FERNET_KEY` — generado con `Fernet.generate_key()` |

**Regla P1 vinculante:** ningún valor real de estas
variables aparece en este documento ni en ningún archivo
del DOC-3. Solo el nombre de la variable.

---

## 4. Comandos de setup del entorno — desde cero

> Criterio de verificación del tramo: el agente ejecuta
> esta secuencia en un entorno limpio y obtiene un
> `api-server` funcional sin consultar el DOC-2.

### 4.1 Backend — secuencia ejecutable

```bash
# 1. Clonar y entrar al repositorio
git clone {url_repositorio} && cd repositorio-tecnimotos

# 2. Python 3.12 con entorno virtual
pyenv install 3.12
pyenv local 3.12
python -m venv .venv
source .venv/bin/activate

# 3. Dependencias backend
pip install "fastapi[standard]>=0.115,<0.116"
pip install "sqlalchemy[asyncio]>=2.0,<2.1" "asyncpg>=0.29,<0.30"
pip install "alembic>=1.13,<1.14"
pip install "redis>=5.0,<6.0"
pip install "cryptography>=43.0,<44.0"
pip install "ruff>=0.6,<0.7" "mypy>=1.11,<1.12"
pip install "pytest>=8.3,<8.4" pytest-asyncio pytest-cov
pip install "pre-commit>=3.8,<3.9"

# 4. Pre-commit hooks
pre-commit install

# 5. Variables de entorno — copiar plantilla, nunca commitear valores reales
cp .env.example .env

# 6. Levantar PostgreSQL y Redis locales
docker compose -f docker-compose.dev.yml up -d postgres redis

# 7. Migraciones — crea las 28 tablas declaradas en 07 modelo-datos
alembic upgrade head

# 8. Seed nivel mínimo — 1 SUPERADMIN · 5 repuestos
python scripts/seed/seed_minimo.py

# 9. Levantar el api-server
uvicorn api.main:app --reload --port 8000
```

### 4.2 Frontend — secuencia ejecutable

```bash
# 1. Entrar al directorio frontend
cd frontend

# 2. Node 20 LTS
nvm install 20
nvm use 20

# 3. Instalar dependencias
npm install

# 4. Variables de entorno — copiar plantilla
cp .env.local.example .env.local

# 5. Levantar en modo desarrollo
npm run dev
```

### 4.3 Verificación post-setup — smoke test ejecutable

```bash
# Backend responde
curl http://localhost:8000/v1/health
# Esperado: {"data":{"estado":"ok","version":"...","timestamp":"..."}}

# Catálogo responde con seed cargado
curl http://localhost:8000/v1/repuestos?universo=mototaxi \
  -H "Authorization: Bearer {token_test}"
# Esperado: HTTP 200 con array de 5 repuestos del seed mínimo
```

Fuente smoke tests: `09 especificaciones-tecnicas` §7.6
ST-01 y ST-02.

---
## 5. Esquema de datos ejecutable

> Fuente: `07 modelo-datos` v1.0.0 §2 a §4 — 28 tablas
> declaradas con tipos, restricciones, índices y relaciones.
> Este tramo no reproduce las 28 tablas completas con su
> diccionario de datos extendido — eso violaría P2 síntesis
> sin duplicación. Aquí se declara la lista ejecutable de
> tablas por módulo con sus campos clave, restricciones
> CHECK críticas e índices — suficiente para que el agente
> genere los modelos SQLAlchemy y las migraciones Alembic
> sin reabrir `07 modelo-datos` salvo para diccionario de
> datos extendido en campos de cifrado o políticas.

### 5.1 Regla de generación

El agente genera un archivo de modelo SQLAlchemy por tabla
en `infrastructure/repositories/models/{tabla}.py` dentro
del módulo dueño declarado en §2.4 de este documento.
Toda tabla usa `UUID v4` como PK · `TIMESTAMPTZ` en
`created_at`/`updated_at` · snake_case singular.
Fuente: `07 modelo-datos` §1.2 convenciones del modelo.

### 5.2 Tablas del módulo `catalogo`

| Tabla | Campos clave | CHECK críticos | Índices |
|---|---|---|---|
| `repuesto` | `codigo` UNIQUE · `universo` · `modelo` · `año` · `precio_venta` · `precio_costo` (cifrado Fernet) · `eliminado_en` | `universo IN (mototaxi, mototaxi_4r, motolineal)` · `año BETWEEN 1990 AND 2100` · `precio_venta > 0` | `idx_repuesto_busqueda (universo, modelo, año, codigo)` · `idx_repuesto_activo (activo, universo)` |
| `historial_precio_repuesto` | `repuesto_id` FK · `precio_anterior` · `precio_nuevo` · `modificado_por` FK | — | `idx_historial_precio (repuesto_id, created_at DESC)` |

### 5.3 Tablas del módulo `stock`

| Tabla | Campos clave | CHECK críticos | Índices |
|---|---|---|---|
| `stock_repuesto` | `repuesto_id` FK UNIQUE · `cantidad_disponible` · `cantidad_apartada` · `cantidad_en_transito` · `umbral_minimo` | `cantidad_disponible >= 0` · `cantidad_apartada >= 0` · `chk_stock_coherente: disponible + apartada >= 0` | `idx_stock_disponible (repuesto_id, cantidad_disponible)` |
| `movimiento_stock` | `repuesto_id` FK · `tipo_movimiento` · `cantidad` · `estado_origen` · `estado_destino` · `actor_id` FK · `referencia_id` | `cantidad > 0` · `tipo_movimiento IN (6 valores — ver 07 §2.2)` | `idx_movimiento_repuesto` · `idx_movimiento_referencia` · `idx_movimiento_actor` |
| `reabastecimiento` | `proveedor` · `estado` | `estado IN (5 valores — ver 07 §2.2)` | `idx_reabastecimiento_estado (estado, created_at DESC)` |
| `reabastecimiento_item` | `reabastecimiento_id` FK · `repuesto_id` FK · `cantidad_solicitada` · `precio_costo_unitario` (cifrado Fernet) | `cantidad_solicitada > 0` | `idx_reab_item_repuesto (repuesto_id, created_at DESC)` |
| `notificacion_stock_cliente` | `repuesto_id` FK · `cliente_id` FK · `estado` | `UNIQUE (repuesto_id, cliente_id, estado)` | `idx_notif_stock (repuesto_id, estado)` |

**Tabla de permisos de escritura crítica:** `movimiento_stock`
es la tabla `auditoria_stock` referenciada en CT-06-03 —
el rol de aplicación tiene `INSERT` pero el agente NO genera
permisos `UPDATE` ni `DELETE` en la migración para este rol.
Fuente: `07 modelo-datos` §2.2 nota de `movimiento_stock`.

### 5.4 Tablas del módulo `pedidos`

| Tabla | Campos clave | CHECK críticos | Índices |
|---|---|---|---|
| `pedido` | `cliente_id` FK nullable · `canal_origen` · `origen_actor` · `estado` · `motivo_cancelacion` · `orden_trabajo_id` FK nullable · `monto_total` · `descuento_aplicado` (cifrado Fernet) · `precio_ajustado` | `estado IN (7 valores)` · `monto_total >= 0` | `idx_pedido_cliente` · `idx_pedido_estado` · `idx_pedido_orden_trabajo` · `idx_pedido_cancelacion` · `idx_pedido_origen_actor` |
| `pedido_item` | `pedido_id` FK · `repuesto_id` FK · `cantidad` · `precio_unitario` · `precio_ajustado_unit` nullable · `subtotal` | `cantidad > 0` · `precio_unitario > 0` | `UNIQUE (pedido_id, repuesto_id)` · `idx_pedido_item_pedido` |
| `reserva` | `cliente_id` FK · `repuesto_id` FK · `pedido_id` FK nullable · `estado` · `segmento` · `expira_en` · `pago_registrado` · `notificaciones_enviadas` | `estado IN (5 valores)` · `segmento IN (3 valores)` · `notificaciones_enviadas >= 0` | `idx_reserva_cliente` · `idx_reserva_repuesto` · `idx_reserva_expiracion` · `idx_reserva_notif` |
| `lista_reserva_progresiva` | `cliente_id` FK · `nombre` nullable · `estado` · `ultima_actividad` | `estado IN (3 valores)` | `idx_lista_cliente` · `idx_lista_actividad` |
| `lista_reserva_progresiva_item` | `lista_id` FK · `repuesto_id` FK · `cantidad` · `precio_referencia` · `disponibilidad_ref` | `cantidad > 0` | `UNIQUE (lista_id, repuesto_id)` |
| `proforma` | `pedido_id` FK · `numero_referencia` UNIQUE · `estado` · `monto_total` | `estado IN (5 valores)` · `monto_total > 0` | `idx_proforma_pedido` · `idx_proforma_numero` |
| `envio` | `pedido_id` FK UNIQUE · `empresa_encomienda` · `direccion_destino` (cifrado Fernet) · `estado` | `estado IN (5 valores)` | `idx_envio_pedido` · `idx_envio_estado` |
| `comprobante` | `pedido_id` FK · `tipo` · `estado` · `monto` · `ruc_cliente` nullable · `nota_credito_id` FK self | `tipo IN (boleta, factura, ticket)` · `estado IN (3 valores)` · `monto > 0` | `idx_comprobante_pedido` · `idx_comprobante_estado` · `idx_comprobante_serie` |
| `deuda_activa` | `pedido_id` FK UNIQUE · `cliente_id` FK · `monto_deuda` · `plazo_dias` · `alerta_50_en` · `alerta_vencimiento_en` | `monto_deuda > 0` · `plazo_dias > 0` | `idx_deuda_cliente` · `idx_deuda_alerta_50` · `idx_deuda_alerta_venc` |
| `cliente` | `usuario_id` FK UNIQUE · `segmento` · `sub_rol` · `canal_preferido` · `mecanico_preferido_id` FK nullable · `nivel_visibilidad` | `segmento IN (S1-S5)` · `nivel_visibilidad IN (0,1,2)` | `idx_cliente_usuario` · `idx_cliente_segmento` |

### 5.5 Tablas del módulo `taller`

| Tabla | Campos clave | CHECK críticos | Índices |
|---|---|---|---|
| `vehiculo` | `universo` · `modelo` · `año` · `placa` nullable (cifrado Fernet) · `tarjeta_propiedad` nullable (cifrado Fernet) · `cliente_id` FK nullable · `salud_estimada` | `año BETWEEN 1990 AND 2100` · `salud_estimada BETWEEN 0 AND 100` | `idx_vehiculo_placa` · `idx_vehiculo_cliente` · `idx_vehiculo_modelo` |
| `mecanico` | `usuario_id` FK UNIQUE · `nivel` · `supervisor_id` FK self nullable · `disponible` | `nivel IN (MASTER, JUNIOR)` | `idx_mecanico_disponible` · `idx_mecanico_supervisor` |
| `mecanico_perfil` | `mecanico_id` FK UNIQUE · `dni` UNIQUE (cifrado Fernet) · `nombres` (cifrado) · `tipo_contrato` · `validado_por` FK | `tipo_contrato IN (4 valores)` | `idx_mecanico_perfil_dni` |
| `orden_trabajo` | `vehiculo_id` FK · `mecanico_master_id` FK · `mecanico_junior_id` FK nullable · `tipo_servicio` · `tipo_urgencia` · `estado` · `cliente_aprobó_lista` · `visibilidad_precio_cliente` · `cobro_confirmado` | `tipo_servicio IN (4 valores)` · `estado IN (6 valores)` | `idx_ot_vehiculo` · `idx_ot_mecanico_master` · `idx_ot_estado` · `idx_ot_cobro` |
| `lista_repuestos_ot` | `orden_trabajo_id` FK · `repuesto_id` FK · `cantidad` · `precio_unitario` · `momento_agregado` · `tramo_precio` nullable · `aprobacion_cliente` | `cantidad > 0` · `momento_agregado IN (2 valores)` · `aprobacion_cliente IN (5 valores)` | `UNIQUE (orden_trabajo_id, repuesto_id)` · `idx_lrot_orden` · `idx_lrot_aprobacion` |
| `costo_adicional_ot` | `orden_trabajo_id` FK · `lista_repuesto_id` FK · `tramo` · `monto_adicional` · `espera_hasta` nullable · `resultado` nullable | `tramo IN (3 valores)` | `idx_costo_adic_ot` · `idx_costo_adic_espera` |
| `historial_intervencion` | `vehiculo_id` FK · `orden_trabajo_id` FK UNIQUE · `mecanico_master_id` FK · `fecha_apertura` · `fecha_cierre` · `monto_final` | — | `idx_historial_vehiculo` · `idx_historial_mecanico` |
| `entrada` | `vehiculo_id` FK · `orden_trabajo_id` FK nullable · `cliente_id` FK nullable · `estado` | `estado IN (ACTIVA, CERRADA)` | `idx_entrada_vehiculo` · `idx_entrada_ot` · `idx_entrada_activa` |
| `historial_cobro_mecanico` | `orden_trabajo_id` FK UNIQUE · `mecanico_master_id` FK · `costo_mano_obra` · `periodo_mes` · `periodo_año` · `rendicion_id` FK nullable | `costo_mano_obra >= 0` | `idx_cobro_master` · `idx_cobro_junior` · `idx_cobro_periodo` · `idx_cobro_rendicion` |
| `rendicion_mecanico` | `mecanico_id` FK · `periodo_mes` · `periodo_año` · `total_generado` · `estado` | `estado IN (3 valores)` · `UNIQUE (mecanico_id, periodo_mes, periodo_año)` | `idx_rendicion_mecanico` · `idx_rendicion_estado` |

### 5.6 Tablas transversales — dueño `shared`

| Tabla | Campos clave | CHECK críticos | Índices |
|---|---|---|---|
| `usuario` | `email` UNIQUE (cifrado Fernet) · `password_hash` (bcrypt) · `rol` · `sub_rol` nullable · `mfa_secret` nullable (cifrado) · `mfa_habilitado` | `rol IN (6 valores)` · `sub_rol IN (6 valores o NULL)` | `idx_usuario_email` · `idx_usuario_rol` · `idx_usuario_sub_rol` |
| `usuario_perfil` | `usuario_id` FK UNIQUE · `nombres`/`apellidos` (cifrado) · `dni` nullable (cifrado) · `telefono_principal`/`secundario` (cifrado) · `consentimiento_fecha` · `eliminado_en` | — | `idx_usuario_perfil_usuario` · `idx_usuario_perfil_consentimiento` |
| `sesion` | `usuario_id` FK · `refresh_token_hash` UNIQUE · `jti` UNIQUE · `consultas_precio` · `mfa_completado` · `activa` · `expira_en` | `consultas_precio >= 0` | `idx_sesion_usuario` · `idx_sesion_jti` · `idx_sesion_refresh` · `idx_sesion_expiracion` |
| `parametros_sistema` | `clave` UNIQUE · `modulo` · `valor` · `tipo_valor` · `valor_defecto` · `modificado_por` FK nullable | `modulo IN (5 valores)` · `tipo_valor IN (4 valores)` | `idx_params_modulo` · `idx_params_clave` |
| `outbox_events` | `tipo_evento` · `modulo_origen` · `payload` JSONB · `estado` · `intentos` | `modulo_origen IN (4 valores)` · `estado IN (3 valores)` · `intentos >= 0` | `idx_outbox_pendiente (estado, created_at ASC)` · `idx_outbox_fallido` · `idx_outbox_tipo` |

### 5.7 Campos con cifrado Fernet — lista de verificación obligatoria

> El agente aplica cifrado Fernet en capa de aplicación
> — nunca en trigger ni función de PostgreSQL — sobre
> estos campos exactos. Lista cerrada, sin extrapolación.
> Fuente: `07 modelo-datos` §3.3.

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

### 5.8 Tabla de eventos_procesados — una por módulo consumidor

> Fuente: `08 contratos-interfaces` §8.2. No es una tabla
> única — cada módulo consumidor (`catalogo`, `pedidos`,
> `stock`, `taller`, `notification-service`) genera su
> propia tabla `eventos_procesados` en su esquema.

```
eventos_procesados (una instancia por módulo consumidor)  
─────────────────────────────────────────────  
evento_id UUID PK  
tipo VARCHAR(100) NOT NULL  
modulo_origen VARCHAR(20) NOT NULL  
modulo_consumidor VARCHAR(20) NOT NULL  
procesado_en TIMESTAMPTZ NOT NULL DEFAULT now()  
resultado VARCHAR(20) NOT NULL CHECK resultado IN ('EXITOSO','IGNORADO')
```
Retención: 30 días desde `procesado_en` — script de limpieza
programado, no trigger de base de datos.

---
## 6. Contratos OpenAPI — endpoints ejecutables por módulo

> Fuente: `08 contratos-interfaces` v1.0.0 §3 — 40 endpoints
> completos con request/response schema y códigos de error.
> Este tramo no reproduce los 40 endpoints con su schema
> JSON completo línea por línea — eso violaría P2 síntesis
> sin duplicación y duplicaría literalmente `08`. Aquí se
> declara el índice ejecutable de endpoints por módulo con
> método, ruta, roles y el efecto lateral crítico — suficiente
> para que el agente genere los routers de FastAPI y consulte
> `08 contratos-interfaces` §3 únicamente para el detalle
> exacto de schema al implementar cada uno.

### 6.1 Regla de generación

El agente genera un archivo de router por módulo en
`api/routes/{modulo}.py`. Cada función de endpoint usa
el código semántico de error declarado en `08` §2.5 —
nunca un mensaje de error inventado. Todo endpoint sin
excepción requiere JWT RS256 salvo los tres declarados
en §6.6 de este tramo.

### 6.2 Índice — módulo `catalogo`

| ID | Método | Ruta | Roles | Efecto lateral |
|---|---|---|---|---|
| EP-CAT-01 | GET | `/v1/repuestos` | Todos autenticados | — |
| EP-CAT-02 | GET | `/v1/repuestos/{codigo}` | Todos autenticados | — |
| EP-CAT-02-B | GET | `/v1/repuestos/{codigo}/precio` | Todos autenticados | Decrementa `consultas_precio` en `sesion` si rol `CLIENTE_*` |
| EP-CAT-03 | POST | `/v1/repuestos` | `SUPERADMIN` · `ADMINISTRADOR` | Publica `repuesto.creado` |
| EP-CAT-04 | PATCH | `/v1/repuestos/{codigo}/precio` | `SUPERADMIN` · `ADMINISTRADOR` | Publica `repuesto.precio_actualizado` |
| EP-CAT-05 | DELETE | `/v1/repuestos/{codigo}` | `SUPERADMIN` · `ADMINISTRADOR` | Publica `repuesto.dado_de_baja` — baja lógica únicamente |
| EP-CAT-06 | GET | `/v1/repuestos/{codigo}/historial-precio` | `SUPERADMIN` · `ADMINISTRADOR` | — |

**Regla de separación crítica:** EP-CAT-01 y EP-CAT-02 NUNCA
devuelven `precio_venta` bajo ninguna condición. Solo
EP-CAT-02-B expone precio. El agente que implemente esto
mal viola una decisión de seguridad explícita — referencia
`08` §3.1 regla de separación de contratos.

### 6.3 Índice — módulo `pedidos`

| ID | Método | Ruta | Roles | Efecto lateral |
|---|---|---|---|---|
| EP-PED-01 | POST | `/v1/pedidos` | Todos autenticados | Publica `pedido.confirmado` si pasa de BORRADOR a CONFIRMADO |
| EP-PED-02 | GET | `/v1/pedidos` | Internos + `CLIENTE_*` (propios) | — |
| EP-PED-03 | GET | `/v1/pedidos/{pedido_id}` | Internos + `CLIENTE_*` (propios) | — |
| EP-PED-04 | POST | `/v1/pedidos/{pedido_id}/confirmar` | Todos autenticados | Publica `pedido.confirmado` |
| EP-PED-05 | POST | `/v1/pedidos/{pedido_id}/cancelar` | Internos + `CLIENTE_*` (solo BORRADOR) | Publica `pedido.cancelado` |
| EP-PED-06 | POST | `/v1/reservas` | Todos autenticados | Publica `reserva.creada` |
| EP-PED-07 | POST | `/v1/reservas/{reserva_id}/liberar` | `SUPERADMIN` · `ADMINISTRADOR` · `VENDEDOR` | Publica `reserva.liberada` o `reserva.prioridad_taller` |
| EP-PED-08 | POST | `/v1/pedidos/{pedido_id}/proforma` | `SUPERADMIN` · `ADMINISTRADOR` · `VENDEDOR` | — |
| EP-PED-09 | POST | `/v1/pedidos/{pedido_id}/envio` | `SUPERADMIN` · `ADMINISTRADOR` · `VENDEDOR` | Pedido → `DESPACHADO` |
| EP-PED-10 | POST | `/v1/pedidos/{pedido_id}/confirmar-recepcion` | Todos autenticados | Pedido → `ENTREGADO` |
| EP-PED-11 | POST | `/v1/pedidos/{pedido_id}/incidencia` | Todos autenticados | Pedido → `INCIDENCIA` |
| EP-PED-12 | POST | `/v1/notificaciones/repuesto-disponible` | `CLIENTE_*` | — |
| EP-PED-13 | POST | `/v1/lista-reserva-progresiva` | `CLIENTE_DISTRITO` | — |
| EP-PED-14 | POST | `/v1/lista-reserva-progresiva/{lista_id}/formalizar` | `CLIENTE_DISTRITO` | Crea pedido en BORRADOR |
| EP-PED-15 | POST | `/v1/pedidos/{pedido_id}/comprobante` | `SUPERADMIN` · `ADMINISTRADOR` · `VENDEDOR` | Publica `comprobante.pendiente_validacion` si aplica |
| EP-PED-16 | POST | `/v1/comprobantes/{comprobante_id}/aprobar` | `SUPERADMIN` · `ADMINISTRADOR` | Emisión SUNAT — irreversible |
| EP-PED-17 | POST | `/v1/comprobantes/{comprobante_id}/anular` | `SUPERADMIN` · `ADMINISTRADOR` | Nota de crédito SUNAT |

### 6.4 Índice — módulo `stock`

| ID | Método | Ruta | Roles | Efecto lateral |
|---|---|---|---|---|
| EP-STK-01 | GET | `/v1/stock/{codigo}` | Internos (no `CLIENTE_*`) | — |
| EP-STK-02 | GET | `/v1/stock` | `SUPERADMIN` · `ADMINISTRADOR` · `VENDEDOR` | — |
| EP-STK-03 | GET | `/v1/stock/{codigo}/movimientos` | `SUPERADMIN` · `ADMINISTRADOR` | — |
| EP-STK-04 | POST | `/v1/stock/{codigo}/ajuste` | `SUPERADMIN` · `ADMINISTRADOR` | Registra `movimiento_stock` tipo `AJUSTE_MANUAL` |
| EP-STK-05 | PATCH | `/v1/stock/{codigo}/umbral` | `SUPERADMIN` · `ADMINISTRADOR` | — |
| EP-STK-06 | POST | `/v1/reabastecimientos` | `SUPERADMIN` · `ADMINISTRADOR` | — |
| EP-STK-07 | PATCH | `/v1/reabastecimientos/{id}/estado` | `SUPERADMIN` · `ADMINISTRADOR` | Si → `RECIBIDO`: publica `reabastecimiento.recibido` + evalúa `margen.alerta` |
| EP-STK-08 | GET | `/v1/reabastecimientos/{id}` | `SUPERADMIN` · `ADMINISTRADOR` | — |

### 6.5 Índice — módulo `taller`

| ID | Método | Ruta | Roles | Efecto lateral |
|---|---|---|---|---|
| EP-TAL-01 | POST | `/v1/ordenes-trabajo` | Internos (no `CLIENTE_*`) | Publica `orden_trabajo.abierta` |
| EP-TAL-02 | POST | `/v1/ordenes-trabajo/{id}/repuestos` | `SUPERADMIN` · `ADMINISTRADOR` · `MECANICO_MASTER` · `MECANICO_JUNIOR` | Comportamiento dual según estado — ver `08` §3.4 |
| EP-TAL-03 | POST | `/v1/ordenes-trabajo/{id}/aprobar-lista` | `SUPERADMIN` · `ADMINISTRADOR` · `VENDEDOR` · `MECANICO_MASTER` | OT → `EN_EJECUCION` · publica `orden_trabajo.lista_aprobada` |
| EP-TAL-04 | POST | `/v1/ordenes-trabajo/{id}/confirmar-adicional` | `SUPERADMIN` · `ADMINISTRADOR` · `VENDEDOR` · `MECANICO_MASTER` | — |
| EP-TAL-05 | POST | `/v1/ordenes-trabajo/{id}/autorizar-precio` | `SUPERADMIN` · `ADMINISTRADOR` · `MECANICO_MASTER` | — |
| EP-TAL-06 | POST | `/v1/ordenes-trabajo/{id}/revision-final` | `SUPERADMIN` · `ADMINISTRADOR` · `MECANICO_MASTER` | OT → `REVISION_FINAL` · publica `orden_trabajo.revision_final` |
| EP-TAL-07 | POST | `/v1/ordenes-trabajo/{id}/cobro-parcial` | `SUPERADMIN` · `ADMINISTRADOR` | Registra `deuda_activa` + 2 alertas programadas |
| EP-TAL-08 | POST | `/v1/ordenes-trabajo/{id}/cerrar` | `SUPERADMIN` · `ADMINISTRADOR` · `MECANICO_MASTER` | Requiere `cobro_confirmado: true` previo · publica `orden_trabajo.cerrada` |
| EP-TAL-09 | POST | `/v1/ordenes-trabajo/{id}/cancelar` | `SUPERADMIN` · `ADMINISTRADOR` | Publica `orden_trabajo.cancelada` |
| EP-TAL-10 | POST | `/v1/ordenes-trabajo/{id}/liberar-vehiculo` | `SUPERADMIN` · `ADMINISTRADOR` · `MECANICO_MASTER` | Requiere OT en `CERRADA` · publica `vehiculo.liberado` |
| EP-TAL-11 | GET | `/v1/taller/disponibilidad` | Todos autenticados | Response dual por rol — ver CT-08-02 |
| EP-TAL-12 | GET | `/v1/ordenes-trabajo/{id}` | Internos (alcance) + `CLIENTE_*` (propias) | — |

### 6.6 Índice — autenticación y administración

| ID | Método | Ruta | Roles | Nota crítica |
|---|---|---|---|---|
| EP-AUTH-01 | POST | `/v1/auth/login` | Público — sin token | Bloqueo 15min tras 10 intentos fallidos/IP |
| EP-AUTH-02 | POST | `/v1/auth/mfa` | Semi-público — `mfa_session_token` | Vida útil 5 minutos |
| EP-AUTH-03 | POST | `/v1/auth/refresh` | Semi-público — `refresh_token` | Replay detection — invalida familia completa |
| EP-AUTH-04 | POST | `/v1/auth/logout` | Todos autenticados | — |
| EP-AUTH-05 | GET | `/v1/health` | Público — sin token | Sin datos de negocio |
| EP-ADM-01 | GET | `/v1/admin/parametros` | `SUPERADMIN` · `ADMINISTRADOR` | — |
| EP-ADM-02 | PATCH | `/v1/admin/parametros/{clave}` | Según `modificable_por` del parámetro | Invalida caché Redis DB-1 inmediato |
| EP-ADM-03 | POST | `/v1/vehiculos` | `SUPERADMIN` · `ADMINISTRADOR` · `VENDEDOR` | `placa` y `tarjeta_propiedad` opcionales |
| EP-ADM-04 | POST | `/v1/mecanicos` | `SUPERADMIN` · `ADMINISTRADOR` | — |
| EP-ADM-05 | POST | `/v1/usuarios` | `SUPERADMIN` · `ADMINISTRADOR` | No puede crear `SUPERADMIN` por este endpoint |

### 6.7 Catálogo de códigos de error — referencia obligatoria

> El agente usa exclusivamente estos códigos semánticos.
> Lista completa en `08 contratos-interfaces` §2.5 — 18
> códigos. No se inventan códigos nuevos sin parche formal
> sobre `08`.

`AUTENTICACION_REQUERIDA` (401) · `ACCESO_DENEGADO` (403) ·
`RECURSO_NO_ENCONTRADO` (404) · `REPUESTO_NO_ENCONTRADO` (404) ·
`REPUESTO_DADO_DE_BAJA` (409) · `REPUESTO_SIN_STOCK` (409) ·
`STOCK_INSUFICIENTE` (409) · `RESERVA_EXPIRADA` (409) ·
`RESERVA_SIN_PAGO_REQUERIDO` (409) · `TRANSICION_ESTADO_INVALIDA` (409) ·
`COBRO_INSUFICIENTE` (409) · `APROBACION_REQUERIDA` (409) ·
`DISCREPANCIA_STOCK` (409) · `COMPROBANTE_YA_EMITIDO` (409) ·
`LIMITE_CONSULTAS_PRECIO` (429) · `RATE_LIMIT_EXCEDIDO` (429) ·
`VALIDACION_FALLIDA` (422) · `UMBRAL_NO_ALCANZADO` (422) ·
`ERROR_INTERNO` (500)

### 6.8 Envelope de respuesta — obligatorio en todo endpoint

```python
# Éxito
{"data": {...}, "meta": {"timestamp": "...", "request_id": "uuid"}}

# Error
{"error": {"code": "...", "message": "...", "detail": "...", "request_id": "uuid"}}
```

El agente implementa esto como un wrapper único en
`api/dependencies.py` o middleware de FastAPI — nunca
repetido manualmente en cada endpoint. Fuente: `08` §2.4.

**Nota de conteo:** la cifra de "40 endpoints" en el frontmatter
de `08 contratos-interfaces` y en `mapa-de-ejecucion.md` del
DOC-2 corresponde a una declaración base de perspectiva previa
a los parches de la sesión 0.9.1 de `08` (separación de
EP-CAT-02-B y ajustes posteriores). El conteo real y vigente
es 54 — reflejado en este tramo. Se recomienda actualizar el
frontmatter de `08` en un parche quirúrgico menor cuando Sant
lo considere oportuno — no bloquea esta construcción.

---
## 7. Contratos AsyncAPI — eventos del EDA interno

> Fuente: `08 contratos-interfaces` v1.0.0 §5 — 21 eventos
> completos con payload schema, productor y efecto en cada
> consumidor. Este tramo no reproduce los 21 payloads campo
> por campo — eso duplicaría `08` violando P2. Aquí se declara
> el índice ejecutable de eventos por módulo productor con
> tópico, consumidores y disparador — suficiente para que el
> agente configure los streams de Redis y los handlers de
> consumo, consultando `08` §5.3-5.6 únicamente para el
> payload exacto al implementar cada evento.

### 7.1 Envelope obligatorio — todo evento sin excepción

```json
{
  "evento_id": "uuid",
  "tipo": "string",
  "timestamp": "date-time",
  "modulo_origen": "enum: [catalogo, pedidos, stock, taller]",
  "version": "string · semver",
  "payload": {}
}
```

Fuente: `08` §5.2. El agente genera este envelope como
clase base reutilizable en `shared/events/envelope.py` —
nunca repetido manualmente por evento.

### 7.2 Índice — eventos del módulo `catalogo`

| Evento | Tópico | Consumidores | Disparador |
|---|---|---|---|
| `repuesto.creado` | `repuesto.creado` | `stock` (`stock-group`) | EP-CAT-03 |
| `repuesto.precio_actualizado` | `repuesto.precio_actualizado` | `pedidos` (`pedidos-group`) · `taller` (`taller-group`) | EP-CAT-04 |
| `repuesto.dado_de_baja` | `repuesto.dado_de_baja` | `pedidos` · `stock` · `taller` (sus groups) | EP-CAT-05 |

### 7.3 Índice — eventos del módulo `stock`

| Evento | Tópico | Consumidores | Disparador |
|---|---|---|---|
| `stock.agotado` | `stock.agotado` | `catalogo-group` · `pedidos-group` | `disponible` llega a 0 |
| `stock.bajo_umbral` | `stock.bajo_umbral` | `notif-group` | `disponible` cae a `umbral_minimo` |
| `stock.disponible` | `stock.disponible` | `catalogo-group` · `pedidos-group` | De 0 a disponible |
| `stock.consumo_registrado` | `stock.consumo_registrado` | `taller-group` | Descuento atómico tras `orden_trabajo.cerrada` |
| `reabastecimiento.recibido` | `reabastecimiento.recibido` | `catalogo-group` · `pedidos-group` | EP-STK-07 → `RECIBIDO` |
| `reabastecimiento.precio_actualizado` | `reabastecimiento.precio_actualizado` | `catalogo-group` | Elena actualiza precio de costo del lote |
| `margen.alerta` | `margen.alerta` | `notif-group` | Variación > `umbral_margen_alerta` |

### 7.4 Índice — eventos del módulo `pedidos`

| Evento | Tópico | Consumidores | Disparador |
|---|---|---|---|
| `reserva.creada` | `reserva.creada` | `stock-group` | EP-PED-06 |
| `reserva.liberada` | `reserva.liberada` | `stock-group` | EP-PED-07 (expiración/manual) |
| `reserva.prioridad_taller` | `reserva.prioridad_taller` | `stock-group` | EP-PED-07 (`motivo: prioridad_taller`) |
| `pedido.confirmado` | `pedido.confirmado` | `stock-group` | EP-PED-04 |
| `pedido.cancelado` | `pedido.cancelado` | `stock-group` | EP-PED-05 |
| `cobro.confirmado` | `cobro.confirmado` | `taller-group` | Cobro completo o parcial con excepción 80% |
| `comprobante.pendiente_validacion` | `comprobante.pendiente_validacion` | `notif-group` | EP-PED-15 por `VENDEDOR` |

### 7.5 Índice — eventos del módulo `taller`

| Evento | Tópico | Consumidores | Disparador |
|---|---|---|---|
| `orden_trabajo.abierta` | `orden_trabajo.abierta` | `stock-group` | EP-TAL-01 |
| `orden_trabajo.lista_aprobada` | `orden_trabajo.lista_aprobada` | `pedidos-group` | EP-TAL-03 |
| `orden_trabajo.repuesto_agregado` | `orden_trabajo.repuesto_agregado` | `stock-group` · `pedidos-group` | EP-TAL-02 en `EN_EJECUCION` |
| `orden_trabajo.revision_final` | `orden_trabajo.revision_final` | `pedidos-group` | EP-TAL-06 |
| `orden_trabajo.cerrada` | `orden_trabajo.cerrada` | `stock-group` | EP-TAL-08 |
| `orden_trabajo.cancelada` | `orden_trabajo.cancelada` | `pedidos-group` · `stock-group` | EP-TAL-09 |
| `vehiculo.liberado` | `vehiculo.liberado` | `pedidos-group` | EP-TAL-10 |

### 7.6 Tabla de consumer groups — configuración Redis ejecutable

> El agente crea exactamente estos 5 consumer groups al
> inicializar el EventBus. Ningún módulo se suscribe a un
> tópico fuera de esta tabla. Fuente: `08` §5.7 · CT-06-04.

| Consumer group | Módulo | Tópicos suscritos |
|---|---|---|
| `catalogo-group` | `catalogo` | `stock.agotado` · `stock.disponible` · `reabastecimiento.recibido` · `reabastecimiento.precio_actualizado` |
| `pedidos-group` | `pedidos` | `stock.disponible` · `reabastecimiento.recibido` · `reserva.creada` · `orden_trabajo.lista_aprobada` · `orden_trabajo.repuesto_agregado` · `orden_trabajo.revision_final` · `orden_trabajo.cancelada` · `vehiculo.liberado` |
| `stock-group` | `stock` | `reserva.creada` · `reserva.liberada` · `reserva.prioridad_taller` · `pedido.confirmado` · `pedido.cancelado` · `orden_trabajo.cerrada` · `orden_trabajo.cancelada` · `repuesto.creado` · `repuesto.dado_de_baja` |
| `taller-group` | `taller` | `cobro.confirmado` · `stock.consumo_registrado` |
| `notif-group` | `notification-service` | `margen.alerta` · `stock.bajo_umbral` · `comprobante.pendiente_validacion` |

**Nota de carga:** `pedidos-group` suscribe 8 tópicos — la
mayor superficie de integración del sistema. Referencia
CT-08-01 — requiere prueba de integración específica que
verifique que cada tópico activa exactamente su handler
declarado, sin interferencia cruzada.

### 7.7 Idempotencia de consumidores — mecanismo obligatorio

> Todo consumidor implementa esto sin excepción antes de
> ejecutar lógica de negocio. Fuente: `08` §8.2 · CT-07-05.

```
1. Consumidor recibe mensaje del stream.
2. Verifica evento_id en su tabla eventos_procesados  
    (declarada en tramo 3 §5.8 de este documento).
3. Si existe → ACK sin ejecutar lógica → resultado: IGNORADO.
4. Si no existe → ejecuta lógica de negocio + inserta  
    evento_id en eventos_procesados en la misma transacción.
5. ACK solo tras transacción confirmada.
6. Si falla → no hace ACK → Redis Streams reentrega.
```
Retención de `eventos_procesados`: 30 días.

### 7.8 Garantías de entrega — resumen ejecutable

| Garantía | Mecanismo | Configuración |
|---|---|---|
| At-least-once | ACK explícito por consumer | Solo tras procesamiento exitoso |
| Idempotencia | Verificación `evento_id` — §7.7 | Obligatoria en todo consumidor |
| Reintentos | Cola Redis DB-2 | `reintentos_notificacion: 3` · `intervalo_reintento_notif_min: 10` |
| Dead letter | Sin ACK tras 3 reintentos | Notifica a `ADMINISTRADOR` |
| Orden | Garantizado por tópico | No asumir orden entre tópicos distintos |

Fuente: `08` §5.8.

**Nota de conteo:** la cifra de "21 eventos" en el frontmatter
de `08 contratos-interfaces`, en `mapa-de-ejecucion.md` del
DOC-2 y en las fuentes de `09 especificaciones-tecnicas`
corresponde al contexto base declarado antes de que el
desarrollo tramo a tramo de `08` añadiera eventos como parte
de su flujo natural de construcción — no como parche posterior
a un cierre. El conteo real y vigente es 24, reflejado en
§7.2 a §7.5 de este documento. Se recomienda actualizar la
cifra en el frontmatter de `08` y en el mapa de ejecución en
una próxima revisión menor — no bloquea esta construcción.

---
## 8. Puertos internos — comunicación síncrona entre módulos

> Fuente: `08 contratos-interfaces` v1.0.0 §4 — puertos
> hexagonales con sus operaciones. El agente implementa
> cada puerto como `Protocol` en `domain/ports/` del módulo
> que lo consume — referencia ISP en `09 especificaciones-tecnicas`
> §3.2. La implementación concreta vive en el módulo que
> lo provee, expuesta vía `infrastructure/factories.py`.

### 8.1 Regla de generación

Ningún módulo importa directamente código de otro módulo.
Toda llamada síncrona entre módulos pasa por un `Protocol`
declarado aquí. El agente cablea la implementación en
`api/dependencies.py` o `infrastructure/factories.py` —
nunca con import directo cruzado entre `domain/` de
módulos distintos.

### 8.2 Índice de puertos — operación, dirección, excepciones

| Puerto | Operación | Llama | Implementa | Excepciones de dominio |
|---|---|---|---|---|
| `CatalogoPedidosPort` | `obtener_precio_vigente(codigo)` · `verificar_existencia(codigo)` | `pedidos` | `catalogo` | `RepuestoNoEncontradoException` · `RepuestoDadoDeBajaException` |
| `CatalogoTallerPort` | `obtener_precio_para_ot(codigo)` | `taller` | `catalogo` | `RepuestoNoEncontradoException` · `RepuestoDadoDeBajaException` |
| `StockPedidosPort` | `verificar_disponibilidad(codigo, cantidad)` · `verificar_lista(items)` | `pedidos` | `stock` | `RepuestoNoEncontradoException` · `StockInsuficienteException` |
| `StockTallerPort` | `verificar_disponibilidad_ot(items)` · `consultar_apartado(codigo)` | `taller` | `stock` | `RepuestoNoEncontradoException` |
| `TallerPedidosPort` | `verificar_cobro_confirmado(orden_trabajo_id)` | `taller` | `pedidos` | `OrdenTrabajoNoEncontradaException` |
| `ParametrosSistemaPort` | `obtener_parametro(clave)` | Todos los módulos | Servicio transversal `shared` | `ParametroNoEncontradoException` |

### 8.3 Regla de dependencia unidireccional — verificación automática
```
atalogo → no llama síncronamente a ningún otro módulo  
stock → no llama síncronamente a ningún otro módulo —  
publica eventos y responde consultas  
pedidos → llama a catalogo · stock  
taller → llama a catalogo · stock · pedidos
```
Dependencias circulares síncronas están prohibidas —
`scripts/check_dip.py` verifica esto junto con la regla
de DIP en cada ejecución de pipeline. Fuente: `08` §4.8.

### 8.4 `ParametrosSistemaPort` — regla de caché obligatoria
```
1. Buscar primero en Redis DB-1 con clave = clave del parámetro.
2. Si está en caché → devolver con desde_cache: true.
3. Si no está → consultar parametros_sistema en PostgreSQL.
4. Almacenar en Redis con TTL = ttl_cache_parametros_segundos  
    (parámetro propio, valor inicial 300 segundos).
5. Al actualizar vía EP-ADM-02 → invalidar la entrada en  
    Redis inmediatamente, sin esperar expiración de TTL.
```
Fuente: `08` §4.7 · CT-06-08.

---

## 9. notification-service — adaptador de salida hexagonal

> Fuente: `08 contratos-interfaces` §6. No es un microservicio
> independiente — es un proceso interno del `api-server` que
> implementa `NotificacionPort`.

### 9.1 Puerto y operación

| Campo | Valor |
|---|---|
| Puerto | `NotificacionPort` |
| Operación | `enviar_notificacion(comando: ComandoNotificacion) → ResultadoNotificacion` |
| Implementado por | `WhatsAppAdapter` (primario) · `SMSAdapter` (fallback) |
| Ubicación | `infrastructure/notifications/` |

### 9.2 Regla de fallback — ejecutable
```
1. Intentar canal_preferido (default: whatsapp).
2. Si falla por timeout o error 4xx/5xx → reintentar  
    automáticamente con SMS sin intervención manual.
3. Registrar fallback_activado: true en el log.
4. Si ambos canales fallan → encolar en Redis DB-2.
5. Reintentar hasta reintentos_notificacion veces  
    (parámetro, valor inicial 3) en intervalos de  
    intervalo_reintento_notif_min minutos (valor inicial 10).
6. Si todos los reintentos fallan → publicar alerta  
    hacia ADMINISTRADOR — tipo NOTIFICACION_FALLIDA.
```
**Regla de segmento rural:** para destinatarios con
`segmento: rural` el servicio activa SMS fallback con
umbral de tiempo reducido — no espera el timeout estándar
de WhatsApp. Fuente: `08` §6.2.

### 9.3 Timeouts por adaptador

| Adaptador | Timeout por intento |
|---|---|
| WhatsApp Business API | 10 segundos |
| SMS — Twilio/AWS SNS | 15 segundos |

### 9.4 Tipos de notificación — lista cerrada

> 15 tipos declarados en `08` §6.2. El agente no inventa
> tipos nuevos sin parche formal. Lista completa: ver
> `08 contratos-interfaces` §6.2 — tabla con evento origen,
> destinatario, canal primario y payload mínimo por tipo.

---

## 10. Rate limiting — política ejecutable por grupo

> Fuente: `08` §7. Middleware evaluado antes de lógica de
> negocio. Clave de identificación: `IP + usuario_id` para
> autenticados · `IP` para endpoints públicos.

| Grupo | Endpoints | Límite | Ventana | Scope |
|---|---|---|---|---|
| Autenticación | EP-AUTH-01 · EP-AUTH-02 | 10 req | 1 min | Por IP |
| Refresh token | EP-AUTH-03 | 20 req | 1 hora | Por IP + usuario |
| Consulta precio | EP-CAT-02-B | `max_consultas_precio_sesion` (default 3) | Por día — reset 05:00 UTC | Por usuario_id · solo `CLIENTE_*` |
| Catálogo lectura | EP-CAT-01 · EP-CAT-02 | 120 req | 1 min | Por IP + usuario |
| Escritura catálogo | EP-CAT-03/04/05 | 30 req | 1 min | Por usuario_id |
| Pedidos lectura | EP-PED-02 · EP-PED-03 | 60 req | 1 min | Por usuario_id |
| Pedidos escritura | EP-PED-01/04/05 | 20 req | 1 min | Por usuario_id |
| Reservas | EP-PED-06 · EP-PED-07 | 10 req | 1 min | Por usuario_id |
| Stock lectura | EP-STK-01/02/03/08 | 60 req | 1 min | Por usuario_id |
| Stock escritura | EP-STK-04/05/06/07 | 20 req | 1 min | Por usuario_id |
| Taller lectura | EP-TAL-11 · EP-TAL-12 | 60 req | 1 min | Por usuario_id |
| Taller escritura | EP-TAL-01 a 10 | 20 req | 1 min | Por usuario_id |
| Comprobantes | EP-PED-15/16/17 | 10 req | 1 min | Por usuario_id |
| Administración | EP-ADM-01 a 05 | 30 req | 1 min | Por usuario_id |
| Health check | EP-AUTH-05 | 60 req | 1 min | Por IP |

**Regla crítica de consulta de precio:** el límite NO produce
HTTP 429 — produce omisión del campo `precio_venta` con flag
`precio_limite_alcanzado: true`. Es comportamiento de negocio,
no error de infraestructura. Fuente: `08` §7.2.

**Headers obligatorios en toda respuesta con rate limiting:**
`X-RateLimit-Limit` · `X-RateLimit-Remaining` · `X-RateLimit-Reset` ·
`Retry-After` (solo en 429).

---

## 11. Transactional Outbox e idempotencia — contrato de proceso

> Fuente: `08` §8 · `07 modelo-datos` §7. Complementa la
> tabla `outbox_events` ya declarada en tramo 3 §5.6.

### 11.1 Worker outbox — contrato ejecutable

| Campo | Valor |
|---|---|
| Tipo | Proceso interno del `api-server` — no servicio separado |
| Mecanismo | Polling sobre `outbox_events` con `estado: PENDIENTE` |
| Query | `SELECT ... WHERE estado='PENDIENTE' ORDER BY created_at ASC LIMIT 50 FOR UPDATE SKIP LOCKED` |
| Intervalo | Configurable — valor inicial 5 segundos |
| Límite de intentos | 3 — tras eso `estado: FALLIDO` + alerta a `SUPERADMIN` |
| Concurrencia | Una sola instancia del worker por módulo |

### 11.2 Flujo ejecutable
```
1. Módulo inserta en outbox_events en la misma transacción  
    que el cambio de negocio.
2. Si la transacción falla → ni el dato ni el evento existen.
3. Si confirma → registro en PENDIENTE.
4. Worker publica en Redis Streams → marca PUBLICADO.
5. Si Redis falla al publicar → permanece en PENDIENTE →  
    reintento en el siguiente ciclo de polling.
```
### 11.3 Eventos que usan Outbox obligatoriamente

`cobro.confirmado` · `orden_trabajo.cerrada` · `reserva.creada` ·
`reserva.liberada` · `reabastecimiento.recibido` ·
`comprobante.pendiente_validacion`

Fuente: `07 modelo-datos` §7 — estos seis eventos no pueden
perderse sin generar inconsistencia de negocio crítica.

### 11.4 Idempotencia de endpoints HTTP — `Idempotency-Key`

| Campo | Valor |
|---|---|
| Header | `Idempotency-Key: {uuid v4}` |
| Obligatorio | No — opcional |
| Recomendado en | EP-PED-01 · EP-PED-04 · EP-PED-06 · EP-TAL-01 · EP-TAL-08 |
| Comportamiento | Request repetida con mismo key → devuelve response original sin reejecutar |
| Retención | 24 horas desde primera ejecución |
| Scope | Por `usuario_id` |

Fuente: `08` §8.3 — caso de uso principal: cliente S4 con
conectividad intermitente que reenvía la misma request.

### 11.5 Ventana de consistencia eventual — valores de referencia

| Escenario | Ventana esperada | Ventana máxima |
|---|---|---|
| Operación normal | < 100ms | 500ms |
| Carga moderada (≤10 req concurrentes) | < 500ms | 2 segundos |
| Reintento tras fallo de consumidor | < 30 segundos | 2 minutos |
| Reintento tras fallo de worker outbox | < 10 segundos | 1 minuto |

El sistema opera con consistencia eventual declarada — no
bloquea la operación esperando consistencia inmediata.
Fuente: `08` §8.4 · RNF-28.

---
## 12. Criterios de verificación del archivo completo

> Verificación contra el criterio de cierre declarado en
> `DOC-3/mapa-de-ejecucion.md` para `03-diseno-sistema`:
> "El agente puede levantar el entorno de desarrollo y
> verificar que los contratos están presentes sin consultar
> el DOC-2."

### 12.1 Checklist de verificación ejecutable
```
□ Repositorio clonado · estructura de directorios de §2.2  
y §2.3 generada exactamente  
□ Las 28 tablas de §5 migradas en PostgreSQL vía Alembic  
sin error  
□ Seed nivel mínimo cargado — 1 SUPERADMIN · 5 repuestos  
□ api-server arranca con `uvicorn` sin error de import  
□ GET /v1/health responde 200 con estado: ok  
□ GET /v1/repuestos?universo=mototaxi con token de test  
responde 200 con array de 5 repuestos  
□ Los 6 puertos internos de §8.2 existen como Protocol  
en domain/ports/ de su módulo correspondiente  
□ scripts/check_dip.py ejecuta sin hallazgos — ningún  
domain/ importa infrastructure/ ni otro módulo  
□ Los 5 consumer groups de §7.6 están registrados en  
Redis Streams al arrancar el EventBus  
□ outbox_events y eventos_procesados (por módulo) existen  
como tablas migradas  
□ El envelope de respuesta {data, meta} / {error} está  
implementado como wrapper único, no repetido por endpoint
```
### 12.2 Criterio de no dependencia hacia el DOC-2

El agente que complete el checklist de §12.1 no necesitó
abrir `06`, `07` ni `08` del DOC-2 — toda la información
estructural, de stack, de esquema y de contratos necesaria
para esa tarea está sintetizada en los tramos 1 a 6 de este
archivo. Las únicas excepciones documentadas son: el schema
JSON completo de un endpoint específico al implementarlo
(§6.1) y el payload completo de un evento específico (§7.1)
— ambos por diseño, para evitar duplicación según P2.

---

## 13. Observaciones activas — heredadas y generadas en esta construcción

### 13.1 Observaciones heredadas de `02-definicion-funcional` — estado de resolución

> Estas 5 observaciones fueron declaradas en el prompt de
> inicialización de esta sesión como pendientes de impacto
> en `03-diseno-sistema`. Se verifica su resolución contra
> el contenido real de `06`, `07` y `08` recibido.

| ID | Observación original | Resuelta en `07`/`08` | Estado |
|---|---|---|---|
| OBS-001 | Contador de consultas de precio por sesión requiere campo en modelo de sesión | `sesion.consultas_precio` — §5.6 de este documento | ✅ Resuelta |
| OBS-002 | Lista de reserva progresiva de S2 requiere tabla propia | `lista_reserva_progresiva` + `lista_reserva_progresiva_item` — §5.4 | ✅ Resuelta |
| OBS-003 | Autorización de visibilidad de precio requiere campo en orden_trabajo | `orden_trabajo.visibilidad_precio_cliente` + `visibilidad_otorgada_por` — §5.5 | ✅ Resuelta |
| OBS-004 | precio_ajustado por ítem requiere campo en pedido de S2 | `pedido.precio_ajustado` + `pedido_item.precio_ajustado_unit` — §5.4 | ✅ Resuelta |
| OBS-005 | Cola de reintentos para notificaciones de S4 requiere mecanismo en contratos | Redis DB-2 + `reintentos_notificacion` — §9.2 de este documento | ✅ Resuelta |

**Resultado: 5 de 5 observaciones heredadas resueltas. ✅**

### 13.2 Observaciones de conteo generadas en esta construcción

| ID | Observación | Naturaleza | Acción recomendada |
|---|---|---|---|
| OBS-DS-001 | Frontmatter de `08 contratos-interfaces` declara "40 endpoints" — conteo real verificado en este documento es 54, por parche posterior a la declaración base (split EP-CAT-02-B y ajustes 0.9.1) | Metadato desactualizado | Parche quirúrgico menor sobre frontmatter de `08` — no bloqueante |
| OBS-DS-002 | Frontmatter de `08 contratos-interfaces`, `mapa-de-ejecucion.md` del DOC-2 y fuentes de `09 especificaciones-tecnicas` declaran "21 eventos" — conteo real verificado es 24, por evolución natural durante construcción tramo a tramo de `08` antes de su cierre | Metadato desactualizado | Actualizar cifra en frontmatter de `08` y referencias cruzadas en próxima revisión — no bloqueante |

### 13.3 Observación de dependencia externa — identidad visual

| ID | Observación | Sección de impacto | Estado |
|---|---|---|---|
| OBS-DS-003 | Tailwind CSS se instala con configuración por defecto en §3.3 de este documento — paleta, tipografía y tokens de marca no están definidos. El sistema de identidad visual está en evaluación en sesión separada, pendiente de validación por Elena y Samuel | Construcción futura de componentes de frontend — fuera del alcance de `03-diseno-sistema` | 🔵 Abierta — no bloquea este documento |

---

## 14. Fuentes

| Documento | Versión | Secciones consultadas |
|---|---|---|
| `06 arquitectura-sistema` | v1.0.0 + parche ADR-004 | §2 ADR-001 · §6 stack · §7 puertos · §8 EventBus |
| `07 modelo-datos` | v1.0.0 | §1 principios · §2 entidades por módulo · §3 diccionario · §4 índices · §7 outbox |
| `08 contratos-interfaces` | v1.0.0 | §2 convenciones · §3 OpenAPI · §4 puertos internos · §5 AsyncAPI · §6 notification-service · §7 rate limiting · §8 idempotencia y outbox |
| `09 especificaciones-tecnicas` | v1.0.0 | §3.2 DIP · §3.3 estructura de carpetas |
| `02-definicion-funcional` (DOC-3) | v0.1.0 | §8 observaciones activas — verificación de resolución |

---

## 15. Historial de versiones

| Versión | Fecha   | Cambio                                                                                                                                                                                                                              | Impacto                                                                                                                                                                                                                                            |
| ------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0.1.0   | 2026-06 | Tramo 1 — frontmatter · propósito · estructura de módulos                                                                                                                                                                           | Base estructural establecida                                                                                                                                                                                                                       |
| 0.2.0   | 2026-06 | Tramo 2 — stack con versiones exactas · comandos de setup                                                                                                                                                                           | Entorno reproducible desde cero                                                                                                                                                                                                                    |
| 0.3.0   | 2026-06 | Tramo 3 — esquema de datos ejecutable · 28 tablas indexadas                                                                                                                                                                         | Modelo de datos sintetizado sin duplicar `07`                                                                                                                                                                                                      |
| 0.4.0   | 2026-06 | Tramo 4 — contratos OpenAPI · 54 endpoints indexados · OBS-DS-001 registrada                                                                                                                                                        | Superficie HTTP completa · discrepancia de conteo documentada                                                                                                                                                                                      |
| 0.5.0   | 2026-06 | Tramo 5 — contratos AsyncAPI · 24 eventos · 5 consumer groups · OBS-DS-002 registrada                                                                                                                                               | EDA interno completo · discrepancia de conteo documentada                                                                                                                                                                                          |
| 0.6.0   | 2026-06 | Tramo 6 — puertos internos · notification-service · rate limiting · outbox e idempotencia                                                                                                                                           | Comunicación síncrona y asíncrona entre módulos cerrada sin discrepancias                                                                                                                                                                          |
| 0.9.0   | 2026-06 | Tramo 7 — criterios de verificación · observaciones activas · fuentes · historial                                                                                                                                                   | Documento completo — pendiente cierre formal                                                                                                                                                                                                       |
| 1.0.0   | 2026-06 | Tramo de cierre formal — confirmación de Sant como validador. Historial interno sincronizado con frontmatter (previamente reflejaba 0.9.0)                                                                                          | Documento cerrado y aprobado — listo para verificación cruzada global                                                                                                                                                                              |
| 1.0.1   | 2026-06 | PCT-CIERRE-008 — añadida §3.3.1 Identidad visual (tokens de color SANTI, sistema tipográfico Quicksand/Nunito Sans/Fira Code, regla de aplicación por superficie). Resuelve OBS-DS-003 — bloqueo de configuración Tailwind retirado | Cierra observación abierta desde sesión anterior. Habilita construcción real de componentes de frontend con tema definido. Aclaración de alcance: "SANTI" es nombre de marca/presentación únicamente — no afecta nomenclatura de dominio del DOC-3 |

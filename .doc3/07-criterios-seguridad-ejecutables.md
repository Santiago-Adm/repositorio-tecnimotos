---
version: 1.0.1
estado: cerrado
archivo: "07"
titulo: Criterios de seguridad ejecutables
autor: Sant
fecha: 2026-06
validador: Sant
aprobado: true
fuente_doc2_unica: "10 seguridad-formal v1.0.0"
tramo_actual: 6 de 6 — cierre · observaciones · fuentes · historial
alimenta: ["09-criterios-avance-automatico"]
cambio: "PCT-CONSTRUCCION-003 — conteo de endpoints actualizado de 54 a 55 tras formalización de EP-CAT-07 en 03 §6.2"
impacto: "55/55 endpoints con riesgo OWASP asignado — inventario actualizado"
---

# 07 — Criterios de seguridad ejecutables
## Tecnimotos Santi · DOC-3 — Protocolo de construcción

> Este archivo responde al agente: ¿qué controles de
> seguridad debo implementar y cómo verifico que están
> activos?
> Fuente única: `10 seguridad-formal` v1.0.0.
> El agente consulta este archivo antes de mergear
> cualquier endpoint nuevo. Para el índice completo de
> endpoints y eventos, este archivo referencia
> `03-diseno-sistema` §6 y §7 — no los repite aquí.

---

## 1. Propósito

Este archivo instruye al agente sobre los controles de
seguridad obligatorios del sistema y el mecanismo exacto
para verificar que cada control está activo antes de
considerar terminado un módulo o un endpoint.

El agente que lee este archivo puede:
emitir y verificar JWT RS256 con los parámetros exactos ·
exigir MFA en los roles que lo requieren · verificar que
un endpoint nuevo cumple los 10 controles OWASP API Top 10
sin abrir el DOC-2 · aplicar la matriz RBAC + ABAC sin
ambigüedad · rotar y validar secretos · ejecutar el proceso
de derecho al olvido bajo Ley 29733 · escribir audit trail
con los campos exigidos por categoría.

Este archivo no explica por qué se eligió cada control
— esa justificación vive en `10 seguridad-formal` del
DOC-2. Este archivo dice qué verificar, con qué umbral
exacto y qué hacer si el umbral no se cumple.
Referencia: Principio 4 — lenguaje ejecutable.

**Regla de precedencia:** ante cualquier ambigüedad entre
este archivo y `10 seguridad-formal`, `10` es la fuente
de verdad. Este archivo se actualiza para reflejarla —
nunca al revés.

---

## 2. Autenticación ejecutable — JWT RS256 + MFA

> Fuente: `10 seguridad-formal` §2.1 a §2.5.
> Verificación: el agente puede confirmar que una sesión
> cumple los parámetros de este tramo sin consultar `10`.

### 2.1 Parámetros de token — valores exactos
```
ALGORITMO: RS256  
ACCESS_TOKEN_TTL: 15 minutos  
REFRESH_TOKEN_TTL: 7 días  
ROTACION_REFRESH: en cada uso — sin excepción  
HASH_PASSWORD: Argon2id + pepper (ARGON2_PEPPER)  
CAMPO_REVOCACION: usuario.token_version (entero)
```
**Verificación ejecutable:** el agente inspecciona el
payload de un JWT emitido por el sistema y confirma:
header declara `alg: RS256` · claim `exp` - claim `iat`
== 900 segundos para access token · existe claim
`token_version` que coincide con `usuario.token_version`
en base de datos en el momento de verificación.

Si cualquiera de estas tres condiciones falla →
criterio de autenticación fallido → no se permite merge.

### 2.2 Almacenamiento por superficie — regla de verificación

| Superficie | El agente verifica que... |
|---|---|
| Navegador web | El access token NUNCA aparece en `localStorage` ni `sessionStorage` — solo en memoria JS. El refresh token solo existe como cookie con flags `HttpOnly` + `Secure` + `SameSite=Strict` simultáneos |
| Android — PWA (MVP) | El access token se descarta al cerrar la PWA — sin persistencia. Cookie `HttpOnly` en WebView para el refresh token |
| Servidor | La tabla `sesion` almacena `refresh_token_hash` — nunca el token en claro. Campo `estado` solo acepta `ACTIVA` o `REVOCADA` |

**Test obligatorio:** grep sobre el código frontend
buscando `localStorage.setItem` o `sessionStorage.setItem`
con clave que contenga `token` — cualquier coincidencia
es criterio de fallo.

### 2.3 Revocación de refresh token — tres escenarios sin excepción
```
ESCENARIO 1 — Logout explícito (EP-AUTH-04)  
→ sesion.estado = REVOCADA  
→ cookie eliminada en response

ESCENARIO 2 — Replay detection (EP-AUTH-03)  
→ refresh token ya usado detectado  
→ invalida TODA la familia de tokens de la sesión  
→ notifica al usuario  
→ registra evento en audit trail — categoría Seguridad (ver §7 de este archivo)

ESCENARIO 3 — Revocación masiva por SUPERADMIN  
→ incrementa usuario.token_version  
→ todo token con version anterior queda inválido  
de inmediato, sin esperar su expiración natural
```
**Verificación ejecutable:** test de integración que
reutiliza un refresh token ya consumido y confirma que
TODOS los tokens de esa sesión —no solo el reutilizado—
quedan inválidos en la siguiente verificación.

### 2.4 MFA — obligatoriedad por rol

| Rol | MFA en MVP | Si falta — consecuencia |
|---|---|---|
| `SUPERADMIN` | Obligatorio — sin excepción | `access_token` NUNCA se emite sin MFA completado |
| `ADMINISTRADOR` | Obligatorio — sin excepción | Idéntico al anterior |
| `VENDEDOR` | Opcional en MVP | — |
| `MECANICO_MASTER` | Opcional en MVP | — |
| `MECANICO_JUNIOR` | Opcional en MVP | — |
| `CLIENTE_*` (los 6 sub-roles) | Opcional | — |

**Flujo ejecutable:**
```
1. POST EP-AUTH-01 con credenciales válidas  
    → emite mfa_session_token (TTL 5 minutos)
2. POST EP-AUTH-02 con código TOTP (patrón ^[0-9]{6}$)  
    → si correcto: emite access_token + refresh_token  
    → si transcurren 5 minutos sin completar paso 2:  
    mfa_session_token se invalida → reiniciar desde paso 1
```
**Verificación ejecutable:** el agente ejecuta una consulta
sobre el audit trail de autenticación (§7) y confirma que
el 100% de las sesiones activas de `SUPERADMIN` y
`ADMINISTRADOR` tienen `mfa_completado: true` registrado.
Un solo registro con `mfa_completado: false` para estos
dos roles es criterio de fallo — sin tolerancia.

### 2.5 Protección contra ataques — umbrales ejecutables

| Ataque | Umbral exacto | Acción automática |
|---|---|---|
| Fuerza bruta login | 10 intentos fallidos / minuto / IP | Bloqueo 15 min + alerta a Sant |
| Enumeración de usuarios | — | Mensaje de error idéntico para email inválido y password inválido — nunca distinguir cuál falló |
| Replay refresh token | 1 reuso detectado | Invalida familia completa — ver §2.3 Escenario 2 |
| Fuerza bruta MFA | 5 intentos fallidos / `mfa_session_token` | Invalida ese `mfa_session_token` — reiniciar desde EP-AUTH-01 |
| Session fixation | — | Login exitoso siempre emite access_token y refresh_token nuevos — invalida los anteriores sin excepción |
| Token forjado | Firma RS256 inválida | HTTP 401 `AUTENTICACION_REQUERIDA` — rechazo inmediato sin procesar el resto del request |

**Nota de umbral vigente:** el umbral correcto es 10
intentos/minuto — no 5. Esto fue una decisión explícita
adoptada en `08 contratos-interfaces` EP-AUTH-01 sobre
un valor más conservador del arsenal de referencia. El
agente usa 10, no 5, bajo ninguna condición.

**Verificación ejecutable:** suite de pruebas de seguridad
con: test de 11 intentos fallidos consecutivos → confirma
bloqueo en el intento 11 · test de mensaje de error
idéntico ante email inexistente vs password incorrecto ·
test de reuso de refresh token → confirma invalidación de
familia completa · test de 6 intentos MFA fallidos →
confirma invalidación del `mfa_session_token` en el
intento 6.

### 2.6 Proveedor de identidad — regla de fase
```
FASE MVP: self-hosted — JWT emitido por el api-server  
sin dependencia de servicio externo  
FASE 2+: Keycloak self-hosted — solo si se necesita  
SSO entre múltiples clientes (web/móvil/admin)
```
El agente implementa la autenticación como adaptador
reemplazable (ADR-001 Hexagonal) — migrar de self-hosted
a Keycloak no debe requerir modificar el dominio, solo
reemplazar el adaptador de autenticación.

---
## 3. Autorización ejecutable — RBAC + ABAC

> Fuente: `10 seguridad-formal` §3.1 a §3.4.
> El agente no reproduce aquí la matriz completa de
> permisos por endpoint — esa matriz vive en `10` §3.2
> y referencia los 55 endpoints indexados en
> `03-diseno-sistema` §6.2 a §6.6. Aquí se declara el
> patrón de verificación y el contenido que sí es nuevo
> para este archivo: las 10 políticas ABAC como
> condiciones ejecutables con su consecuencia exacta.

---

### 3.1 Roles del sistema — lista cerrada
```
ROLES_INTERNOS:  
SUPERADMIN — control total · Sant  
ADMINISTRADOR — stock·precios·pedidos·comprobantes·reportes · Elena  
VENDEDOR — catálogo(lectura)·pedidos(crear/ver)·stock(ver)  
MECANICO_MASTER — órdenes de trabajo(todas)·autoriza precio al cliente  
MECANICO_JUNIOR — órdenes asignadas·sin autorización de precio

SUB_ROLES_CLIENTE:  
CLIENTE_CONDUCTOR — S1 — activo  
CLIENTE_DISTRITO — S2 — activo  
CLIENTE_RURAL — S4 — activo  
CLIENTE_FLOTA_DUENO — S3 — rol existe, sin HU activas en MVP  
CLIENTE_FLOTA_CONDUCTOR — S3 — rol existe, sin HU activas en MVP  
CLIENTE_MOTOLINEAL — S5 — rol existe, sin HU activas en MVP
```
**Regla de extensión:** el agente no crea un rol o
sub-rol nuevo sin parche formal sobre `10 seguridad-formal`.
Esta lista es cerrada — 5 roles internos + 6 sub-roles
de cliente = 11 valores válidos para el campo `rol`/`sub_rol`.

### 3.2 Verificación RBAC — patrón obligatorio, no matriz repetida

El agente NO reproduce aquí la tabla de permisos por
endpoint — consulta `10 seguridad-formal` §3.2 para el
detalle exacto de qué rol accede a qué operación de los
55 endpoints declarados en `03-diseno-sistema` §6.

Lo que sí declara este archivo es el **patrón de
verificación** que aplica a los 55 endpoints sin
excepción:
```
PARA CADA endpoint nuevo o modificado:

1. Identificar los roles autorizados según la matriz  
    vigente de `10` §3.2.
2. Generar un test parametrizado con token de CADA  
    rol del sistema (los 5 internos + CLIENTE_* genérico).
3. Confirmar: rol autorizado → 200/201 según operación.
4. Confirmar: rol NO autorizado → 403 ACCESO_DENEGADO  
    ANTES de ejecutar cualquier lógica de negocio.
5. La verificación de rol ocurre en middleware —  
    nunca dentro del use case.
```
**Criterio de fallo:** un endpoint que ejecuta lógica
de negocio (consulta a base de datos, efecto lateral)
antes de confirmar el rol es un fallo de arquitectura
de seguridad — no solo de autorización. Bloquea merge.

### 3.3 ABAC — las 10 políticas ejecutables

> Regla de implementación vinculante: RBAC se verifica
> en middleware. ABAC se verifica en el use case. Nunca
> al revés — un endpoint que verifica ABAC en el router
> o middleware viola esta regla sin excepción.

```
ABAC-01 — recurso: pedido  
CLIENTE_*: sujeto.usuario_id == recurso.cliente_id  
Fallo → RECURSO_NO_ENCONTRADO (404) — nunca 403  
Endpoints: EP-PED-02 · EP-PED-03 · EP-PED-05

ABAC-02 — recurso: reserva  
CLIENTE_*: sujeto.usuario_id == recurso.cliente_id  
Fallo → RECURSO_NO_ENCONTRADO (404)  
Endpoint: EP-PED-06

ABAC-03 — recurso: orden_trabajo  
MECANICO_JUNIOR: sujeto.mecanico_id == recurso.mecanico_id  
Fallo → RECURSO_NO_ENCONTRADO (404)  
Endpoint: EP-TAL-12

ABAC-04 — recurso: orden_trabajo  
CLIENTE_*: sujeto.usuario_id == recurso.cliente_id  
Fallo → RECURSO_NO_ENCONTRADO (404)  
Endpoint: EP-TAL-12

ABAC-05 — recurso: precio_venta  
CLIENTE_*: sesion.consultas_precio_restantes > 0  
Fallo → omite campo precio_venta + flag  
precio_limite_alcanzado: true  
(NO es 429 — es comportamiento de negocio,  
ver §4 Tramo 3 de este archivo, API4)  
Endpoint: EP-CAT-02-B

ABAC-06 — recurso: comprobante  
  VENDEDOR: SIEMPRE genera el comprobante en estado
    PENDIENTE_VALIDACION — sin excepción, independiente
    de requiere_validacion_admin.
  ADMINISTRADOR / SUPERADMIN: generan directo en EMITIDO,
    EXCEPTO si requiere_validacion_admin: true en el
    request body — en ese caso también caen a
    PENDIENTE_VALIDACION.
  Campo motivo_validacion (string, maxLength 200):
    obligatorio si requiere_validacion_admin: true.
    Ausente en ese caso → VALIDACION_FALLIDA (422).
  Reglas de umbral previas e independientes (verificar
    ANTES de evaluar este ABAC):
    boleta + monto ≤ S/20 → exige solicitud_cliente: true
      o falla con VALIDACION_FALLIDA / UMBRAL_NO_ALCANZADO
    factura → exige monto > S/60 Y ruc_cliente presente
  Efecto lateral si resultado es PENDIENTE_VALIDACION:
    publica comprobante.pendiente_validacion
  Endpoint: EP-PED-15

ABAC-07 — recurso: parametro_sistema  
ADMINISTRADOR: solo modifica si  
parametro.modificable_por == ADMINISTRADOR  
Fallo → ACCESO_DENEGADO (403) — aquí SÍ se confirma  
la existencia del recurso, es un parámetro  
del sistema, no un dato personal de terceros  
Endpoint: EP-ADM-02

ABAC-08 — campo: precio_costo_unitario  
Visible SOLO para: SUPERADMIN · ADMINISTRADOR  
Para todos los demás roles: campo OMITIDO en  
serialización del servidor — nunca filtrado en cliente  
Endpoints: EP-STK-06 · EP-STK-08 · EP-CAT-06

ABAC-09 — campo: monto_con_descuento  
Visible SOLO para: SUPERADMIN · ADMINISTRADOR  
Omitido para: VENDEDOR · CLIENTE_*  
Endpoint: EP-PED-03

ABAC-10 — acción: autorizar_precio_cliente  
Permitido SOLO: SUPERADMIN · ADMINISTRADOR · MECANICO_MASTER  
MECANICO_JUNIOR: bloqueado explícitamente — sin excepción  
Endpoint: EP-TAL-05
```
**Regla de respuesta diferenciada — crítica:**
```
SI la política ABAC protege un recurso cuya EXISTENCIA  
no debe confirmarse al actor no autorizado  
(ABAC-01 a ABAC-04)  
→ respuesta: RECURSO_NO_ENCONTRADO (404)

SI la política ABAC protege una acción sobre un recurso  
cuya existencia es pública o irrelevante para el actor  
(ABAC-07, ABAC-10)  
→ respuesta: ACCESO_DENEGADO (403)

SI la política ABAC omite un campo en lugar de bloquear  
el acceso al recurso completo  
(ABAC-08, ABAC-09)  
→ respuesta: 200 con el campo ausente del JSON —  
nunca null, nunca placeholder — ausente
```
El agente que devuelve 403 donde correspondía 404 (o
viceversa) viola esta regla — confirma indirectamente
la existencia de un recurso que no debía confirmarse.

### 3.4 Verificación ejecutable de ABAC — patrón de test
```
PARA CADA política ABAC-01 a ABAC-10:

1. Crear fixture de instancia (pedido/reserva/OT/etc.)  
    pertenece a actor_A.
2. Generar token válido de actor_B con mismo rol pero  
    identidad distinta.
3. Ejecutar la operación del endpoint con token de  
    actor_B sobre el recurso de actor_A.
4. Confirmar código de respuesta exacto según §3.3  
    regla de respuesta diferenciada — 404 o 403 según  
    corresponda a esa política específica.
5. Para ABAC-08 y ABAC-09 — confirmar AUSENCIA del  
    campo en el JSON crudo de respuesta, antes de  
    cualquier deserialización del lado cliente.
```
**Cobertura mínima exigida:** una política ABAC sin
al menos un test que reproduzca el escenario de fallo
(actor no autorizado) es una política no verificada —
no cuenta como implementada para criterios de avance
automático (referencia `09-criterios-avance-automatico`).

### 3.5 Escalada de privilegios — test obligatorio en staging

> No basta verificar RBAC y ABAC de forma aislada. El
> agente ejecuta además un test que intenta romper la
> frontera de rol mediante manipulación directa del
> token — no solo mediante el flujo normal de la API.
```
TEST: VENDEDOR no puede ejecutar operación de  
ADMINISTRADOR bajo ninguna manipulación del token  
— incluyendo intento de modificar el claim `rol`  
en un token ya firmado (debe fallar por firma  
inválida, no llegar a verificación de rol)
```
Este test corre en la suite de seguridad de staging —
no en el pipeline de PR por su naturaleza más costosa.
Referencia `10` §3.4 tabla de verificación.

---
## 4. Checklist OWASP API Top 10 — por endpoint

> Fuente: `10 seguridad-formal` §4 y §4.1.
> Aplica sobre los **55 endpoints** indexados en
> `03-diseno-sistema` §6.2 a §6.6 — no sobre 40. Ver
> §4.0 de este tramo para la corrección formal de cifra.
> El agente NO reproduce aquí el índice completo de
> endpoints — referencia el ID declarado en `03` §6 y
> aplica el control correspondiente según el riesgo
> OWASP que ese grupo de endpoints activa.

---

### 4.0 Corrección formal de cifra — OBS-EP-002 cerrada

`10 seguridad-formal` v1.0.0 fue cerrado citando "40
endpoints" en su frontmatter (CT-08-07), §1.3, intro de
§4, API9 y CT-08-07 de cierre. `03-diseno-sistema` v1.0.0
—construido después, con `08 contratos-interfaces` ya
evolucionado tras su sesión 0.9.1— indexó el conteo real
y vigente: **55 endpoints** (8 catálogo + 17 pedidos +
8 stock + 12 taller + 5 auth + 5 admin).

Verificación realizada para este tramo: cada ID de
"endpoint de mayor riesgo" citado en `10` §4 (API1 a
API10) existe sin alteración en el índice de 55 de `03`
§6. No hay endpoint huérfano de asignación de riesgo —
la diferencia de 15 endpoints entre 40 y 55 corresponde
a IDs que `10` ya incluía implícitamente en su análisis
de riesgo por grupo (ej. el bloque completo EP-PED-01
a 17, EP-ADM-01 a 05), no a endpoints nuevos sin
clasificar.

**Caso particular `EP-CAT-02-B`:** este ID aparece
nombrado explícitamente en `10` §3.3 ABAC-05 y en `10`
§4 API1 y API4 — es decir, `10` ya lo trataba como
entidad propia con riesgo asignado, aun cuando el
frontmatter de `10` no actualizó la suma total. No es
un endpoint que "apareció después" para efectos de
seguridad — solo para efectos de conteo agregado.

**Resultado: 55 de 55 endpoints con riesgo OWASP
asignado. OBS-EP-002 cerrada. ✅**
Acción recomendada — no bloqueante: parche quirúrgico
de frontmatter sobre `10 seguridad-formal` para corregir
"40" → "55" en los 5 puntos donde aparece la cifra.

---

### 4.1 API1:2023 — Broken Object Level Authorization
```
CONTROL: ABAC-01 a ABAC-10 (ver Tramo 2 §3.3) —  
verificación en use case, nunca en router  
ENDPOINTS: EP-PED-03 · EP-PED-05 · EP-TAL-12 ·  
EP-CAT-06 · EP-STK-08  
VERIFICAR: test por política ABAC con token de actor  
no autorizado → 404 RECURSO_NO_ENCONTRADO  
(nunca 403 cuando la existencia no debe  
confirmarse — ver Tramo 2 §3.3 regla de  
respuesta diferenciada)  
SUITE: tests/unit/{modulo}/use_cases/
```
### 4.2 API2:2023 — Broken Authentication
```
CONTROL: JWT RS256 + Refresh Token Rotation + MFA +  
rate limiting (ver Tramo 1 completo)  
ENDPOINTS: EP-AUTH-01 · EP-AUTH-02 · EP-AUTH-03  
VERIFICAR: token forjado → 401 ·  
refresh ya usado → invalida familia completa ·  
11 intentos fallidos → bloqueo activo ·  
acceso sin MFA para ADMINISTRADOR → sin  
access_token bajo ninguna condición
```
### 4.3 API3:2023 — Broken Object Property Level Authorization
```
CONTROL: Omisión de campos en servidor — ABAC-08 ·  
ABAC-09 (ver Tramo 2 §3.3)  
ENDPOINTS: EP-PED-03 · EP-STK-06 · EP-STK-08 · EP-CAT-06  
VERIFICAR: precio_costo_unitario AUSENTE en response  
raw para roles distintos a SUPERADMIN/  
ADMINISTRADOR · monto_con_descuento AUSENTE  
en response raw para VENDEDOR y CLIENTE_* ·  
inspección del JSON crudo, antes de  
deserialización del cliente
```
### 4.4 API4:2023 — Unrestricted Resource Consumption
```
CONTROL: Rate limiting por grupo de endpoints — tabla completa de 15 grupos con límite/ventana/scope en 03-diseno-sistema §10 (no reproducido aquí, ver Tramo 3 §4.4 nota de referencia) · cuota de consulta de precio · paginación page_size máximo 100 
ENDPOINTS: EP-CAT-01 · EP-CAT-02-B · EP-PED-01 · EP-STK-04  
VERIFICAR: solicitudes sobre umbral → 429 +  
header Retry-After ·  
page_size > 100 → 422 VALIDACION_FALLIDA ·  
cuarta consulta de precio en sesión →  
comportamiento de negocio (omisión de campo  
+ flag, ver Tramo 2 §3.3 ABAC-05) — NO 429
REFERENCIA: 03-diseno-sistema §10 — tabla ejecutable de rate limiting por grupo. El agente consulta esa tabla para el límite/ventana exactos de CUALQUIER endpoint — este archivo no repite esos valores para evitar dos fuentes de verdad sobre el mismo umbral (P2).
```
**Nota de precisión heredada del Tramo 2:** el límite de
consultas de precio NO produce HTTP 429 — produce omisión
de `precio_venta` con `precio_limite_alcanzado: true`.
Es la única excepción dentro de API4 donde el control no
es un código de error sino un cambio de payload. Fuente:
`08` §7.2, ya capturado en ABAC-05.

### 4.5 API5:2023 — Broken Function Level Authorization
```
CONTROL: RBAC en middleware (ver Tramo 2 §3.2) ·  
matriz de permisos en 10 §3.2  
ENDPOINTS: EP-CAT-04 · EP-STK-04 · EP-TAL-05 · EP-ADM-02 ·  
EP-PED-16 · EP-PED-17  
VERIFICAR: test parametrizado por rol sobre cada endpoint  
restringido → todos los roles no autorizados  
reciben 403 ACCESO_DENEGADO antes de ejecutar  
lógica · test específico de MECANICO_JUNIOR  
intentando EP-TAL-05 (ABAC-10) → bloqueado  
explícitamente
```
### 4.6 API6:2023 — Unrestricted Access to Sensitive Business Flows
```
CONTROL: Rate limiting en escritura (20 req/min) ·  
Idempotency-Key para S4 ·  
comprobante requiere pedido en estado cobrable  
ENDPOINTS: EP-PED-01 · EP-PED-06 · EP-PED-15 · EP-PED-16  
VERIFICAR: creación de pedidos sobre el límite → 429 ·  
comprobante sin pedido cobrable → 409  
TRANSICION_ESTADO_INVALIDA ·  
reserva masiva mismo repuesto/mismo usuario →  
rate limiting activo
```
### 4.7 API7:2023 — Server Side Request Forgery
```
CONTROL: URLs de WhatsApp/SMS fijas en variables de  
entorno — nunca construidas con input del  
usuario  
ENDPOINTS: ninguno directo — riesgo vive en  
infrastructure/notifications/  
VERIFICAR: revisión de código — ninguna URL se construye  
con input del usuario · número de teléfono  
fuera del patrón ^[0-9]{9}$ → rechazado
```
### 4.8 API8:2023 — Security Misconfiguration
```
CONTROL: CORS sin wildcard en producción · HSTS ·  
X-Content-Type-Options · X-Frame-Options ·  
Content-Security-Policy · campo `detail`  
omitido en producción · sin endpoints debug  
ENDPOINTS: todos — control transversal, no por grupo  
VERIFICAR: request con origen no permitido → rechazado ·  
response de error en producción sin stack  
trace · arranque sin variable crítica → falla  
rápido con mensaje claro (ver Tramo 4,  
§5.3 de 10) · checkov en pipeline sobre  
Dockerfile e infraestructura
```
### 4.9 API9:2023 — Improper Inventory Management
```
CONTROL: inventario cerrado — TODO endpoint declarado  
en 03-diseno-sistema §6, ningún endpoint sin  
contrato formal · un solo prefijo /v1/ ·  
EP-AUTH-05 único endpoint público sin  
exposición de datos de negocio  
ENDPOINTS: EP-AUTH-05 (único público) · cualquier  
endpoint no declarado en el índice de 55  
VERIFICAR: el conjunto de endpoints activos en el  
servidor coincide EXACTAMENTE con los 55  
declarados en 03-diseno-sistema §6 — no 40 —  
ningún endpoint responde fuera de /v1/ ·  
EP-AUTH-05 no expone datos internos bajo  
ninguna condición
```
**Nota de actualización respecto a `10`:** el criterio
original en `10` decía "coincide exactamente con los 40
declarados en `08`". El criterio vigente y corregido es
55 — ver §4.0 de este tramo.

### 4.10 API10:2023 — Unsafe Consumption of APIs
```
CONTROL: respuestas de WhatsApp/SMS validadas con  
Pydantic antes de procesar · timeout 10s  
WhatsApp / 15s SMS · errores externos nunca  
propagados al cliente  
ENDPOINTS: ninguno directo — riesgo vive en  
WhatsAppAdapter · SMSAdapter  
VERIFICAR: respuesta malformada de WhatsApp Stub →  
excepción de dominio tipada, sin propagación ·  
timeout → fallback a SMS dentro del tiempo  
declarado
```
---

### 4.11 Resumen de cobertura — corregido

| Riesgo | Control principal | Endpoints afectados (de 55) | Estado |
|---|---|---|---|
| API1 | ABAC-01 a ABAC-10 | 5 de mayor riesgo identificado | ✅ |
| API2 | JWT + MFA + rate limit + replay detection | 3 (auth) | ✅ |
| API3 | Omisión de campos — ABAC-08/09 | 4 de mayor riesgo identificado | ✅ |
| API4 | Rate limiting + paginación + cuota precio | 4 de mayor riesgo identificado | ✅ |
| API5 | RBAC en middleware | 6 de mayor riesgo identificado | ✅ |
| API6 | Rate limiting escritura + estado previo | 4 de mayor riesgo identificado | ✅ |
| API7 | URLs fijas en entorno | 0 directo — adaptadores | ✅ |
| API8 | CORS + headers + sin debug | 55 — transversal | ✅ |
| API9 | Inventario cerrado en 55, no 40 | 55 — transversal | ✅ |
| API10 | Pydantic + timeout + excepciones tipadas | 0 directo — adaptadores | ✅ |

**Criterio de verificación del archivo completo cumplido
para este tramo:** el agente puede tomar cualquiera de
los 55 endpoints de `03-diseno-sistema` §6, identificar
su grupo de riesgo OWASP por los endpoints de mayor
riesgo listados arriba o por su control transversal
(API8/API9), y aplicar el control correspondiente sin
abrir `10 seguridad-formal`.

---
## 5. Gestión de secretos — ejecutable

> Fuente: `10 seguridad-formal` §5.1 a §5.5.
> Regla P1 vinculante: este archivo declara nombres de
> variable y mecanismos de verificación — nunca un valor
> real de secreto, clave, token o credencial.

---

### 5.1 Clasificación de secretos — lista cerrada
```
CRITICOS (nunca en código, repo, logs, ni env de staging):  
RS256_PRIVATE_KEY — clave privada JWT  
ARGON2_PEPPER — pepper de hashing de passwords  
FERNET_KEY — cifrado en reposo (ADR-006)  
Credenciales PostgreSQL  
Clave SOL SUNAT — fuera del sistema, propiedad  
de Elena, nunca toca el sistema

INFRAESTRUCTURA (nunca en código ni repo):  
Credenciales Redis

INTEGRACION_EXTERNA (nunca en código, repo, logs):  
WHATSAPP_API_TOKEN  
Credenciales Twilio / AWS SNS

CICD (nunca en código, repo, logs de pipeline públicos):  
Secrets de GitHub Actions

DISTRIBUCION_PERMITIDA (variable de entorno, nunca hardcode):  
RS256_PUBLIC_KEY — distribución permitida por  
diseño, verificación de firma
```
**Regla de extensión:** ningún secreto nuevo se introduce
sin clasificarlo primero en una de estas 5 categorías.
Si no encaja en ninguna, se detiene el avance y se reporta
— no se asume una categoría por defecto.

### 5.2 Política de almacenamiento por entorno
```
DESARROLLO_LOCAL:  
mecanismo: .env en .gitignore desde el primer commit  
verificacion: Gitleaks en pre-commit hook (.gitleaks.toml  
con allowlist de tests)  
restriccion: nunca en repositorio bajo ninguna condición

RAILWAY_MVP:  
mecanismo: variables de entorno en Railway Dashboard,  
cifradas en reposo por Railway  
restriccion: sin secretos en railway.toml ni en archivos  
de configuración versionados

GITHUB_ACTIONS:  
mecanismo: GitHub Secrets · OIDC para Azure sin client  
secret de larga vida  
restriccion: sin secretos en archivos de workflow ni en  
logs de pipeline

PRODUCCION_AZURE (fase posterior):  
mecanismo: Azure Key Vault referenciado desde Container  
Apps  
restriccion: sin secretos en variables de entorno del  
contenedor en texto plano
```
### 5.3 Validación de variables de entorno al arranque — fail fast

> El agente implementa esto como la PRIMERA verificación
> que ejecuta el `api-server` al iniciar — antes de aceptar
> cualquier request. Si falla, el proceso termina con
> mensaje claro. Referencia: DEC-CL07.
```
VARIABLE FORMATO ESPERADO FALLA SI  
RS256_PRIVATE_KEY PEM -----BEGIN RSA PRIVATE KEY----- ausente o formato inválido  
RS256_PUBLIC_KEY PEM -----BEGIN PUBLIC KEY----- ausente o formato inválido  
ARGON2_PEPPER string >= 32 caracteres ausente o longitud insuficiente  
FERNET_KEY base64 URL-safe 32 bytes ausente o longitud inválida  
DATABASE_URL postgresql+asyncpg://... ausente o esquema incorrecto  
REDIS_URL redis://... ausente  
WHATSAPP_API_TOKEN string no vacío ausente  
SMS_PROVIDER enum: [twilio, aws_sns] ausente o fuera del enum  
SMS_API_KEY string no vacío ausente  
ENVIRONMENT enum: [development, staging,  
production] ausente
```
**Verificación ejecutable:** test de arranque que omite
deliberadamente cada variable una por una y confirma que
el proceso falla ANTES de exponer el puerto HTTP — nunca
arranca en estado parcial o degradado por variable
faltante. 10 variables × 1 test de ausencia = cobertura
mínima de este criterio.

**Nota de relación con `ENVIRONMENT`:** esta variable no
solo se valida en formato — su valor determina el nivel
de detalle en los mensajes de error expuestos al cliente
(ver Tramo 3 §4.8 API8 — campo `detail` omitido en
producción). El agente no trata `ENVIRONMENT` como una
variable más de la lista — es la que controla el
comportamiento de las otras 9 frente al cliente externo.

### 5.4 Calendario de rotación — ejecutable
```
SECRETO FRECUENCIA RESPONSABLE  
RS256_PRIVATE_KEY 90 días Sant  
ARGON2_PEPPER 180 días Sant  
FERNET_KEY 90 días Sant  
WHATSAPP_API_TOKEN según política Sant  
de Meta  
Credenciales Twilio/AWS SNS 90 días Sant  
Credenciales PostgreSQL 90 días Sant
```
**Procedimiento de rotación — patrón común, no repetido
por secreto:**
```
1. Generar nuevo valor del secreto.
2. Actualizar variable de entorno en el destino  
    correspondiente según §5.2 de este tramo.
3. Deploy.
4. Verificación post-rotación específica del secreto:
    - RS256_PRIVATE_KEY → invalidar TODOS los refresh  
        tokens activos (ver Tramo 1 §2.3 Escenario 3)
    - ARGON2_PEPPER → re-hashear passwords en migración  
        programada — operación de fondo, no bloqueante
    - FERNET_KEY → re-cifrar columnas sensibles —  
        ver lista cerrada en 03-diseno-sistema §5.7
    - credenciales de proveedor externo → smoke test de  
        conectividad/notificación antes de cerrar el ciclo
```
**Nota de detalle operativo:** el runbook paso a paso de
cada rotación —con comandos exactos y checklist de
ejecución— es responsabilidad de `08-plan-operacion-ejecutable`,
no de este archivo. Este tramo declara QUÉ rotar y CADA
CUÁNTO; el CÓMO operativo completo vive en `08` (pendiente,
ver mapa de ejecución — impacto CT-10-01 ya declarado
desde `10` hacia `11 plan-operacion`).

### 5.5 Verificación de ausencia de secretos en código — doble barrera
```
BARRERA 1 — commit local:  
mecanismo: Gitleaks en pre-commit hook  
config: .gitleaks.toml con allowlist de tests  
frecuencia: cada commit

BARRERA 2 — pipeline CI (independiente de barrera 1):  
mecanismo: Gitleaks en security.yml como gate  
bloqueante — DEC-P04  
frecuencia: cada PR  
regla: un desarrollador que deshabilita el hook  
local NO puede mergear a main sin pasar  
este gate — las dos barreras son  
independientes, no una respaldo opcional  
de la otra

BARRERA 3 — imagen Docker:  
mecanismo: Trivy con scan de secrets en imagen  
construida  
frecuencia: cada build

BARRERA 4 — historial Git:  
mecanismo: git log scan con Gitleaks  
frecuencia: al rotar cualquier secreto
```
**Acción ante detección — secuencia obligatoria:**
```
1. Pipeline bloquea el merge de inmediato.
2. Sant recibe alerta inmediata (ver Tramo 5 de este  
    archivo — audit trail categoría Seguridad).
3. El secreto se rota antes de cualquier otro avance —  
    no se continúa trabajando con el secreto expuesto  
    activo.
4. El commit con el secreto se elimina del historial  
    con git filter-branch o git filter-repo —  
    procedimiento detallado en 08-plan-operacion-ejecutable  
    (pendiente, CT-10-05 ya declarado desde 10 hacia 11).
```
**Verificación complementaria — dominio sin credenciales:**
`scripts/check_dip.py` (ver `03-diseno-sistema` §2.2)
verifica que ningún archivo en `domain/` importa desde
`infrastructure/` — esto incluye, por construcción,
que el dominio no puede importar un cliente de base de
datos o un SDK que requiera credenciales directamente.
La combinación de Gitleaks (detección de secretos) +
check_dip.py (arquitectura) es lo que cierra esta
verificación de forma completa — ninguno de los dos solo
es suficiente.

---
## 6. Privacidad y cumplimiento — Ley 29733 ejecutable

> Fuente: `10 seguridad-formal` §6.1 a §6.6.
> Regla vinculante: todos los controles de esta sección
> se implementan antes del primer usuario real — sin
> excepción. El registro ANPDP es precondición legal de
> apertura al público, no precondición de código.

---

### 6.1 Datos personales — clasificación ejecutable
```
DATO MODULO RETENCION  
nombre_cliente pedidos 5 años desde última transacción  
telefono_whatsapp pedidos 5 años desde última transacción  
dni_cliente pedidos 5 años — obligación tributaria  
si hay comprobante emitido  
ruc_cliente pedidos 7 años — obligación SUNAT  
historial_pedidos pedidos 5 años desde última transacción  
historial_orden_trabajo taller 5 años desde última intervención  
placa_tarjeta_propiedad taller 5 años desde última intervención  
deuda_activa taller + hasta cancelación + 2 años  
pedidos  
datos_proveedor_precio_costo stock 5 años desde última operación  
logs_auditoria infra 2 años  
timestamp_ip_sesion sesion 90 días desde cierre de sesión
```
**Regla de derecho al olvido aplicable:** todo dato
marcado con retención "desde última transacción/
intervención" es candidato a anonimización bajo §6.3
de este tramo — el agente no aplica derecho al olvido
sobre `ruc_cliente`, `deuda_activa` mientras esté activa,
ni `logs_auditoria` — estos tienen base legal de retención
que prevalece sobre la solicitud del titular.

### 6.2 Consentimiento explícito — Art. 13
```
CAMPO: consentimiento_datos: boolean — obligatorio  
para roles CLIENTE_* en EP-ADM-05  
VERIFICAR: crear CLIENTE_* sin consentimiento_datos:true  
→ 422 VALIDACION_FALLIDA

CAMPO: consentimiento_fecha: date-time — registrado  
automáticamente al crear la cuenta, tabla  
usuario_perfil (ver 03-diseno-sistema §5.6)  
VERIFICAR: consulta en BD — toda cuenta CLIENTE_* tiene  
consentimiento_fecha no nulo, sin excepción

REQUISITO: política de privacidad publicada y accesible  
SIN autenticación, URL en parametros_sistema  
VERIFICAR: smoke test — URL de política de privacidad  
responde sin token

CASO REGISTRO PRESENCIAL:  
cuando VENDEDOR crea cuenta en tienda vía EP-ADM-05,  
consentimiento_datos: true confirma que el vendedor  
informó verbalmente al cliente  
VERIFICAR: audit trail registra actor_id del vendedor  
que ejecutó el registro (ver §7.1 de este  
tramo, categoría Datos personales)
```
### 6.3 Derechos ARCO — proceso ejecutable
```
ACCESO:  
mecanismo: CLIENTE_* consulta vía EP-PED-02/03 y  
EP-TAL-12 — ya cubiertos por ABAC-01/04  
plazo: inmediato — el sistema ya lo provee

RECTIFICACION:  
mecanismo: ADMINISTRADOR corrige vía EP-ADM-05 update  
plazo: ≤ 72 horas desde solicitud  
responsable: Elena + Sant

CANCELACION (derecho al olvido):  
plazo: ≤ 72 horas desde solicitud — RNF-26  
responsable: Sant ejecuta · Elena autoriza  
proceso:  
1. Cliente presenta solicitud a Elena (presencial o  
WhatsApp).  
2. Elena registra la solicitud con timestamp y motivo  
(ver §7.1 de este tramo, categoría Datos personales).  
3. Sant ejecuta anonimización:  
nombre → "CLIENTE ANONIMIZADO"  
telefono → "000000000"  
dni → "00000000"  
placa → "ANONIMIZADO"  
email → {uuid}@anonimizado.local  
4. Registros de transacción (pedidos · comprobantes ·  
orden_trabajo) se CONSERVAN con datos anonimizados  
— obligación tributaria no permite eliminación.  
5. Cuenta de usuario → estado INACTIVO, nunca ELIMINADO  
— permanece para auditoría sin datos identificables.  
6. Sant documenta cierre con timestamp de ejecución.  
VERIFICAR: test que ejecuta el patrón de anonimización  
sobre fixture y confirma los 5 campos  
reemplazados exactamente con los valores  
declarados arriba — no aproximados, no  
nulos

OPOSICION:  
plazo: ≤ 72 horas desde solicitud  
responsable: Elena gestiona  
estado MVP: no aplica aún — sin marketing automático  
en el sistema
```
### 6.4 Registro ANPDP — precondición de deploy, no de código
```
ACCION RESPONSABLE MOMENTO  
identificar banco de datos "Clientes Sant + Elena antes del primer  
Tecnimotos Santi" usuario real  
completar formulario de inscripción ANPDP Elena + Sant antes del primer  
usuario real  
publicar política de privacidad en interfaz Sant antes del primer  
usuario real  
mantener registro actualizado ante cambios Elena continuo  
de finalidad
```
**Regla de bloqueo crítica:** el agente puede completar
el 100% del checklist técnico de este archivo y el
sistema seguirá sin poder abrirse a usuarios reales
hasta que el registro ANPDP esté completado. Este es
un criterio de negocio/legal, no técnico — el agente
no puede "resolverlo con código". El checklist pre-deploy
de `08-plan-operacion-ejecutable` (pendiente) debe incluir
verificación explícita del número de registro ANPDP
obtenido, según impacto CT-10-03 ya declarado desde `10`.

### 6.5 Cifrado de datos sensibles en reposo
```
DATO MECANISMO  
password_usuario Argon2id + pepper — nunca en claro  
telefono_cliente Fernet — columna cifrada, descifrado  
en application layer  
dni_cliente Fernet — idéntico  
precio_costo_unitario en eventos EDA Fernet sobre el campo del payload,  
antes de publicar en Redis Streams  
refresh_token en BD SHA-256 — solo el hash, nunca el  
token en claro
```
**Verificación ejecutable:** la lista cerrada de campos
cifrados con Fernet ya está declarada en
`03-diseno-sistema` §5.7 — este tramo no la repite,
solo confirma que el mecanismo (Fernet en capa de
aplicación, nunca en trigger de PostgreSQL) es el
criterio de seguridad vinculante. Test: insertar un
registro con un campo de la lista de `03` §5.7 y
confirmar que el valor en la columna de PostgreSQL,
leído directamente sin pasar por la aplicación, no es
legible en texto plano.

### 6.6 Data masking en entornos no productivos
```
STAGING: seeds con Faker — nunca datos reales  
VERIFICAR: pipeline rechaza seed con  
patrón de DNI real o teléfono real  
PREVIEW_ENVIRONMENTS: idéntico + destrucción automática al  
cerrar PR  
LOGS_DESARROLLO: teléfono → XXX-XXX-XXX · DNI →  
XXXXXXXX, aplicado por middleware  
de logging antes de escribir  
ENVIO_LLM_DESARROLLO: checklist de saneamiento manual  
antes de enviar fragmento de  
código con PII — responsabilidad  
de Sant, no automatizable en MVP
```
---

## 7. Auditoría y trazabilidad — audit trail ejecutable

> Fuente: `10 seguridad-formal` §7.1 a §7.4.

---

### 7.1 Operaciones auditables — 8 categorías, campos obligatorios
```
CATEGORIA: Autenticación  
eventos: login exitoso · login fallido · MFA completado ·  
MFA fallido · logout · refresh · replay detection  
campos: timestamp · actor_id · rol · ip_origen ·  
resultado · request_id

CATEGORIA: Autorización  
eventos: acceso denegado RBAC · acceso denegado ABAC ·  
intento de escalada de privilegios  
campos: timestamp · actor_id · rol · endpoint ·  
recurso_id · politica_violada · request_id

CATEGORIA: Precio y descuento  
eventos: actualización precio venta · aplicación  
descuento · consulta precio de costo  
campos: timestamp · actor_id · repuesto_id ·  
valor_anterior · valor_nuevo · request_id

CATEGORIA: Stock  
eventos: TODO movimiento — entrada · salida · ajuste ·  
apartado · liberado  
campos: timestamp · actor_id · repuesto_id · cantidad ·  
tipo_movimiento · modulo_origen · referencia_id ·  
request_id

CATEGORIA: Comprobante  
eventos: generación · aprobación · anulación  
campos: timestamp · actor_id · comprobante_id ·  
pedido_id · monto · tipo · resultado · request_id

CATEGORIA: Datos personales  
eventos: creación de cuenta · modificación de datos ·  
consentimiento registrado · solicitud ARCO ·  
anonimización ejecutada  
campos: timestamp · actor_id · usuario_afectado_id ·  
operacion · campos_modificados · request_id

CATEGORIA: Configuración  
eventos: modificación de parámetros — EP-ADM-02  
campos: timestamp · actor_id · clave_parametro ·  
valor_anterior · valor_nuevo · request_id

CATEGORIA: Seguridad  
eventos: rotación de secretos · bloqueo de IP ·  
desbloqueo manual · revocación masiva de  
tokens  
campos: timestamp · actor_id · tipo_evento · detalle ·  
request_id
```
**Verificación ejecutable:** test por categoría que
ejecuta la operación correspondiente y confirma que el
registro de auditoría generado contiene EXACTAMENTE los
campos obligatorios declarados — ni de menos (criterio
de fallo) ni es problema si hay campos adicionales
siempre que los obligatorios estén presentes.

### 7.2 Inmutabilidad — controles ejecutables
```
RESTRICCION_BD: tablas audit_* solo admiten INSERT —  
ningún proceso ejecuta UPDATE ni DELETE  
VERIFICAR: permisos de rol de aplicación  
sobre audit_* no incluyen UPDATE/DELETE  
(mismo patrón que movimiento_stock, ver  
03-diseno-sistema §5.3 nota de permisos)

SEPARACION_FISICA: audit_autenticacion · audit_stock ·  
audit_precio · audit_datos_personales ·  
audit_configuracion — tablas separadas,  
no una tabla genérica con campo "tipo"

FORMATO: JSON estructurado — todos los campos de  
§7.1 de este tramo

CORRELACION: request_id presente en TODO log —  
permite trazar todos los efectos de un  
mismo request

ACCESO_LECTURA: solo SUPERADMIN puede consultar tablas de auditoría — EXCLUSIVAMENTE vía SSH directo a PostgreSQL desde san-aorus o tecnimoto (ambos nodos Tailscale con Ed25519 + MFA). NUNCA vía endpoint HTTP, bajo ninguna condición ni rol — la superficie HTTP queda descartada por diseño para este dato, no solo restringida por RBAC. Referencia: 11-plan-operacion §6.5 · OBS-EP-005.
```
**Nota de cobertura:** la categoría "Seguridad" definida
en §7.1 incluye explícitamente "rotación de secretos" —
esto cierra la referencia pendiente del Tramo 4 §5.5
paso 2 ("Sant recibe alerta inmediata — ver Tramo 5").
La detección de Gitleaks no es en sí un evento de
categoría Seguridad en `audit_*` — es una alerta de
pipeline (ver §7.4 de este tramo); lo que sí se audita
en `audit_*` es la rotación del secreto una vez ejecutada
como respuesta.

### 7.3 Retención por tipo de log
```
audit_stock 5 años  
audit_comprobante 7 años — obligación SUNAT  
audit_datos_personales 5 años — Ley 29733, demostrar  
cumplimiento ante ANPDP  
audit_autenticacion 2 años — detección de  
patrones de ataque  
audit_configuracion 3 años  
logs_infraestructura 90 días — Railway/Azure  
registros_sesion 90 días desde cierre
```
### 7.4 Alertas en tiempo real — umbrales ejecutables
```
CONDICION UMBRAL DESTINATARIO  
errores HTTP 500 1 error Sant — inmediato  
latencia sostenida > 2s por > 30s Sant  
errores de autenticación > 10 por minuto Sant — inmediato  
intento de escalada de privilegios 1 intento Sant — inmediato  
replay detection activado 1 evento Sant — inmediato  
secreto detectado por Gitleaks 1 detección Sant — alerta  
bloqueante de  
pipeline  
cobertura bajo umbral en pipeline cualquier módulo Sant — pipeline  
bajo su umbral bloqueado
```
**Cierre de referencia pendiente:** esto resuelve
formalmente la promesa hecha en Tramo 4 §5.5 — "Sant
recibe alerta inmediata" para detección de Gitleaks
corresponde exactamente a la fila "secreto detectado
por Gitleaks" de esta tabla.

---
## 8. Criterios de verificación del archivo completo

> Verificación contra el criterio de cierre declarado en
> `mapa-de-ejecucion.md` del DOC-3 para `07`: "El agente
> puede verificar que un endpoint nuevo cumple los 10
> controles OWASP antes de mergear, sin consultar el DOC-2."

### 8.1 Checklist de verificación ejecutable — archivo completo
```
□ El agente puede emitir y verificar un JWT RS256 con  
los parámetros exactos de Tramo 1 §2.1, sin abrir 10  
□ El agente puede confirmar MFA obligatorio para  
SUPERADMIN/ADMINISTRADOR vía consulta de audit trail  
(Tramo 1 §2.4 + Tramo 5 §7.1 categoría Autenticación)  
□ El agente puede aplicar el patrón de verificación RBAC  
sobre cualquiera de los 55 endpoints de 03-diseno-sistema  
§6, sin reproducir la matriz de 10 §3.2 (Tramo 2 §3.2)  
□ El agente puede ejecutar un test por cada una de las  
10 políticas ABAC con su respuesta diferenciada correcta  
404 vs 403 (Tramo 2 §3.3 — incluyendo corrección  
aplicada sobre ABAC-06 vía parche de sesión)  
□ El agente puede tomar cualquier endpoint nuevo de los  
55 indexados, identificar su grupo de riesgo OWASP y  
aplicar el control correspondiente sin abrir 10  
(Tramo 3 §4.1 a §4.10 — OBS-EP-002 resuelta)  
□ El agente puede validar las 10 variables de entorno  
críticas al arranque con fail-fast verificable  
(Tramo 4 §5.3)  
□ El agente puede ejecutar el patrón de rotación para  
cualquiera de los 6 secretos calendarizados  
(Tramo 4 §5.4)  
□ El agente puede confirmar la doble barrera Gitleaks  
como controles independientes, no redundantes  
(Tramo 4 §5.5)  
□ El agente puede ejecutar el proceso de anonimización  
de derecho al olvido con los 5 campos exactos  
(Tramo 5 §6.3)  
□ El agente puede generar un registro de audit trail  
para cualquiera de las 8 categorías con sus campos  
obligatorios exactos (Tramo 5 §7.1)
```
### 8.2 Criterio de no dependencia hacia el DOC-2

El agente que complete el checklist de §8.1 no necesitó
abrir `10 seguridad-formal` del DOC-2 — toda la
información de autenticación, autorización, OWASP,
secretos, privacidad y auditoría necesaria para esas
tareas está sintetizada en los 6 tramos de este archivo.
Las únicas referencias hacia otros archivos del DOC-3
son deliberadas y por diseño, para evitar duplicación
según P2:
```
03-diseno-sistema §6 → índice completo de 55 endpoints  
(Tramo 2 §3.2 · Tramo 3 completo)  
03-diseno-sistema §7 → índice completo de 24 eventos  
(no consultado directamente en  
este archivo, pero el envelope  
de eventos comparte el mismo  
principio de no-duplicación)  
03-diseno-sistema §10 → tabla de rate limiting por grupo  
(Tramo 3 §4.4, corregida vía  
parche de sesión)  
03-diseno-sistema §5.7 → lista cerrada de campos cifrados  
Fernet (Tramo 5 §6.5)  
08-plan-operacion-ejecutable → runbooks operativos de  
rotación, anonimización y brecha  
(pendiente — referencias  
explícitas en Tramo 4 §5.4/§5.5  
y Tramo 5 §6.4)
```
---

## 9. Observaciones activas — generadas durante esta construcción

| ID | Observación | Origen | Estado |
|---|---|---|---|
| OBS-EP-002 | `10-seguridad-formal` frontmatter y 5 menciones internas declaran "40 endpoints"; cobertura real verificada uno a uno contra `03-diseno-sistema` §6 confirma 55 (actualizado con EP-CAT-07 vía PCT-CONSTRUCCION-003), sin endpoint huérfano de riesgo OWASP | Tramo 3 §4.0 | ✅ Resuelta — parche de frontmatter sobre `10` recomendado, no bloqueante |
| OBS-EP-003 | `10-seguridad-formal` §3.3 ABAC-06 no declaraba el nombre del campo `motivo_validacion` ni la regla precisa de transición de estado para `VENDEDOR` vs `ADMINISTRADOR`/`SUPERADMIN` en EP-PED-15 | Tramo 2 §3.3, ampliada con fragmento de `08 contratos-interfaces` | ✅ Resuelta y ampliada — `08` adoptado como fuente más específica, parche aplicado sobre Tramo 2 |
| OBS-EP-004 | `10-seguridad-formal` §7.1 categoría Seguridad lista "desbloqueo manual" de IP como evento auditable, sin endpoint ni mecanismo declarado en `10` ni `03-diseno-sistema` para ejecutarlo | Tramo 5 §7.1 | 🔵 Abierta — no bloqueante, pertenece a `08-plan-operacion-ejecutable` o a un endpoint administrativo futuro |

**Resultado: 3 observaciones generadas · 2 resueltas dentro de esta sesión · 1 abierta no bloqueante dirigida a construcción futura.**

---

## 10. Fuentes

| Documento | Versión | Secciones consultadas |
|---|---|---|
| `10 seguridad-formal` | v1.0.0 | §1 a §10 completas — fuente única declarada de este archivo |
| `03-diseno-sistema` | v1.0.0 | §6 índice de 55 endpoints · §7 índice de 24 eventos · §5.7 campos cifrados Fernet · §5.3 nota de permisos de escritura · §10 rate limiting · §2.2 check_dip.py |
| `08 contratos-interfaces` | v1.0.0 (fragmento EP-PED-15) | Schema completo de request body, regla de estado inicial, códigos de error — usado para resolver OBS-EP-003 |
| `mapa-de-ejecucion.md` (DOC-3) | v1.2 | Criterio de cierre declarado para archivo `07` |

---

## 11. Historial de versiones

| Versión    | Fecha                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Cambio                                                                                                                                                   | Impacto                                                                              |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 0.1.0      | 2026-06                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Tramo 1 — frontmatter · propósito · autenticación JWT RS256 + MFA ejecutable                                                                             | Base de verificación de autenticación establecida                                    |
| 0.2.0      | 2026-06                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Tramo 2 — RBAC 5 roles + 6 sub-roles · 10 políticas ABAC ejecutables                                                                                     | Base de autorización establecida — parche posterior sobre ABAC-06                    |
| —          | 2026-06                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Parche de sesión — corrección ABAC-06 (estado inicial VENDEDOR vs ADMINISTRADOR/SUPERADMIN) vía fragmento de `08 contratos-interfaces`                   | OBS-EP-003 resuelta y ampliada                                                       |
| 0.3.0      | 2026-06                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Tramo 3 — checklist OWASP API1 a API10 · corrección formal de cifra 40→54                                                                                | OBS-EP-002 resuelta — cobertura completa confirmada sobre los 54 endpoints reales    |
| —          | 2026-06                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Parche de sesión — corrección de referencia rate limiting en §4.4 hacia `03-diseno-sistema` §10 directo, sin sección nueva                               | Evita introducir contenido fuera de alcance acordado — preserva P2                   |
| 0.4.0      | 2026-06                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Tramo 4 — clasificación de secretos · validación de arranque · calendario de rotación · doble barrera Gitleaks                                           | Cierra criterio transversal "Secrets scan sin hallazgos" de `09`                     |
| 0.5.0      | 2026-06                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Tramo 5 — Ley 29733 ejecutable (datos personales, consentimiento, ARCO, registro ANPDP) · audit trail 8 categorías · inmutabilidad · retención · alertas | OBS-EP-004 generada — desbloqueo manual de IP sin mecanismo declarado                |
| 1.0.0      | 2026-06                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Tramo 6 — criterio de verificación global · consolidación de observaciones · fuentes · historial · cierre formal                                         | Documento completo — 6 de 6 tramos cerrados sin observaciones bloqueantes pendientes |
| 1.0.1      | 2026-06 | PCT-CONSTRUCCION-003 — conteo de endpoints actualizado de 54 a 55 tras formalización de EP-CAT-07 en 03 §6.2 | 55/55 endpoints con riesgo OWASP asignado — inventario actualizado |


---

**Resultado de cierre: `07-criterios-seguridad-ejecutables.md` v1.0.1 — 6 de 6 tramos completados. 3 observaciones generadas, 2 resueltas, 1 abierta no bloqueante. Sin CT pendientes de esta construcción.**
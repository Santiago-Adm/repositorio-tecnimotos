---
version: 1.0.0
estado: cerrado
archivo: "08"
titulo: Plan de operación ejecutable
autor: Sant
fecha: 2026-06
validador: Sant
aprobado: true
fuente_doc2_unica: "11 plan-operacion v1.0.0"
tramo_actual: 6 de 6 — cierre · SE-07 · validación Elena · observaciones · fuentes · historial
alimenta: ["09-criterios-avance-automatico"]
cambio: "Tramo 6 — criterios de adopción SE-07 · criterios de cancelación CC-01 a CC-05 · protocolo de validación de Elena en tecnimoto · consolidación de observaciones · 4 CT heredados de 11 sin resolver · fuentes · historial · cierre formal v1.0.0"
impacto: "Archivo completo — desbloquea la renumeración pendiente de 09-criterios-avance-automatico, que ahora puede referenciar 07 y 08 sin duplicar su contenido"
---

# 08 — Plan de operación ejecutable
## Tecnimotos Santi · DOC-3 — Protocolo de construcción

> Este archivo responde al agente: ¿cómo despliego,
> opero y recupero el sistema ante incidentes?
> Fuente única: `11 plan-operacion` v1.0.0.
> El agente consulta este archivo ante cualquier
> incidente operativo, antes de cada deploy, y en
> los checklists periódicos — sin necesidad de abrir
> el DOC-2.

---

## 1. Propósito

Este archivo instruye al agente sobre cómo desplegar
el sistema en cada fase, cómo recuperarlo ante fallos,
y cómo verificar que está listo para operar. A
diferencia de `07-criterios-seguridad-ejecutables`,
los procedimientos de este archivo no se sintetizan
desde su fuente — se trasladan casi completos, porque
ya son la pieza atómica de ejecución que el agente
necesita consultar en el momento exacto del incidente,
sin depender de acceso al DOC-2 ni a Obsidian.

El agente que lee este archivo puede:
desplegar el sistema en cualquiera de las 4 fases con
sus condiciones de entrada y salida exactas · ejecutar
cualquiera de los 9 runbooks operativos ante un
incidente declarado · ejecutar cualquiera de los 6
runbooks de seguridad con plazo legal · completar los
3 checklists operativos con resultado binario ·
reconocer los criterios de adopción del MVP sin
necesitar interpretarlos.

**Regla de precedencia:** ante cualquier ambigüedad
entre este archivo y `11 plan-operacion`, `11` es la
fuente de verdad. Este archivo se actualiza para
reflejarla — nunca al revés.

**Regla de traslado casi completo — excepción a P2:**
Los runbooks de §3 y §4 de este archivo no son síntesis
— son el contenido ejecutable de `11` trasladado con
mínima edición de formato. Esto es una excepción
deliberada al principio de síntesis sin duplicación,
justificada porque no existe en el DOC-3 ningún otro
archivo más detallado que sintetizar — `11` ya es el
nivel de detalle mínimo necesario para ejecución sin
DOC-2.

---

## 2. Restricciones operativas vinculantes

> Fuente: `11 plan-operacion` §1.2.
> Estas 6 restricciones gobiernan cómo se escribe
> CUALQUIER runbook o checklist de este archivo —
> ningún procedimiento de los tramos siguientes puede
> contradecirlas.

```
RO-01 Sant es el ÚNICO operador técnico durante el  
MVP — ningún runbook de este archivo puede  
requerir un segundo operador técnico.

RO-02 tecnimoto es un thin client — Elena accede  
vía navegador sobre Tailscale. No hay stack  
local que operar en ese nodo desde el lado  
de Elena.

RO-03 Horario comercial: 8:00–20:30, lunes a sábado.  
Downtime fuera de ese horario es aceptable si  
se resuelve antes de la apertura.

RO-04 Elena NO ejecuta ningún procedimiento técnico.  
Su rol es reportar síntoma — nunca diagnosticar  
ni intervenir. Ningún runbook de este archivo  
puede asignarle un paso técnico.

RO-05 El canal de reporte de Elena hacia Sant es  
WhatsApp — no Slack, no email, no sistema de  
tickets.

RO-06 Todo procedimiento de recuperación debe poder  
ejecutarse desde san-aorus vía Tailscale, sin  
presencia física en el nodo de infraestructura.
```
**Verificación ejecutable:** cualquier runbook de §3 o
§4 de este archivo que asigne un paso técnico a Elena,
o que requiera presencia física, o que requiera un
segundo operador técnico, viola RO-01 a RO-06 y debe
corregirse antes de aprobarse — no es un detalle menor,
es un criterio de rechazo del runbook completo.

---

## 3. Estrategia de despliegue por fase — ejecutable

> Fuente: `11 plan-operacion` §2.1 a §2.4.
> Formaliza ADR-003 en condiciones de entrada/salida
> verificables.

### 3.1 Fase 0 — Desarrollo local
```
INFRAESTRUCTURA: san-aorus — Docker Compose local  
STACK: api-server FastAPI · PostgreSQL 16 ·  
Redis 7 · Next.js dev server  
ACCESO_ELENA: Tailscale — tecnimoto → IP de  
san-aorus en red privada → navegador  
→ URL de staging

MODELO_OPERATIVO:  
san-aorus levanta Docker Compose  
└── api-server :8000  
└── next-dev :3000  
└── postgres :5432  
└── redis :6379  
Elena abre navegador en tecnimoto  
└── http://[ip-tailscale-san-aorus]:3000  
└── usa el sistema exactamente como en producción  
└── Sant observa comportamiento real — sin intervenir

CONDICION_SALIDA: Elena completa los flujos críticos  
de ADMINISTRADOR sin asistencia de  
Sant en más de 1 de cada 5 intentos  
(flujos declarados en Tramo 6 §9  
de este archivo)
```
### 3.2 Fase 1 — Railway MVP
```
INFRAESTRUCTURA: Railway — api-server · PostgreSQL  
managed · Redis managed  
FRONTEND: Vercel o Railway — Next.js separado  
DESPLIEGUE: automático desde main en GitHub —  
push despliega  
SECRETOS: variables de entorno en Railway —  
sin secretos en código  
COSTO_ESTIMADO: S/100–200/mes según volumen  
ADMINISTRACION: Sant desde san-aorus vía CLI Railway  
o panel web sobre Tailscale

CONDICION_ENTRADA: checklist pre-deploy de Tramo 5 §7.1  
en verde · Elena validó flujos en  
Fase 0 · backups configurados y  
probados (ver Tramo 2 §4 de este  
archivo)

CONDICION_SALIDA (cualquiera activa Fase 2):

- latencia P95 > 2s sostenida por más de 3 días
- costo Railway > S/300/mes
- necesidad de red privada entre servicios
- cualquier CC-01 a CC-05 de 02-alcance activada  
    (ver Tramo 6 §8.2 de este archivo)
```
### 3.3 Fase 2 — VPS Hetzner
```
INFRAESTRUCTURA: VPS Hetzner CAX21 o equivalente —  
Docker Compose en servidor  
BASE_DE_DATOS: PostgreSQL con PITR habilitado ·  
respaldo en objeto externo  
REDIS: Redis Sentinel — alta disponibilidad  
básica  
ACCESO_SEGURO: Tailscale en nodo Hetzner — Sant  
administra remotamente sin exponer  
puertos  
DESPLIEGUE: GitHub Actions — ssh + docker  
compose pull && up -d  
COSTO_ESTIMADO: €15–25/mes fijo

CONDICION_ENTRADA: cualquier condición de salida de  
Fase 1 cumplida · runbooks de esta  
fase documentados y probados en  
staging antes de migrar

CONDICION_SALIDA (cualquiera activa Fase 3+):

- tráfico > 500 req/min sostenido
- necesidad de multi-región o compliance que  
    requiera proveedor certificado
- decisión con métricas reales — no proyecciones
```
### 3.4 Fase 3+ — AWS o Azure
```
INFRAESTRUCTURA: Azure Container Apps o AWS ECS —  
decisión en ese momento con  
métricas reales  
BASE_DE_DATOS: Azure DB Flexible Server o AWS RDS —  
PITR nativo · managed backups  
SECRETOS: Azure Key Vault o AWS Secrets  
Manager · Managed Identity  
IAC: Terraform con state remoto

CONDICION_ENTRADA: cualquier condición de salida de  
Fase 2 cumplida · decisión formal  
con datos reales de Fase 2

PRINCIPIO_PORTABILIDAD: el código no cambia entre  
fases — todo corre en contenedores Docker. Migrar  
de fase es cambiar variables de entorno y config  
de infraestructura, nunca reescribir la aplicación.  
RNF-29 y RNF-30 garantizan este principio.
```
---
## 4. RTO y RPO — objetivos de recuperación ejecutables 
> Fuente: `11 plan-operacion` §3.1 a §3.4. 
### 4.1 Valores declarados — contrato con el negocio
```
RTO (Recovery Time Objective): 4 horas  
RPO (Recovery Point Objective): 24 horas

DOWNTIME_ACEPTABLE: fuera de horario comercial  
(20:30–8:00) — el sistema puede  
estar inactivo si se resuelve  
antes de la apertura  
DOWNTIME_CRITICO: dentro de horario comercial  
(8:00–20:30 L–S) — cada hora de  
inactividad es operación perdida  
para Elena
```
**Justificación de los valores — el agente no los
trata como aspiracionales:**
```
RTO=4h: la tienda tiene canal alternativo presencial  
— Elena puede operar en papel durante ese  
período. 4h es el máximo antes de que las  
ventas perdidas superen el costo de la  
recuperación.  
RPO=24h: el backup diario automatizado cubre este  
valor. Pérdida máxima de un día de  
transacciones — aceptable en MVP con volumen  
bajo y operaciones reconstruibles por Elena  
desde memoria operativa.
```
**Condición de revisión obligatoria — no opcional:**
```
SI el sistema incorpora pagos digitales en Fase 2  
ENTONCES RPO debe reducirse a 1 hora  
Y RTO debe reducirse a 1 hora  
→ decisión formal como ADR en ese momento, no  
ajuste silencioso de estos valores
```
### 4.2 Estrategia de recuperación por fase
```
Fase 0 — Local: Sant reinicia Docker Compose  
en san-aorus  
Tiempo: < 5 minutos

Fase 1 — Railway: redeploy automático desde  
GitHub · restauración desde  
backup si hay corrupción  
Tiempo: 30 min – 4h según causa

Fase 2 — Hetzner: docker compose up -d desde  
san-aorus vía SSH · restauración  
desde backup lógico si aplica  
Tiempo: 1–4h según causa

Fase 3+ — Azure/AWS: procedimiento específico del  
proveedor con PITR nativo —  
definido al iniciar esa fase  
Tiempo: según SLA del proveedor
```
### 4.3 Procedimiento de fallback — ejecutable

**Condición de activación:** el sistema lleva más de
2 horas inactivo en horario comercial Y Sant no tiene
ETA de recuperación menor a 2 horas adicionales.
```
1. Sant notifica a Elena por WhatsApp:  
    "El sistema va a tardar más de lo esperado.  
    Activa el modo papel hasta nuevo aviso."
2. Elena activa operación en papel:  
    — Ventas: registro manual en cuaderno de tienda  
    — Stock: Elena consulta físicamente el almacén  
    — Taller: MECANICO_MASTER anota en registro físico  
    — Comprobantes: boletas físicas manuales
3. Sant trabaja en recuperación sin presión de  
    Elena en el sistema.
4. Cuando el sistema vuelve, Sant notifica a Elena.
5. Elena registra en el sistema las operaciones  
    del período de fallback — en ese mismo día  
    antes del cierre.
6. Sant registra el incidente en el log de  
    post-mortem con causa, duración y acción  
    correctiva (docs/postmortems/).
```
**Restricción crítica — verificación de RO-04:**
Elena NUNCA diagnostica ni reinicia nada del sistema.
Su único rol es reportar el síntoma por WhatsApp y
activar el modo papel. Cualquier runbook que le asigne
un paso técnico en este escenario viola RO-04 (Tramo 1
§2) y debe corregirse.

---

## 5. Backups — estrategia 3-2-1 ejecutable

> Fuente: `11 plan-operacion` §4.1 a §4.5.
> Implementa RNF-07. Regla 3-2-1: 3 copias · 2 medios
> distintos · 1 offsite.

### 5.1 Qué se respalda — clasificación por criticidad
```
CRITICA:

- Base de datos PostgreSQL — fuente de verdad de  
    todo el negocio (stock, pedidos, clientes, OT)
- Variables de entorno y secretos — respaldo en  
    gestor de secretos, NUNCA en archivo plano

ALTA:

- Código fuente — respaldado automáticamente en  
    GitHub, sin procedimiento adicional
- Logs de auditoría — retención 5 años
- Configuración de infraestructura IaC — Git,  
    reproducible desde cero

MEDIA:

- Assets estáticos del catálogo — recuperables  
    desde fuente si se pierden
```
### 5.2 Implementación 3-2-1 — Fase 1 Railway
```
COPIA 1: PostgreSQL managed Railway — automático,  
continuo (PITR si disponible) — retención 7d  
COPIA 2: pg_dump lógico → Object storage externo  
(Backblaze B2 o equiv.) — diario 02:00 UTC-5  
— retención 30d  
COPIA 3: pg_dump comprimido → san-aorus local  
(/backups/tecnimotos/) — semanal, domingo  
03:00 UTC-5 — retención 90d
```
### 5.3 Implementación 3-2-1 — Fase 2 Hetzner
```
COPIA 1: PITR PostgreSQL en disco del VPS — continuo,  
WAL archiving — retención 7d  
COPIA 2: pg_dump lógico → Hetzner Object Storage o  
Backblaze B2 — diario 02:00 UTC-5 — retención 30d  
COPIA 3: pg_dump comprimido → san-aorus local —  
semanal, domingo 03:00 UTC-5 — retención 90d
```
### 5.4 Procedimiento de backup lógico diario — automatizado

> Ejecutado por GitHub Actions o cron. Sant NO ejecuta
> esto manualmente en operación normal.

```bash
# 1. pg_dump ejecuta a 02:00 UTC-5
pg_dump $DATABASE_URL \
  --format=custom \
  --compress=9 \
  --file=backup_$(date +%Y%m%d).dump

# 2. Sube a object storage
rclone copy backup_$(date +%Y%m%d).dump \
  backblaze:tecnimotos-backups/daily/

# 3. Archivos con más de 30 días se eliminan
#    automáticamente por política del bucket

# 4. Log de éxito/fallo enviado a Sant vía alerta
#    del pipeline

# 5. Si falla: alerta crítica a Sant — Sant verifica
#    y relanza manualmente antes de las 08:00 del
#    mismo día
```

### 5.5 Verificación trimestral de restauración — obligatoria

> R26 — backups sin prueba de restauración no son
> backups, son archivos con esperanza.
> Frecuencia: cada 90 días, alineado con checklist
> trimestral (Tramo 5 §7.3 de este archivo).

```bash
# 1. Descargar backup más reciente del object storage

# 2. Levantar instancia PostgreSQL en staging
#    (Docker local o Railway staging)

# 3. Ejecutar restauración
pg_restore --dbname=tecnimotos_staging \
  --clean --if-exists \
  backup_YYYYMMDD.dump

# 4. Verificar integridad mínima:
#    - count de registros en repuesto, pedido,
#      orden_trabajo, cliente
#    - al menos un pedido y una orden_trabajo
#      completos, legibles y coherentes
#    - el sistema levanta contra esa BD sin
#      errores de migración

# 5. Registrar resultado en checklist trimestral
#    con fecha y hash del backup restaurado

# 6. Si la restauración falla: incidente de
#    Severidad 1 — Sant investiga causa y corrige
#    antes de continuar
```

### 5.6 Lo que NO se respalda — y por qué
```
SECRETOS_TEXTO_PLANO: nunca en backup — riesgo de  
exposición. Fuente de verdad:  
Key Vault / Railway env vars  
SESIONES_REDIS: efímeras por diseño, TTL nativo  
— usuarios re-autentican tras  
restauración  
COLA_REINTENTOS_REDIS_DB2: mensajes en tránsito,  
aceptable perderlos en fallo  
mayor — notification-service  
reintenta desde outbox  
LOGS_INFO_DEBUG: retención 30 días, no son  
datos de negocio
```
---
## 6. Runbooks — escenarios críticos de operación

> Fuente: `11 plan-operacion` §5.1 a §5.9.
> Cada runbook: síntoma detectable · diagnóstico
> ordenado · resolución · criterio de éxito.
> Verificación cruzada con Tramo 1 §2 (RO-01 a RO-06):
> ningún paso de estos 9 runbooks asigna tarea técnica
> a Elena ni requiere un segundo operador técnico.

---

### 6.1 Caída del api-server

**Síntoma:** disponibilidad < 99% · health check
`/health` no responde · Elena reporta por WhatsApp
que el sistema no carga.

**Diagnóstico en orden:**
```
1. Verificar alerta — confirmar que no es falso  
    positivo del Blackbox Exporter.
2. curl https://[dominio]/health
3. Revisar logs:  
    Fase 1 Railway: panel → logs del servicio  
    Fase 2 Hetzner:  
    ssh san@[ip-tailscale-hetzner]  
    docker logs tecnimotos-api --tail=100
4. Identificar causa:
    - OOM (proceso muerto por RAM)
    - error de arranque (fallo conexión BD/Redis)
    - crash de aplicación (excepción no manejada)
    - deploy fallido (imagen rota en último push)
```
**Resolución según causa:**
```
OOM:  
Fase 1: Railway reinicia automáticamente.  
Si recurre en < 1h → escalar plan Railway.  
Fase 2: docker restart tecnimotos-api  
Revisar memory limits en compose.

Error de arranque por BD o Redis:  
→ ir a runbook §6.2 (PostgreSQL) o §6.3 (Redis)  
según indique el log.

Crash de aplicación:  
git log --oneline -5 ← identificar último commit  
railway rollback ← Fase 1  
docker compose up -d --no-deps api ← Fase 2,  
imagen anterior

Deploy fallido:  
Fase 1: railway rollback [deployment-id]  
Fase 2: docker pull [imagen-anterior]  
docker compose up -d
```
**Criterio de éxito:** `curl https://[dominio]/health`
responde 200 · Elena confirma por WhatsApp que el
sistema carga · alerta cerrada.

**Post-mortem:** registrar en `docs/postmortems/` con
fecha · causa raíz · tiempo de recuperación · acción
correctiva.

---

### 6.2 Fallo de PostgreSQL

**Síntoma:** error rate > 0.5% con `connection refused`
o `FATAL: remaining connection slots` en logs ·
operaciones de escritura fallan.

**Diagnóstico en orden:**
```
1. Confirmar que es PostgreSQL y no el api-server:  
    si /health responde pero las operaciones fallan  
    → PostgreSQL es el candidato.
2. Fase 1 Railway:  
    Panel → servicio PostgreSQL → estado.  
    Si caído: Railway gestiona el reinicio.  
    Esperar máximo 10 min antes de escalar a soporte.
3. Fase 2 Hetzner:  
    ssh san@[ip-tailscale-hetzner]  
    docker ps | grep postgres  
    docker logs tecnimotos-postgres --tail=50
4. Causas comunes Fase 2:
    - disco lleno: df -h → si > 90% → limpiar logs  
        o ampliar volumen
    - conexiones agotadas: revisar max_connections  
        y pool del api-server
    - corrupción: pg_dump falla con error → activar  
        fallback (Tramo 2 §4.3) · restaurar desde  
        backup (Tramo 2 §5.5)
```
**Resolución según causa:**
```
Disco lleno:  
docker exec tecnimotos-postgres  
psql -U postgres -c "VACUUM FULL;"  
Si no libera suficiente: ampliar volumen en  
panel Hetzner.

Conexiones agotadas:  
docker restart tecnimotos-api  
Si recurre: reducir pool_size en SQLAlchemy  
config y redesplegar.

Reinicio de PostgreSQL en Fase 2:  
docker restart tecnimotos-postgres  
Esperar 30 segundos.  
docker logs tecnimotos-postgres --tail=20  
Verificar "database system is ready to  
accept connections".

Corrupción confirmada:  
→ activar fallback (Tramo 2 §4.3) inmediatamente.  
→ restaurar desde backup (Tramo 2 §5.5).  
→ notificar a Elena: modo papel activado.
```
**Criterio de éxito:** operaciones de escritura
responden correctamente · error rate < 0.5% · alerta
cerrada · datos íntegros verificados con count en
tablas críticas.

---

### 6.3 Fallo de Redis

**Síntoma:** error rate con `redis.exceptions.
ConnectionError` en logs · EDA interno detenido ·
sesiones no válidas · notificaciones no se envían.

**Diagnóstico en orden:**
```
1. Logs del api-server:
    - "ConnectionError" → Redis no responde
    - "NOGROUP" → consumer group perdido
    - "WRONGTYPE" → corrupción de clave
2. Fase 1 Railway: panel → servicio Redis → estado.  
    Si caído: Railway gestiona el reinicio.
3. Fase 2 Hetzner:  
    docker ps | grep redis  
    docker logs tecnimotos-redis --tail=30  
    docker exec tecnimotos-redis redis-cli ping  
    → esperado: PONG
```
**Impacto por DB lógica durante el fallo:**
```
DB-0 Event bus: EDA interno detenido.  
Recuperación: eventos en outbox PostgreSQL no se  
pierden — el worker reintenta al volver Redis.

DB-1 Caché y sesiones: usuarios pierden sesión,  
parámetros se recargan desde PostgreSQL.  
Recuperación: automático al reiniciar Redis.

DB-2 Cola reintentos S4: notificaciones pendientes  
a S4 se pierden.  
Recuperación: aceptable en MVP — S4 recibe la  
notificación en el siguiente ciclo.
```
**Resolución:**
```
Reinicio estándar Fase 2:  
docker restart tecnimotos-redis  
Esperar 15 segundos.  
docker exec tecnimotos-redis redis-cli ping  
→ verificar PONG.

Verificar consumer groups tras reinicio:  
docker exec tecnimotos-redis redis-cli  
XINFO GROUPS repuesto  
→ deben aparecer todos los grupos declarados  
en 03-diseno-sistema §7.6 (5 consumer groups).  
Si un grupo desapareció: el worker del api-server  
lo recrea automáticamente al iniciar. Reiniciar  
api-server si no ocurre en 2 minutos.

Si Redis no levanta tras reinicio:  
→ activar fallback (Tramo 2 §4.3).  
→ sistema opera sin EDA — solo operaciones  
síncronas funcionan.  
→ notificar a Elena: notificaciones automáticas  
desactivadas temporalmente.
```
**Criterio de éxito:** `redis-cli ping` responde PONG ·
consumer groups verificados · primer evento procesado
correctamente por cada grupo · notificaciones vuelven
a enviarse.

**Nota de referencia cruzada:** este runbook menciona
los 5 consumer groups que `03-diseno-sistema` §7.6 ya
indexó — no se reproduce la tabla aquí, solo se
referencia para que el agente sepa dónde verificar
la lista completa si necesita el detalle exacto por
tópico.

---

### 6.4 Acumulación de eventos PENDIENTE en outbox

**Síntoma:** alerta de Dead Letter o acumulación en
`outbox_events` · eventos `PENDIENTE` acumulándose sin
procesarse · operaciones completadas sin efectos
secundarios (stock no descontado, notificaciones no
enviadas).

**Causa raíz típica:** Redis caído/intermitente ·
worker del outbox detenido o en loop de error.

**Diagnóstico en orden:**
```bash
# 1. Verificar Redis
docker exec tecnimotos-redis redis-cli ping
# Si no responde → ir a runbook §6.3 primero

# 2. Contar eventos pendientes
docker exec tecnimotos-postgres \
  psql -U postgres -d tecnimotos \
  -c "SELECT COUNT(*) FROM outbox_events \
      WHERE estado = 'PENDIENTE';"

# 3. Verificar worker
docker logs tecnimotos-api --tail=50 | grep "outbox"
# Errores repetidos → worker en loop de retry
# Sin logs en > 5 min → worker detenido

# 4. Identificar eventos acumulados por tipo
docker exec tecnimotos-postgres \
  psql -U postgres -d tecnimotos \
  -c "SELECT tipo_evento, COUNT(*) \
      FROM outbox_events \
      WHERE estado = 'PENDIENTE' \
      GROUP BY tipo_evento \
      ORDER BY COUNT(*) DESC LIMIT 10;"
```

**Resolución:**
```
Redis estaba caído y ya volvió:  
El worker retoma automáticamente. Esperar 2 min  
y verificar que el COUNT de PENDIENTE baja.  
Si no baja: docker restart tecnimotos-api

Worker en loop de error:  
docker exec tecnimotos-postgres  
psql -U postgres -d tecnimotos  
-c "SELECT id, tipo_evento, intentos,  
ultimo_error, creado_en  
FROM outbox_events  
WHERE estado = 'PENDIENTE' AND intentos >= 3  
ORDER BY creado_en ASC LIMIT 5;"

Si hay eventos con intentos >= 3:  
UPDATE outbox_events SET estado = 'FALLIDO'  
WHERE intentos >= 3;  
→ investigar ultimo_error  
→ crear issue en GitHub con payload y error

Verificación final:  
SELECT COUNT(*) FROM outbox_events  
WHERE estado = 'PENDIENTE';  
→ debe ser 0 o reducirse progresivamente.
```
**Criterio de éxito:** `outbox_events` PENDIENTE en 0 ·
worker procesando normalmente · efectos secundarios
verificados para al menos el último evento procesado.

---

### 6.5 Cola de notificaciones saturada

**Síntoma:** alerta de cola saturada en Redis DB-2 ·
notificaciones a S4 no llegan · WhatsApp y SMS fallan
simultáneamente.

**Causa raíz típica:** WhatsApp Business API caída o
con rate limit · Twilio/AWS SNS con error · fallo de
red saliente.

**Diagnóstico en orden:**
```bash
# 1. Estado de proveedores externos
#    - WhatsApp Business API: status page del BSP
#    - Twilio: https://status.twilio.com
#    - ambos caídos → fallo de red saliente o
#      incidente externo masivo

# 2. Tamaño de la cola
docker exec tecnimotos-redis redis-cli \
  -n 2 XLEN notificaciones-retry
# > 100 mensajes → cola saturada

# 3. Logs del notification-service
docker logs tecnimotos-api --tail=100 | grep "notification"
# "429 Too Many Requests" → rate limit
# "Connection timeout" → fallo de red saliente
# "Invalid token" → credencial expirada → ir a §7.1
```

**Resolución:**
```
Fallo externo del proveedor:  
No hay acción en el servidor — esperar  
recuperación del proveedor.  
Notificar a Elena por WhatsApp personal (no  
Business API):  
"Las notificaciones automáticas del sistema están  
suspendidas temporalmente. Los clientes que esperan  
respuesta deben ser contactados manualmente hasta  
nuevo aviso."  
La cola persiste — el worker procesa al volver  
el proveedor.

Rate limit de WhatsApp (429):  
El worker ya tiene backoff exponencial.  
No intervenir.  
Si la cola supera 500 mensajes:  
docker exec tecnimotos-postgres  
psql -U postgres -d tecnimotos  
-c "DELETE FROM outbox_events  
WHERE tipo_evento IN  
('stock.bajo_umbral', 'pedido.visto')  
AND estado = 'PENDIENTE';"  
(descarta notificaciones informativas, conserva  
las críticas: moto lista, cobro confirmado)

Credencial expirada:  
→ ir a runbook §7.1 rotación de secretos.  
Tras rotar: docker restart tecnimotos-api
```
**Criterio de éxito:** cola en Redis DB-2 procesándose
o vaciada · al menos una notificación de prueba
entregada vía WhatsApp · alerta cerrada.

---

### 6.6 Dead Letter — eventos sin ACK tras 3 reintentos

**Síntoma:** alerta de Dead Letter activa · eventos en
tópico `dead-letter` de Redis Streams · operaciones
completadas sin efectos secundarios correspondientes.

**Diagnóstico en orden:**
```bash
# 1. Leer eventos en dead-letter
docker exec tecnimotos-redis redis-cli \
  XRANGE dead-letter - + COUNT 10

# 2. Cruzar con outbox_events
psql -c "SELECT id, tipo_evento, intentos, \
  ultimo_error, creado_en FROM outbox_events \
  WHERE estado = 'FALLIDO' \
  ORDER BY creado_en DESC LIMIT 10;"

# 3. Clasificar:
#    - Evento crítico de negocio (pedido.confirmado ·
#      cobro.confirmado · orden_trabajo.cerrada)
#      → intervención inmediata
#    - Evento informativo (stock.bajo_umbral ·
#      margen.alerta) → puede descartarse
```

**Resolución según clasificación:**
```
Evento crítico de negocio en dead-letter:

1. Identificar consumer group que falló:  
    XINFO GROUPS [topico]  
    Ver campo "pel" (pending entries) por grupo.
2. Reintentar manualmente:  
    XCLAIM [topico] [grupo] admin 0 [message-id]
3. Si falla nuevamente: bug en el handler.  
    Crear issue urgente en GitHub con payload completo.  
    Aplicar el efecto manualmente en BD para no  
    bloquear la operación de Elena. Ejemplo —  
    cobro.confirmado sin stock descontado:  
    UPDATE stock_repuesto  
    SET cantidad_disponible = cantidad_disponible - [cantidad]  
    WHERE repuesto_id = [id];  
    Registrar en audit trail manual.

Evento informativo en dead-letter:  
XDEL dead-letter [message-id]  
→ descartado limpiamente.  
Registrar en issue de GitHub para investigar  
en el siguiente sprint
```
**Criterio de éxito:** tópico `dead-letter` vacío ·
efectos de negocio de eventos críticos verificados en
PostgreSQL · issue creado en GitHub para cada evento
fallido.

---

### 6.7 E2E nightly fallo — respuesta nocturna

**Síntoma:** alerta de GitHub Actions synthetic
fallida entre 00:00 y 08:00 · workflow `e2e-nightly.yml`
con resultado FAIL.

**Principio de respuesta nocturna:** un fallo del E2E
nightly NO requiere despertar a Sant si el sistema está
operativo para usuarios reales. Evaluar severidad antes
de actuar.

**Diagnóstico en orden:**
```
1. curl https://[dominio]/health  
    Si responde 200 → sistema funciona para usuarios  
    reales, el fallo es del test, no del sistema.
2. Revisar log del workflow: GitHub → Actions →  
    e2e-nightly → último run.
3. Clasificar:
    - fallo de infraestructura de test (staging BD sin  
        datos, seed no aplicado, variable faltante)
    - fallo de regresión (el sistema cambió y el test  
        detectó comportamiento incorrecto)
    - fallo flaky (test inestable por timing o datos  
        variables)
```
**Resolución según clasificación:**
```
Sistema operativo + fallo de infraestructura de test:  
→ NO despertar. Registrar:  
"E2E nightly falló por infraestructura de test.  
Sistema prod OK. Se investiga en horario laboral."  
→ investigar al despertar. Ver runbook §6.9 si el  
staging tiene la BD corrupta.

Sistema operativo + fallo de regresión:  
→ evaluar si afecta a usuarios reales ahora.  
→ si afecta: despertar y aplicar hotfix o rollback  
según §6.1.  
→ si no afecta en prod: registrar y atender en  
horario laboral.

Sistema NO operativo:  
→ ir a runbook §6.1 inmediatamente. El E2E nightly  
detectó la caída antes de que Elena llegue.

Fallo flaky confirmado:  
→ marcar el test como xfail en pytest hasta  
estabilizarlo. No bloquear el pipeline por un  
test inestable conocido.
```
**Criterio de éxito:** causa identificada y clasificada
· acción tomada según clasificación · próximo E2E
nightly pasa o queda documentado como issue con
prioridad asignada.

---

### 6.8 Rollback con transacciones confirmadas en ventana

**Síntoma:** deploy fallido que requiere rollback, pero
entre el deploy y el rollback hubo transacciones reales
de usuarios.

**Riesgo real:** el rollback revierte código pero no
datos. Si el schema cambió en el deploy fallido, el
rollback puede dejar código antiguo con datos nuevos —
inconsistencia.

**Diagnóstico antes de ejecutar el rollback:**
```bash
# 1. ¿Hubo migración de Alembic en el deploy?
git show [commit-del-deploy]:alembic/versions/
# Hay migración nueva → riesgo alto
# No hay migración → rollback seguro

# 2. Si hubo migración, identificar transacciones
#    en la ventana de fallo:
psql -c "SELECT COUNT(*) FROM pedido \
  WHERE creado_en > '[timestamp-del-deploy]';"
psql -c "SELECT COUNT(*) FROM orden_trabajo \
  WHERE creado_en > '[timestamp-del-deploy]';"
psql -c "SELECT COUNT(*) FROM comprobante \
  WHERE creado_en > '[timestamp-del-deploy]';"
```

**Resolución según escenario:**
```
Sin migración de BD — rollback limpio:  
Fase 1: railway rollback [deployment-id]  
Fase 2: docker pull [imagen-version-anterior]  
docker compose up -d  
→ verificar /health · verificar operación con Elena.

Con migración + transacciones en ventana:  
→ NO ejecutar rollback automático del código.  
→ evaluar si el código nuevo puede estabilizarse  
con hotfix:  
- identificar el error específico en logs  
- bug menor: aplicar hotfix y redesplegar  
- irrecuperable:  
1. activar fallback (Tramo 2 §4.3) inmediatamente  
2. exportar datos de la ventana:  
pg_dump --table=pedido --table=orden_trabajo  
--table=comprobante  
--where="creado_en > '[timestamp]'"  
tecnimotos > ventana_datos.sql  
3. alembic downgrade -1  
4. restaurar código anterior  
5. reimportar datos de la ventana si son  
compatibles  
6. verificar integridad con Elena

Con migración + sin transacciones en ventana:  
→ rollback seguro: revertir código primero, luego  
alembic downgrade -1.  
→ verificar que el schema anterior es coherente  
con el código anterior.
```
**Criterio de éxito:** sistema operativo en versión
estable · integridad de datos verificada · Elena
confirma operación normal · transacciones de la
ventana preservadas o documentadas con impacto exacto.

---

### 6.9 Restauración de seed en staging corrupto

**Síntoma:** E2E nightly falla por datos incoherentes
en staging · seed corrupto o desactualizado.

**Cuándo ocurre:** prueba dejó datos sucios · migración
parcial falló en staging · modificación manual no
documentada.

**Procedimiento de restauración:**
```bash
# 1. Confirmar que es staging — NUNCA producción
echo $ENVIRONMENT
# Debe responder "staging". Si responde "production":
# DETENER INMEDIATAMENTE.

# 2. Derribar BD de staging
psql -U postgres -c \
  "DROP DATABASE IF EXISTS tecnimotos_staging;"
psql -U postgres -c \
  "CREATE DATABASE tecnimotos_staging;"

# 3. Migraciones desde cero
alembic upgrade head

# 4. Aplicar seed del nivel adecuado
#    Nivel 1 (5 registros)  → smoke tests rápidos
#    Nivel 2 (25 registros) → E2E nightly
#    Nivel 3 (55 registros) → validación con Elena
python scripts/seed.py --level=2 --env=staging

# 5. Verificar integridad del seed
python scripts/verify_seed.py --env=staging
# Debe reportar PASS en todas las tablas
# (script pendiente — ver CT-11-02, Tramo 6 §10)

# 6. Relanzar E2E nightly
gh workflow run e2e-nightly.yml --ref main

# 7. Si pasa: staging restaurado.
#    Si falla de nuevo: el problema no era el seed
#    → investigar el error específico del test.
```

**Criterio de éxito:** E2E nightly pasa en staging
restaurado · `verify_seed.py` reporta PASS · staging
disponible para próximas pruebas.

---
## 7. Runbooks de seguridad

> Fuente: `11 plan-operacion` §6.1 a §6.6.
> Procedimientos con consecuencias legales o
> contractuales si no se ejecutan correctamente.
> Cada uno con plazo máximo declarado — no opcional.

---

### 7.1 Rotación de secretos cada 90 días

**Plazo máximo:** 90 días desde la última rotación.
Un secreto con más de 90 días sin rotar es un
incidente de seguridad latente.

**Inventario de secretos:**
```
SECRETO UBICACION ROTACION  
JWT private key RS256 Railway/Hetzner/Key Vault 90 días  
JWT public key RS256 mismo origen que private key con private key  
DATABASE_URL Railway/Hetzner/Key Vault 90 días  
Redis password Railway/Hetzner env 90 días  
WhatsApp BSP API key Railway/Key Vault 90 días o  
según proveedor  
Twilio API key Railway/Key Vault 90 días  
SUNAT API credentials Railway/Key Vault según SUNAT  
(típ. anual)  
Fernet encryption key Railway/Key Vault 90 días —  
ver nota crítica  
Backblaze B2 API key Railway/san-aorus cifrado local 90 días
```
**Nota crítica — Fernet key:** rotarla requiere
re-cifrar todos los datos sensibles en PostgreSQL
cifrados con la key anterior. No es solo cambio de
variable. Requiere ventana de mantenimiento fuera de
horario comercial con la BD en modo solo lectura
temporal.

**Procedimiento de rotación estándar (no Fernet):**
```bash
# 1. Generar nuevo valor
# JWT RS256:
openssl genrsa -out jwt_private.pem 2048
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem
# Passwords y API keys:
openssl rand -base64 32

# 2. Actualizar en la fuente de secretos
# Fase 1: railway variables set SECRET_NAME=nuevo_valor
# Fase 2: editar .env en servidor vía SSH —
#         NUNCA editar desde san-aorus y subir por
#         rsync (riesgo de exposición en tránsito)
# Fase 3: az keyvault secret set \
#         --vault-name tecnimotos-kv \
#         --name SECRET_NAME --value nuevo_valor

# 3. Redesplegar para cargar el nuevo secreto
# Fase 1: railway redeploy
# Fase 2: docker compose up -d --force-recreate api
# Fase 3: az containerapp update ...

# 4. Verificar arranque correcto
curl https://[dominio]/health  # → 200
# intentar login con cuenta de prueba

# 5. Invalidar secreto anterior
# JWT: refresh token rotation ya invalida tokens
#      anteriores al rotar la key. Notificar a Elena:
#      "El sistema requiere que inicies sesión
#      nuevamente hoy."
# DATABASE_URL: cambiar password en PostgreSQL
#      después de actualizar la variable:
#      ALTER USER tecnimotos_user PASSWORD 'nuevo';
# Resto: queda inactivo al no estar en uso

# 6. Registrar rotación en checklist trimestral
#    (Tramo 5 §8.3) con fecha y tipo — NUNCA el valor
```

**Procedimiento de rotación Fernet — ventana de
mantenimiento:**
```bash
# 1. Notificar a Elena la noche anterior:
#    "El sistema estará en mantenimiento mañana
#    de [hora] a [hora]. Aproximadamente 30-60 min."

# 2. Fuera de horario comercial — modo solo lectura:
railway variables set READ_ONLY_MODE=true
docker compose restart api  # o equivalente

# 3. Script de re-cifrado — primero en seco:
python scripts/reencrypt_fernet.py \
  --old-key $FERNET_KEY_OLD \
  --new-key $FERNET_KEY_NEW \
  --dry-run
# (script pendiente — ver CT-11-01, Tramo 6 §10)

# 4. Verificar dry-run sin errores. Ejecutar en real:
python scripts/reencrypt_fernet.py \
  --old-key $FERNET_KEY_OLD \
  --new-key $FERNET_KEY_NEW

# 5. Actualizar FERNET_KEY en la fuente de secretos

# 6. Desactivar modo solo lectura y redesplegar

# 7. Verificar que datos cifrados son legibles:
#    - login de Elena exitoso
#    - precio de costo visible para ADMINISTRADOR
#      en al menos un repuesto
#    - descuento aplicado legible en pedido histórico

# 8. Registrar en checklist trimestral (Tramo 5 §8.3)
```

---

### 7.2 Secreto detectado en historial Git

**Severidad:** Crítica — el secreto se considera
comprometido desde el momento del commit, no desde
el descubrimiento.

**Acción inmediata — antes de limpiar el historial:**
```
1. Revocar o rotar el secreto expuesto AHORA. No  
    esperar a limpiar el historial. → seguir §7.1  
    para el tipo de secreto afectado.
2. Repositorio público: asumir que fue visto.  
    Repositorio privado: rotar igual — bots indexan  
    repos privados que alguna vez fueron públicos.
3. Si el secreto es de proveedor externo (Twilio,  
    WhatsApp BSP): contactar al proveedor para  
    invalidar la credencial desde su lado también.
```
**Limpieza del historial con git filter-repo:**
```bash
# 1. Instalar si no está disponible
pip install git-filter-repo

# 2. Backup antes de operar
cp -r [repo] [repo]-backup-$(date +%Y%m%d)

# 3. Identificar archivo o string con el secreto
git log --all --full-history -- [archivo]
git log -S "[fragmento-del-secreto]" --source --all

# 4. Eliminar del historial completo
# Opción A — eliminar archivo completo:
git filter-repo --path [archivo] --invert-paths
# Opción B — reemplazar el valor específico:
git filter-repo --replace-text <(echo \
  "[secreto-expuesto]==>REMOVED")

# 5. Verificar que no aparece
git log --all -S "[secreto-expuesto]"
# → debe retornar vacío

# 6. Forzar push al remoto
git push origin --force --all
git push origin --force --tags

# 7. Si hay colaboradores o forks: notificarles
#    que deben clonar nuevamente

# 8. Revocar y regenerar el GitHub token de Sant
#    si el secreto expuesto era ese token

# 9. Registrar en post-mortem: qué secreto · cuándo
#    fue committeado · cuándo detectado · acciones ·
#    tiempo de exposición
```

**Criterio de éxito:** secreto rotado y activo con
nuevo valor · historial Git limpio verificado ·
`git log -S` retorna vacío · remoto actualizado con
force push.

---

### 7.3 Derecho al olvido — anonimización en 72h

**Contexto legal:** Ley 29733 Art. 18 — plazo máximo
de ejecución 72 horas desde recepción de la solicitud.

**Canal de recepción:** email de contacto · WhatsApp
de tienda · presencial. Toda solicitud llega a Sant
el mismo día de recepción.

**Qué se anonimiza vs qué se conserva:**
```
ANONIMIZAR:  
nombre → CLIENTE_ELIMINADO_[id]  
telefono → 0000000000  
direccion → DIRECCIÓN_ELIMINADA  
dni → 00000000  
foto_perfil → eliminar físicamente del storage

CONSERVAR (con cliente anonimizado):  
historial de pedidos — obligación contable RNL-03  
comprobantes emitidos — obligación SUNAT RNL-01  
logs de auditoría — retención 5 años, ID anonimizado
```
**Procedimiento de anonimización:**
```sql
-- 1. Verificar identidad del solicitante y registrar
--    la solicitud con fecha/hora de recepción —
--    el plazo de 72h empieza aquí.

-- 2. Identificar el cliente
SELECT id, nombre, telefono, dni FROM cliente
WHERE telefono = '[telefono-solicitante]'
   OR dni = '[dni-solicitante]';

-- 3. Ejecutar anonimización en transacción
BEGIN;
UPDATE cliente SET
  nombre = 'CLIENTE_ELIMINADO_' || id,
  telefono = '0000000000',
  direccion = 'DIRECCIÓN_ELIMINADA',
  dni = '00000000',
  email = NULL,
  foto_url = NULL,
  anonimizado = true,
  anonimizado_en = NOW(),
  anonimizado_por = '[sant-user-id]'
WHERE id = [cliente_id];

-- verificar que pedidos conservan el FK:
SELECT COUNT(*) FROM pedido WHERE cliente_id = [cliente_id];
COMMIT;
```

```bash
# 4. Eliminar foto de perfil si existe
rclone delete backblaze:tecnimotos-assets/clientes/[cliente_id]/
```
```sql
-- 5. Verificar anonimización
SELECT nombre, telefono, dni, email
FROM cliente WHERE id = [cliente_id];
-- todos los campos deben mostrar valores anonimizados
```

```
6. Notificar al solicitante por el mismo canal:  
    "Sus datos personales han sido eliminados del  
    sistema. Los registros contables asociados se  
    conservan por obligación legal sin datos  
    identificatorios."
7. Registrar en audit trail (categoría Datos  
    personales — ver 07-criterios-seguridad-ejecutables  
    Tramo 5 §7.1).
```
**Criterio de éxito:** datos PII anonimizados y
verificados · foto eliminada · notificación enviada ·
registro en audit trail · todo dentro de 72 horas.

---

### 7.4 Respuesta ante brecha — notificación ANPDP 72h

**Contexto legal:** Ley 29733 Art. 30 y DS 003-2013-JUS
— plazo máximo de notificación a la ANPDP: 72 horas
desde que se toma conocimiento del incidente.

**Definición de brecha:** acceso no autorizado ·
divulgación · alteración · destrucción de datos
personales de clientes.

**Paso 0 — Contención inmediata:**
```
1. Aislar el vector de ataque:
    - credencial comprometida → revocar de inmediato  
        (§7.1)
    - endpoint explotado → modo mantenimiento:  
        railway variables set MAINTENANCE=true
    - acceso no autorizado activo → revocar todos los  
        tokens JWT cambiando la JWT private key (§7.1)
2. NO eliminar evidencia — no borrar logs, no  
    reiniciar servicios antes de capturar el estado.  
    Exportar logs del período sospechoso (ver §7.5).
3. Registrar timestamp exacto del descubrimiento —  
    el plazo de 72h empieza aquí.
```
**Evaluación del alcance:**
```sql
SELECT c.id, c.nombre, c.telefono, c.dni
FROM cliente c
JOIN pedido p ON p.cliente_id = c.id
WHERE p.creado_en BETWEEN
  '[inicio-ventana-brecha]' AND '[fin-ventana-brecha]';
```

```
Identificar el vector: revisar logs de acceso del  
período (§7.5) · buscar IPs/user agents anómalos ·  
verificar acceso con credenciales válidas en horario  
o volumen inusual.

Cuantificar: número de registros afectados · tipos  
de datos expuestos · si fueron leídos, modificados  
o eliminados.
```
**Notificación a la ANPDP:**
```
Plazo: 72 horas desde el descubrimiento.  
Canal: portal web ANPDP o formulario oficial —  
verificar URL vigente al momento del incidente.

Información requerida:

1. Identificación del responsable del banco de datos  
    (razón social, RUC, nombre del registro, número  
    de registro ANPDP).
2. Descripción del incidente (fecha/hora de  
    descubrimiento, naturaleza, categorías de datos  
    afectados, número aproximado de titulares,  
    consecuencias probables).
3. Medidas adoptadas (contención ejecutada, medidas  
    correctivas en curso).
4. Datos de contacto del responsable.
```
**Notificación a los titulares afectados:**
```
Si los datos expuestos incluyen PII directa:

"Estimado [nombre], le informamos que hemos detectado  
un incidente de seguridad que pudo haber afectado sus  
datos personales registrados en Tecnimotos Santi.  
Hemos tomado medidas inmediatas para contener el  
incidente y mejorar nuestros controles de seguridad.  
Si tiene preguntas, contáctenos en [contacto]."

No mencionar detalles técnicos del vector ni datos  
que puedan ampliar el daño.
```
**Criterio de éxito:** contención ejecutada · evidencia
preservada · notificación ANPDP enviada dentro de 72h
con acuse de recibo · titulares notificados ·
post-mortem documentado en `docs/postmortems/`.

---

### 7.5 Consulta de audit trail para investigación

> **Mecanismo confirmado — OBS-EP-005 cerrada en este
> tramo:** el acceso de lectura a audit trail es
> EXCLUSIVAMENTE vía SSH directo a PostgreSQL desde
> `san-aorus` o `tecnimoto` — ambos nodos Tailscale
> con Ed25519 + MFA. NUNCA se expone un endpoint HTTP
> de consulta de audit trail, bajo ninguna condición
> ni rol, ni siquiera restringido a `SUPERADMIN`. La
> superficie HTTP queda descartada por diseño para
> este dato — no por insuficiencia de RBAC, sino
> porque SSH+Tailscale+Ed25519 es estructuralmente más
> resistente a interceptación o captura que cualquier
> sesión autenticada por JWT sobre navegador.

**Cuándo se usa:** investigación de incidente de
seguridad · solicitud de derecho al olvido que
requiere verificar qué datos existen · auditoría
interna · soporte a Elena sobre una operación que no
recuerda haber ejecutado.

**Tablas de audit trail disponibles:**
```
auditoria — operaciones críticas de negocio  
(pedidos, cobros, comprobantes,  
stock) — retención 5 años  
auditoria_stock — movimientos de stock —  
retención 5 años  
auditoria_seguridad — autenticación, acceso a datos  
sensibles, cambios de rol —  
retención 5 años
```
**Consultas por caso de uso:**
```sql
-- CASO 1 — quién accedió a datos de un cliente en
-- un período
SELECT a.ejecutado_en, a.ejecutado_por, a.accion,
       a.detalle, u.nombre as usuario
FROM auditoria a
JOIN usuario u ON u.id = a.ejecutado_por
WHERE a.entidad = 'cliente'
  AND a.entidad_id = [cliente_id]
  AND a.ejecutado_en BETWEEN '[fecha_inicio]' AND '[fecha_fin]'
ORDER BY a.ejecutado_en DESC;

-- CASO 2 — todas las operaciones de un usuario en
-- un período (comportamiento anómalo)
SELECT a.ejecutado_en, a.accion, a.entidad,
       a.entidad_id, a.detalle
FROM auditoria a
WHERE a.ejecutado_por = [usuario_id]
  AND a.ejecutado_en BETWEEN '[fecha_inicio]' AND '[fecha_fin]'
ORDER BY a.ejecutado_en DESC;

-- CASO 3 — eventos de autenticación fallidos
-- (detección de fuerza bruta)
SELECT as_.ocurrido_en, as_.ip_origen,
       as_.user_agent, as_.detalle
FROM auditoria_seguridad as_
WHERE as_.evento = 'LOGIN_FALLIDO'
  AND as_.ocurrido_en > NOW() - INTERVAL '24h'
ORDER BY as_.ocurrido_en DESC;

-- CASO 4 — movimientos de stock en un período
-- (reconciliación o faltante)
SELECT ast.registrado_en, ast.tipo_movimiento,
       ast.cantidad, ast.referencia,
       ast.ejecutado_por, r.nombre as repuesto
FROM auditoria_stock ast
JOIN repuesto r ON r.id = ast.repuesto_id
WHERE ast.repuesto_id = [repuesto_id]
  AND ast.registrado_en BETWEEN '[fecha_inicio]' AND '[fecha_fin]'
ORDER BY ast.registrado_en DESC;

-- CASO 5 — exportar audit trail completo para
-- notificación ANPDP (período de brecha)
COPY (
  SELECT a.ejecutado_en, u.nombre, a.accion,
         a.entidad, a.entidad_id, a.detalle
  FROM auditoria a
  JOIN usuario u ON u.id = a.ejecutado_por
  WHERE a.ejecutado_en BETWEEN '[inicio_brecha]' AND '[fin_brecha]'
  ORDER BY a.ejecutado_en ASC
) TO '/tmp/audit_export.csv' WITH CSV HEADER;
```

**Restricción de acceso — vinculante:** estas consultas
se ejecutan exclusivamente desde una sesión SSH sobre
`san-aorus` o `tecnimoto` vía Tailscale. El agente que
proponga, durante la construcción del sistema, un
endpoint HTTP `/v1/admin/audit-trail` o equivalente —
incluso protegido por RBAC + MFA — viola este criterio
y debe detenerse.

---

### 7.6 Canal de contingencia alertas Elena

**Contexto:** si Slack falla · Sant no responde · o el
sistema de mensajería del negocio (WhatsApp Business)
está caído, Elena necesita un canal para reportar
síntomas y recibir instrucciones.

**Jerarquía de canales Sant ↔ Elena:**
```
1° WhatsApp personal de Sant — siempre disponible,  
canal primario  
2° Llamada telefónica directa — si WhatsApp no  
entrega en 5 min  
3° SMS al número de Sant — si la llamada no  
entra (zona sin señal)  
4° Mensaje a familiar de Sant — si Sant es  
presente en tienda inubicable > 30 min
```
**Lo que Elena hace cuando el sistema no funciona:**
```
Síntoma: "El sistema no carga" · "Sale un error raro"  
· "Las notificaciones no llegan" ·  
"No puedo iniciar sesión"

1. Tomar foto o anotar el mensaje de error exacto.
2. Enviar a Sant por WhatsApp personal:  
    "[hora] — El sistema [descripción del síntoma].  
    [foto del error si hay]"
3. Esperar respuesta de Sant máximo 15 minutos en  
    horario laboral.
4. Si no hay respuesta en 15 min: llamar al número  
    de Sant.
5. Mientras espera: continuar operación en papel  
    (fallback, Tramo 2 §4.3). No reiniciar nada.  
    No entrar por otra URL. No pedir ayuda técnica  
    a terceros.
```
**Lo que Sant hace cuando Elena reporta:**
```
1. Confirmar recepción inmediatamente:  
    "Recibido, revisando ahora." (detiene el ciclo  
    de llamadas de Elena)
2. Diagnosticar con los runbooks §6.1 a §6.9  
    (Tramo 3 de este archivo) según el síntoma.
3. Dar ETA en máximo 10 minutos:  
    "El sistema vuelve en [tiempo estimado]." o  
    "Va a tardar más. Activa el modo papel."
4. Notificar cuando el sistema esté listo:  
    "El sistema ya funciona. Puedes continuar."
```
**Canal de contingencia para alertas del sistema
cuando Slack falla:**
```
Alertas de respaldo configuradas en:

- Email de Sant: alerta de GitHub Actions si el  
    E2E nightly falla.
- UptimeRobot (plan gratuito) o similar: monitor  
    externo de /health que envía SMS a Sant si el  
    endpoint no responde. Independiente del stack  
    interno — funciona aunque el sistema completo  
    caiga. (pendiente de configurar — ver CT-11-05,  
    Tramo 6 §10)

Configuración:  
Monitor type: HTTP(s)  
URL: https://[dominio]/health  
Check interval: 5 minutes  
Alert contacts: SMS a número de Sant
```
**Criterio de canal operativo:** el canal de
contingencia está operativo cuando Sant recibe una
alerta SMS de prueba desde el monitor externo —
verificar en checklist trimestral (Tramo 5 §8.3).

---
## 8. Checklists operativos

> Fuente: `11 plan-operacion` §7.1 a §7.3.
> Un checklist no es una lista de buenas intenciones —
> es verificación con resultado binario: pasa o no
> pasa. Ningún ítem es opcional dentro de su checklist.

---

### 8.1 Checklist pre-deploy

> Se ejecuta antes de cada deploy a producción. Un
> deploy que no pasa este checklist no sale — sin
> excepción.

**Infraestructura y secretos**
```
☐ Terraform plan ejecutado sin drift.  
☐ Todos los secretos cargados en la fuente correcta  
(Railway env / Hetzner .env / Azure Key Vault) —  
ningún secreto en el repositorio.  
☐ Key Vault o equivalente accesible desde el  
api-server — prueba de lectura de secreto no sensible.  
☐ Dominio apuntando correctamente — nslookup [dominio]  
retorna la IP esperada.  
☐ TLS activo — https://[dominio] sin advertencia de  
certificado. Validez > 30 días.
```
**Base de datos**
```
☐ Al menos un backup exitoso en las últimas 24h.  
☐ Migraciones Alembic en estado correcto:  
alembic current → revisión head, sin pending.  
☐ PITR probado en staging en los últimos 90 días —  
ver registro en checklist trimestral §8.3.  
☐ Seed de datos iniciales aplicado en staging y  
verificado — verify_seed.py reporta PASS  
(script pendiente — ver CT-11-02, Tramo 6 §10)
```
**Despliegue**
```
☐ Pipeline CI/CD verde en el último commit de main —  
lint · tests · build · security scan.  
☐ E2E nightly pasó en las últimas 48 horas en staging.  
☐ Rollback probado en staging — revertir a la versión  
anterior funciona en menos de 5 minutos.  
☐ Feature flags de módulos no listos desactivados en  
producción — verificar en parametros_sistema.  
☐ Si el deploy incluye migración de Alembic:  
☐ Migración es expand-only o tiene downgrade  
documentado.  
☐ Migración probada en staging con seed nivel 3.  
☐ Procedimiento de rollback con transacciones  
(Tramo 3 §6.8) revisado y listo.
```
**Seguridad**
```
☐ Security scan sin vulnerabilidades críticas o altas  
sin mitigación documentada.  
☐ MFA activo en cuenta Railway de Sant — verificar en  
Railway Dashboard → Account → Security antes de cada  
deploy a producción. Una cuenta sin MFA expone todas  
las variables de entorno del sistema, incluyendo  
Fernet key, DATABASE_URL y tokens de APIs externas.  
☐ OWASP dependency check sin CVE críticos.  
☐ Sin secretos detectados en el diff del deploy —  
secret scanning del pipeline en verde.  
☐ Rate limiting activo en endpoints públicos —  
verificar con prueba manual de 20 requests seguidos  
al mismo endpoint.
```
**Legal — precondición de deploy, no técnica**
```
☐ Número de registro ANPDP del banco de datos de  
clientes obtenido y documentado:  
Nro. de registro: _______________  
Fecha de registro: ______________  
→ SIN este número el sistema no puede recibir datos  
personales de clientes. Es precondición legal de  
deploy, no pendiente post-launch.

☐ Política de privacidad publicada en [dominio]/privacidad:  
☐ identificación del responsable del banco de datos  
☐ finalidad del tratamiento de datos  
☐ derechos ARCO con canal de ejercicio  
☐ plazo de retención por tipo de dato  
☐ transferencia a terceros (SUNAT, WhatsApp BSP,  
Twilio) declarada

☐ Consentimiento explícito implementado en el flujo  
de registro de cliente — checkbox no premarcado con  
link a política de privacidad.
```
**Observabilidad**
```
☐ Logs JSON estructurados visibles en el sistema de  
agregación — enviar request de prueba y verificar.  
☐ Métricas de las cuatro señales doradas visibles —  
/metrics responde con datos.  
☐ Al menos una alerta activa y probada en staging.  
☐ Runbooks vinculados a cada alerta activa —  
verificar que el link en la regla de Prometheus  
apunta al runbook correcto (Tramo 3 §6 o Tramo 4 §7  
de este archivo).  
☐ Monitor externo (UptimeRobot o equiv.) activo y  
enviando SMS de prueba a Sant  
(pendiente — ver CT-11-05, Tramo 6 §10).
```
**Validación final**
```
☐ Elena validó los flujos críticos en staging desde  
tecnimoto — ver Tramo 6 §9 de este archivo.  
☐ Sant ejecutó smoke test manual completo: login  
ADMINISTRADOR · búsqueda catálogo · consulta de  
stock · creación de pedido de prueba · apertura de  
orden_trabajo.  
☐ Fallback (Tramo 2 §4.3) comunicado a Elena — Elena  
sabe qué hacer si el sistema falla en los primeros  
días de producción.
```
---

### 8.2 Checklist diario

> Se ejecuta cada día hábil antes de las 08:00 — antes
> de que Elena llegue a la tienda. Tiempo estimado:
> 5 minutos. Si algún ítem falla: Sant resuelve o
> activa el fallback (Tramo 2 §4.3) antes de las 08:00.
```
VERIFICACIÓN DIARIA — [fecha]

Sistema  
☐ Health check verde: curl https://[dominio]/health → 200  
☐ Sin alertas críticas activas desde el día anterior.  
☐ Error rate últimas 8h < 0.5%.

Base de datos  
☐ Backup diario exitoso — verificar log del pipeline.  
Hora esperada: 02:00 UTC-5.  
Si falló: relanzar manualmente ahora y resolver  
antes del cierre del día.

Worker reset-precio  
☐ Workflow reset-precio.yml ejecutado exitosamente a  
las 05:00 UTC-5 — GitHub Actions → último run →  
success.  
Si falló:  
☐ revisar logs del workflow  
☐ ejecutar manualmente: gh workflow run reset-precio.yml  
☐ verificar que los precios de sesión en Redis DB-1  
fueron limpiados:  
docker exec tecnimotos-redis redis-cli -n 1 KEYS "precio:*"  
→ debe retornar vacío si el reset funcionó.

Outbox  
☐ Sin eventos acumulados:  
SELECT COUNT(*) FROM outbox_events WHERE estado = 'PENDIENTE';  
→ debe ser 0. Si hay pendientes: ver runbook Tramo 3 §6.4.  
☐ Sin eventos en dead-letter:  
docker exec tecnimotos-redis redis-cli XLEN dead-letter  
→ debe ser 0. Si hay eventos: ver runbook Tramo 3 §6.6.

Notificaciones  
☐ Cola de reintentos vacía:  
docker exec tecnimotos-redis redis-cli -n 2 XLEN notificaciones-retry  
→ si > 10 mensajes: ver runbook Tramo 3 §6.5.

Resultado: ☐ TODO OK — sistema listo para operación de Elena.  
☐ INCIDENCIA — [descripción y acción tomada]
```
---

### 8.3 Checklist trimestral

> Se ejecuta cada 90 días. Alineado con la rotación de
> secretos (Tramo 4 §7.1) y la verificación de
> restauración (Tramo 2 §5.5). Fecha base: primer día
> de operación en producción.
```
VERIFICACIÓN TRIMESTRAL — [fecha]  
Período cubierto: [fecha_inicio] a [fecha_fin]

Backups  
☐ Restauración desde backup probada en staging:  
Backup restaurado: [nombre del archivo]  
Hash verificado: [sha256]  
Fecha del backup: [fecha]  
Resultado: ☐ PASS ☐ FAIL  
Si FAIL: incidente Severidad 1 — resolver antes de continuar.

Secretos — Tramo 4 §7.1  
☐ JWT RS256 key pair rotado. Fecha: ____________  
☐ DATABASE_URL password rotado. Fecha: ____________  
☐ Redis password rotado. Fecha: ____________  
☐ WhatsApp BSP API key rotado. Fecha: ____________  
☐ Twilio API key rotado. Fecha: ____________  
☐ Backblaze B2 API key rotado. Fecha: ____________  
☐ Fernet key — evaluar si rotar este trimestre:  
☐ Rotar (requiere ventana de mantenimiento)  
☐ Postponer con justificación: __________  
☐ SUNAT credentials — verificar vigencia.  
Vencimiento declarado por SUNAT: ________

Seguridad  
☐ OWASP dependency check ejecutado — sin CVE críticos  
sin mitigación.  
☐ Revisión de usuarios activos:  
SELECT rol, COUNT(*) FROM usuario WHERE activo = true  
GROUP BY rol;  
→ usuarios sin actividad en 60+ días:  
SELECT nombre, ultimo_acceso FROM usuario  
WHERE ultimo_acceso < NOW() - INTERVAL '60d' AND activo = true;  
→ desactivar cuentas inactivas confirmadas con Elena.  
☐ Revisión de permisos RBAC — ningún usuario tiene  
permisos superiores a los necesarios para su rol  
actual (verificar contra 07-criterios-seguridad-  
ejecutables Tramo 2 §3.1 lista cerrada de roles).

Observabilidad  
☐ Revisión de alertas activas — eliminar alertas que  
no requirieron acción en los últimos 90 días.  
☐ Monitor externo (UptimeRobot) activo — SMS de  
prueba recibido por Sant.  
☐ Runbooks revisados — actualizar los que cambiaron  
por incidentes del trimestre.

Legal  
☐ Política de privacidad vigente y publicada — sin  
cambios normativos pendientes de incorporar.  
☐ Registro ANPDP vigente — sin renovación pendiente.  
☐ Logs de auditoría — verificar retención:  
SELECT MIN(ejecutado_en) FROM auditoria;  
→ si hay registros con más de 5 años: archivar  
antes de eliminar.

Operación  
☐ Post-mortems del trimestre revisados — acciones  
correctivas implementadas.  
☐ Runbooks actualizados tras cada incidente.  
☐ Capacidad de infraestructura revisada — crecimiento  
de BD, uso de object storage, costo mensual vs  
proyección.

Resultado: ☐ TODO OK  
☐ ÍTEMS PENDIENTES: [lista]  
☐ PRÓXIMA FECHA: [fecha + 90 días]
```
---
## 9. Criterios de adopción SE-07 y validación de Elena

> Fuente: `11 plan-operacion` §8 y §9.
> SE-07 es el criterio de éxito del MVP — el sistema
> se considera adoptado cuando estos umbrales se
> cumplen en operación real, no en demos ni staging.
> Período de medición: primeros 60 días con usuarios
> reales.

---

### 9.1 Umbrales de adopción — ejecutables
```
DIMENSION METRICA UMBRAL  
Uso de Elena pedidos en sistema vs pedidos totales ≥ 80% en semana 4  
Uso de Elena órdenes de trabajo en sistema ≥ 70% en semana 4  
Datos producidos ventas perdidas registradas ≥ 1/semana en  
semana 2-8  
Datos producidos LTV calculable S1 y S2 ≥ 10 clientes S1 +  
≥ 3 clientes S2 con  
> 1 pedido  
Estabilidad disponibilidad horario comercial ≥ 99% semanas 3-8  
Estabilidad error rate < 0.5% sostenido  
semanas 3-8  
Estabilidad latencia P95 en tecnimoto < 1s consulta  
stock/precio  
Segmento externo clientes S1/S2 vía sistema directo ≥ 3 clientes con  
≥ 1 pedido en 60d
```
**Fuente de datos de cada métrica:** tabla `pedido`
(usa el campo `origen_actor` confirmado aplicado vía
PCT-11-02 para distinguir `CLIENTE_EXTERNO`) ·
`orden_trabajo` · `pedido.motivo_cancelacion`
(confirmado aplicado vía PCT-11-01 para `SIN_STOCK`) ·
SLOs de disponibilidad/error rate/latencia desde el
stack de observabilidad.

### 9.2 Criterios de cancelación del MVP — condiciones de parada
```
CC-01: Elena rechaza usar el sistema después de  
2 semanas de operación real  
→ detener MVP · entrevista formal con Elena ·  
rediseño de flujos críticos

CC-02: más de 3 incidentes de pérdida de datos en 30 días  
→ detener MVP · auditoría de integridad completa ·  
corrección antes de continuar

CC-03: costo de infraestructura > S/500/mes sin volumen  
que lo justifique  
→ revisión de plan de infraestructura · migración  
a fase más económica

CC-04: ningún cliente externo usa el sistema en 60 días  
→ revisión de estrategia de adopción S1/S2

CC-05: incidente legal por datos personales no resuelto  
en 72h  
→ suspensión del sistema hasta resolución completa
```
**Verificación ejecutable:** si cualquiera de CC-01 a
CC-05 se activa antes de los 60 días, el agente
reporta la condición exacta con el mismo formato de
detención declarado en `09-criterios-avance-automatico`
— no continúa avanzando módulos hasta revisión formal.

### 9.3 Decisión sobre Fase 2 — al cumplir 60 días
```
SI SE-07 cumplido Y ningún CC activo:  
→ sistema adoptado.  
→ revisar condiciones de salida de Fase 1  
(Tramo 1 §3.2 de este archivo).  
→ si alguna se cumplió: iniciar planificación de  
migración a Fase 2 (Hetzner).  
→ si no: continuar en Fase 1, revisión en 60 días  
adicionales.

SI SE-07 no cumplido en dimensión "uso de Elena":  
→ investigar causa con Elena en sesión presencial.  
→ rediseñar flujos con fricción identificada.  
→ extender período de medición 30 días más.

SI SE-07 no cumplido en dimensión "datos producidos":  
→ revisar si los datos se registran correctamente o  
si Elena los registra fuera del sistema.  
→ ajustar flujos de captura.

SI algún CC activo:  
→ detener según la acción declarada en §9.2.  
→ no avanzar a Fase 2 hasta resolver.
```
---

### 9.4 Validación de Elena en tecnimoto — protocolo

> Referencia: `03-C` §8.3 protocolo base, extendido
> aquí con pasos concretos de despliegue.

**Modelo operativo de validación:**
```
san-aorus levanta el sistema en staging  
(Docker Compose local — Fase 0 — o Railway  
staging environment — pre-Fase 1)  
│  
│ Tailscale — red privada zero-trust  
│  
tecnimoto — Elena abre el navegador  
└── http://[ip-tailscale-san-aorus]:3000  
o https://[subdominio-staging].[dominio]  
└── Elena usa el sistema exactamente como en  
producción  
└── Sant observa desde san-aorus sin intervenir  
(VNC read-only o log de sesión)  
└── el comportamiento real de Elena es el criterio  
de aceptación — no su opinión sobre el diseño
```
**Regla de validación:** si Elena necesita más de 3
intentos para completar una acción crítica sin ayuda
de Sant, la funcionalidad NO pasa y requiere rediseño
antes de continuar.

**Flujos a validar — 4 sesiones, en orden:**
```
SESIÓN 1 — Autenticación y catálogo  
☐ login con MFA en < 60s desde tecnimoto — IC-06  
☐ buscar repuesto por modelo y año  
☐ buscar repuesto por código  
☐ verificar stock disponible de un repuesto  
☐ verificar precio de venta y de costo

SESIÓN 2 — Pedidos y comprobantes  
☐ crear pedido presencial para cliente S1 registrado  
☐ aplicar descuento a un ítem sin que el cliente lo vea  
☐ cerrar pedido y emitir comprobante (boleta/factura)  
☐ revisar comprobante de VENDEDOR en  
PENDIENTE_VALIDACION y aprobarlo  
☐ cancelar pedido en estado BORRADOR

SESIÓN 3 — Taller  
☐ abrir orden_trabajo para vehículo que ingresa  
☐ armar lista de repuestos con MECANICO_MASTER (simulado)  
☐ recibir notificación de vehículo listo y ejecutar  
cierre: verificar lista · calcular monto · cobrar ·  
emitir comprobante  
☐ liberar vehículo desde el sistema

SESIÓN 4 — Reabastecimiento y parámetros  
☐ registrar ingreso de reabastecimiento con precio  
de costo por repuesto  
☐ ajustar precio de venta tras recibir reabastecimiento  
☐ modificar umbral de margen.alerta desde parámetros  
☐ modificar tiempo de reserva S1 desde parámetros

Criterio por sesión: todos los flujos en un intento.  
Resultado: ☐ APROBADO ☐ REDISEÑO → [flujo]
```
**Criterio de aprobación global — listo para primer
usuario real:**
```
☐ Las 4 sesiones aprobadas — todos los flujos en un  
intento sin asistencia de Sant.  
☐ Elena declara verbalmente: "Puedo usar esto sola."  
→ Sant registra fecha y contexto en el log del DOC-2.  
☐ Checklist pre-deploy (Tramo 5 §8.1) completo.  
☐ Fallback (Tramo 2 §4.3) explicado a Elena y  
confirmado: Elena puede describir qué hace si el  
sistema falla sin leer ningún documento.
```
**Protocolo de reporte de Elena durante validación:**
```
Formato exigido:  
"[Acción que intenté hacer] → [Lo que pasó] →  
[Lo que esperaba que pasara]"

Ejemplo correcto:  
"Busqué el repuesto por el código 'KIT-001' →  
El sistema no mostró nada → Esperaba ver el  
repuesto en la lista"

Ejemplo incorrecto (no útil):  
"El sistema no funciona bien"
```
Sant registra cada reporte en formato BEFORE/AFTER y
lo convierte en criterio de aceptación concreto para
el rediseño correspondiente.

---

## 10. Observaciones activas y CT heredados — sin resolver en este archivo

> Por decisión de alcance confirmada al inicio de esta
> construcción: estas son tareas de infraestructura o
> script, no contenido del plan operativo en sí. Se
> heredan tal cual desde `11` §10, marcadas en los
> puntos exactos de este archivo donde se usan.

| ID | Impacto | Usado en este archivo | Estado |
|---|---|---|---|
| CT-11-01 | Script `reencrypt_fernet.py` debe existir antes del primer deploy — no se puede crear durante un incidente | Tramo 4 §7.1 — procedimiento de rotación Fernet | 🔵 Abierta — tarea de construcción DOC-3, fuera de alcance de este archivo |
| CT-11-02 | Script `verify_seed.py` debe existir y ser ejecutable desde CI/CD | Tramo 3 §6.9 · Tramo 5 §8.1 | 🔵 Abierta — idéntico |
| CT-11-05 | Monitor externo (UptimeRobot o equiv.) debe configurarse antes del primer deploy, independiente del stack interno | Tramo 4 §7.6 · Tramo 5 §8.1 y §8.3 | 🔵 Abierta — idéntico |
| CT-11-06 | Cuenta `synthetic-monitor` con permisos de solo lectura debe crearse antes del primer deploy | Referenciada indirectamente vía CT-11-05 | 🔵 Abierta — idéntico |

**Nota de cierre sobre CT-11-03 y CT-11-04:** estos dos
NO aparecen en esta tabla porque ya fueron resueltos —
verificado por búsqueda en historial de sesión: los
parches PCT-11-01 (`motivo_cancelacion`), PCT-11-02
(`origen_actor`) y PCT-11-03 (índices derivados) ya
están aplicados sobre `07 modelo-datos`. §9.1 de este
tramo ya los usa como fuente de datos confirmada.

## 11. Observaciones generadas durante esta construcción

| ID         | Observación                                                                                                                                                                                                                    | Origen                                                                                                                                                                                                                                                                                                               | Estado                                                                                |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| OBS-EP-005 | `10-seguridad-formal` §7.2 sugería superficie HTTP para consulta de audit trail; `11 plan-operacion` §6.5 la prohíbe explícitamente por razón de superficie de ataque (SSH+Tailscale+Ed25519 más resistente que HTTP+RBAC+MFA) | `10-seguridad-formal` §7.2 sugería superficie HTTP para consulta de audit trail; `11 plan-operacion` (fuente DOC-2) §6.5 la prohíbe explícitamente por razón de superficie de ataque (SSH+Tailscale+Ed25519 más resistente que HTTP+RBAC+MFA) \| Detectada al iniciar construcción de `08`, resuelta en `07` v1.0.0  | ✅ Resuelta — mecanismo SSH-only confirmado y aplicado en Tramo 4 §7.5 de este archivo |
| OBS-EP-006 | `11-plan-operacion` frontmatter declara `alimenta_doc3: false`, pero el mapa de ejecución activa `08` con `11` como única fuente, y `11` §10 declara impactos cruzados explícitos hacia DOC-3                                  | Tramo 1, verificación de cobertura inicial                                                                                                                                                                                                                                                                           | 🔵 Abierta — no bloqueante, parche de frontmatter recomendado sobre `11`              |

---

## 12. Criterios de verificación del archivo completo

> Verificación contra el criterio de cierre declarado
> en `mapa-de-ejecucion.md` para `08`: "El agente puede
> ejecutar un runbook completo ante un incidente
> declarado sin consultar el DOC-2."

### 12.1 Checklist de verificación ejecutable
```
□ El agente puede identificar la fase de despliegue  
vigente y sus condiciones de entrada/salida sin  
abrir 11 (Tramo 1 §3)  
□ El agente puede ejecutar el procedimiento de  
fallback completo ante downtime > 2h en horario  
comercial (Tramo 2 §4.3)  
□ El agente puede ejecutar cualquiera de los 9  
runbooks operativos con sus comandos exactos  
(Tramo 3 §6.1 a §6.9)  
□ El agente puede ejecutar cualquiera de los 6  
runbooks de seguridad con su plazo legal exacto  
(Tramo 4 §7.1 a §7.6)  
□ El agente puede completar los 3 checklists con  
resultado binario por ítem (Tramo 5 §8.1 a §8.3)  
□ El agente reconoce las 5 condiciones de cancelación  
CC-01 a CC-05 como criterio de detención, no de  
avance silencioso (Tramo 6 §9.2)  
□ El agente sabe que el registro ANPDP es precondición  
legal de deploy, no técnica — no intenta "resolverlo  
con código" (Tramo 5 §8.1 bloque legal)
```
### 12.2 Criterio de no dependencia hacia el DOC-2

El agente que complete el checklist de §12.1 no
necesitó abrir `11 plan-operacion` del DOC-2 — el
contenido fue trasladado casi completo por decisión de
alcance, no sintetizado, dado que no existía otro
archivo del DOC-3 con mayor detalle que sintetizar.
Las únicas referencias hacia otros archivos del DOC-3
son deliberadas:
```
03-diseno-sistema §7.6 → 5 consumer groups exactos  
por tópico (Tramo 3 §6.3,  
referencia sin reproducir)  
07-criterios-seguridad-  
ejecutables Tramo 2 → lista cerrada de roles RBAC  
§3.1 / Tramo 5 §7.1 (Tramo 5 §8.3) / categorías  
de audit trail (Tramo 4 §7.3)  
09-criterios-avance-  
automatico (pendiente) → consume CC-01 a CC-05 como  
criterio de detención formal
```
---

## 13. Fuentes

| Documento                                    | Versión                         | Secciones consultadas                                                                                     |
| -------------------------------------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `11 plan-operacion`                          | v1.0.0                          | §1 a §10 completas — fuente única declarada                                                               |
| `10 seguridad-formal`                        | v1.0.0 (+ parches recomendados) | Referencia cruzada para resolución de OBS-EP-005                                                          |
| `03-diseno-sistema`                          | v1.0.0                          | §7.6 consumer groups (referencia, no reproducción)                                                        |
| `07 modelo-datos`                            | v1.0.0 + PCT-11-01/02/03        | Confirmación de campos `motivo_cancelacion` y `origen_actor` ya aplicados, usados en §9.1 de este archivo |
| `07-criterios-seguridad-ejecutables` (DOC-3) | v1.0.0                          | Tramo 2 §3.1 roles · Tramo 5 §7.1 categorías de audit trail                                               |
| `mapa-de-ejecucion.md` (DOC-3)               | v1.2                            | Criterio de cierre declarado para archivo `08`                                                            |

---

## 14. Historial de versiones

| Versión | Fecha | Cambio | Impacto |
|---|---|---|---|
| 0.1.0 | 2026-06 | Tramo 1 — restricciones operativas RO-01 a RO-06 · estrategia de despliegue 4 fases | Base operativa establecida — OBS-EP-006 generada |
| 0.2.0 | 2026-06 | Tramo 2 — RTO 4h/RPO 24h con condición de revisión · backups 3-2-1 · fallback ejecutable | Objetivos de recuperación y respaldo declarados |
| 0.3.0 | 2026-06 | Tramo 3 — 9 runbooks operativos completos, traslado casi completo por decisión de alcance | Procedimientos de incidente operativo sin dependencia del DOC-2 |
| 0.4.0 | 2026-06 | Tramo 4 — 6 runbooks de seguridad · OBS-EP-005 resuelta formalmente (SSH-only audit trail) | Procedimientos legales y de seguridad completos |
| 0.5.0 | 2026-06 | Tramo 5 — 3 checklists operativos con bloque legal ANPDP explícito | Criterios binarios pre-deploy/diario/trimestral |
| 1.0.0 | 2026-06 | Tramo 6 — SE-07 · CC-01 a CC-05 · validación de Elena · consolidación de observaciones · 4 CT heredados sin resolver · cierre formal | Documento completo — 6 de 6 tramos cerrados |

---

**Resultado de cierre: `08-plan-operacion-ejecutable.md` v1.0.0 — 6 de 6 tramos completados. 2 observaciones generadas en esta sesión (1 resuelta, 1 abierta no bloqueante), 4 CT heredados de `11` sin resolver (tareas de infraestructura/script fuera de alcance), 2 CT de `11` confirmados ya resueltos (PCT-11-01/02/03 verificados aplicados). Sin contradicciones activas pendientes con `07` ni con `10`.**

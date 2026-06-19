---
doc: DOC-3
archivo: 02-definicion-funcional
version: 1.0.0
estado: cerrado
fecha: 2026-06
fuentes:
  - DOC-2/03-A-glosario-dominio v1.0.0
  - DOC-2/03-B-modelo-dominio v1.0.0
  - DOC-2/03-C-perfiles-uso v1.0.0
  - DOC-2/04-requerimientos v1.0.0
regla: Si hay contradicción entre este archivo y el DOC-2 → el DOC-2 gana.
validado: false
validado_cuando: primera ejecución completa con CLI o agente produce resultado correcto en todos los smoke tests declarados en §6.5
scope: protocolo de construcción automatizada para CLI y agentes
audiencia: CLI · agentes de IA · herramientas automáticas
not_for: Sant · Elena · auditores — para esos usa el DOC-2
alimenta: src/ del repositorio tecnimotos — no el vault de Obsidian
contradiccion: DOC-2 gana siempre — este archivo lo refleja, no lo reemplaza
secciones:
  - §1 — Vocabulario canónico ejecutable
  - §2 — Bounded contexts y contratos
  - §3 — Eventos de dominio
  - §4 — Roles y condiciones de uso
  - §5 — Historias de usuario como instrucciones ejecutables
  - §6 — Criterios de verificación del módulo
  - §7 — Índice de construcción
  - §8 — Registro de observaciones al DOC-2
  - §9 — Historial de versiones
modulos_cubiertos:
  - catalogo
  - pedidos
  - stock
  - taller
hu_cubiertas: 25
escenarios_gherkin: 107
observaciones_doc2_activas: 5
proxima_accion: validar con primera ejecución real de CLI o agente
ct_pendientes:
  - OBS-001 → 07 modelo-datos — campo sesión para contador de precio
  - OBS-002 → 07 modelo-datos — tabla lista_progresiva
  - OBS-003 → 07 modelo-datos — campo autorización precio en orden_trabajo
  - OBS-004 → 07 modelo-datos — campo precio_ajustado en pedido S2
  - OBS-005 → 08 contratos-interfaces — cola reintentos notificaciones S4
cambio: v0.1.0 — primera versión completa como borrador ejecutable
impacto: habilita construcción de 03-diseno-sistema cuando DOC-2 secciones 06 · 07 · 08 estén disponibles
---

# 02 — Definición funcional
## Protocolo de construcción — Tecnimotos Santi

> Este archivo le dice al agente qué comportamiento
> debe producir y cómo verificar que lo produjo
> correctamente. No explica por qué — eso está en
> el DOC-2. El agente lee este archivo completo
> antes de escribir una sola línea de código.

---

## §1 — Vocabulario canónico ejecutable

> Fuente: DOC-2/03-A-glosario-dominio §1–5
>
> Instrucción al agente:
> Antes de cerrar cualquier módulo ejecuta:
>
>   grep -r "producto\|ítem\|artículo\|orden\|ticket\
>            \|servicio\|trabajo\|apartado\|moto\
>            \|inventario\|existencia\|despacho\
>            \|voucher\|recibo\|presupuesto\|técnico\
>            \|operario\|chofer\|visita" \
>        src/{modulo}/domain/
>
> Si encuentra coincidencias → criterio de vocabulario
> fallido → corrección automática antes de avanzar.
> Si no encuentra coincidencias → vocabulario correcto.

---

### 1.1 Entidades — qué construir y cómo nombrarlas

Cada entidad de esta tabla es una clase en `domain/`.
El nombre de la clase es exactamente el término canónico.
Si el agente necesita nombrar esta entidad en cualquier
parte del código — clase, variable, atributo, función,
tabla de base de datos, evento — usa el término canónico.
Cualquier otro nombre es un error que bloquea el avance.

| Qué representa | Nombre de clase en código | Si el agente escribe esto → error bloqueante |
|----------------|--------------------------|----------------------------------------------|
| Pieza física que el negocio vende, usa en taller o gestiona en stock | `Repuesto` | `Producto` `Item` `Articulo` `Parte` `Componente` `Material` |
| Solicitud de uno o más repuestos hecha por un cliente al negocio | `Pedido` | `Orden` `Solicitud` `Compra` `Transaccion` |
| Solicitud de repuestos que el negocio hace a un proveedor | `Reabastecimiento` | `PedidoProveedor` `OrdenCompra` |
| Apartamiento temporal de un repuesto del stock para un cliente | `Reserva` | `Apartado` `Separado` |
| Registro formal de una intervención técnica sobre un vehículo | `OrdenTrabajo` | `Ticket` `Servicio` `Trabajo` |
| Interacción registrada de un cliente con el negocio | `Entrada` | `Visita` `Atencion` |
| Despacho físico de repuestos hacia un cliente externo a la ciudad | `Envio` | `Despacho` `Encomienda` |
| Documento tributario electrónico emitido al cierre de transacción | `Comprobante` | `Voucher` `Recibo` |
| Cotización formal emitida antes de confirmar el pedido | `Proforma` | `Presupuesto` `Cotizacion` |
| Cantidad física de un repuesto distinguida en tres estados operativos | `Stock` | `Inventario` `Existencia` `Cantidad` |
| Mototaxi o motolineal registrado en el sistema | `Vehiculo` | `Moto` `Unidad` `Maquina` |
| Conjunto de vehículos bajo propiedad de un mismo dueño | `Flota` | `Grupo` `ParqueVehicular` |
| Empresa o aliado que abastece repuestos al negocio | `Proveedor` | `Distribuidor` `Mayorista` |
| Miembro del equipo técnico del taller con disponibilidad registrada | `Mecanico` | `Tecnico` `Operario` |
| Cliente que opera un vehículo directamente | `Conductor` | `Chofer` `Usuario` (cuando refiere al rol de negocio) |

---

### 1.2 Procesos — qué construir y cómo nombrar los casos de uso

Cada proceso de esta tabla es un caso de uso o servicio
de aplicación en `application/`. El nombre del servicio
o método sigue el término canónico exacto.

| Qué proceso representa | Nombre del servicio o método | Si el agente escribe esto → error bloqueante |
|------------------------|------------------------------|----------------------------------------------|
| Cliente llega al local y el sistema registra la interacción | `AtencionPresencialService` | — |
| Cliente contacta por llamada o WhatsApp y el sistema registra | `AtencionRemotaService` | — |
| Cliente compra repuesto directamente sin intervención de taller | `VentaMostradorService` | `VentaService` (sin calificador) |
| Intervención técnica programada sobre un vehículo | `MantenimientoPreventivoService` | `MantenimientoService` (sin calificador) |
| Intervención técnica por falla activa sobre un vehículo | `ReparacionCorrectivaService` | `ReparacionService` (sin calificador) |
| Pedido iniciado remotamente por cliente de distrito o rural | `PedidoRemotoService` | `DespachoService` (sin calificador) |
| Apartamiento, seguimiento y liberación de un repuesto | `GestionReservaService` | — |
| Registro de repuestos consumidos durante una orden_trabajo | `RegistroConsumoTallerService` | `RegistroService` (sin calificador) |
| Solicitud, seguimiento y recepción de repuestos al proveedor | `ReabastecimientoStockService` | — |
| Generación del comprobante tributario electrónico al cierre | `EmisionComprobanteService` | `FacturacionService` |

---

### 1.3 Estados — qué valores construir por entidad

El agente construye un enum por entidad con exactamente
estos valores. Sin valores adicionales. Sin renombrados.

**Enum `EstadoPedido`**
```python
class EstadoPedido(str, Enum):
    BORRADOR           = "BORRADOR"
    CONFIRMADO         = "CONFIRMADO"
    EN_PREPARACION     = "EN_PREPARACION"
    DESPACHADO         = "DESPACHADO"
    ENTREGADO          = "ENTREGADO"
    INCIDENCIA         = "INCIDENCIA"
    CANCELADO          = "CANCELADO"
```
Transiciones que el agente debe rechazar con error de dominio:
- `ENTREGADO` → cualquier estado
- `CANCELADO` → cualquier estado
- `DESPACHADO` → `CANCELADO`

**Enum `EstadoOrdenTrabajo`**
```python
class EstadoOrdenTrabajo(str, Enum):
    ABIERTA          = "ABIERTA"
    LISTA_REPUESTOS  = "LISTA_REPUESTOS"
    EN_EJECUCION     = "EN_EJECUCION"
    REVISION_FINAL   = "REVISION_FINAL"
    CERRADA          = "CERRADA"
    CANCELADA        = "CANCELADA"
```
Transición que el agente debe bloquear:
- `EN_EJECUCION` → `REVISION_FINAL` sin confirmación
  del mecánico de lista verificada y costo de mano
  de obra declarado.
- `CERRADA` solo cuando `pedidos` envía
  evento `cobro.confirmado`.

**Enum `EstadoReserva`**
```python
class EstadoReserva(str, Enum):
    ACTIVA      = "ACTIVA"
    CONFIRMADA  = "CONFIRMADA"
    EXPIRADA    = "EXPIRADA"
    LIBERADA    = "LIBERADA"
```
Invariante que el agente debe hacer cumplir:
Solo en `ACTIVA` y `CONFIRMADA` el repuesto permanece
descontado del stock `disponible`. En cualquier otro
estado el agente debe verificar que stock fue liberado.

**Enum `EstadoStockUnidad`**
```python
class EstadoStockUnidad(str, Enum):
    DISPONIBLE   = "disponible"
    APARTADO     = "apartado"
    EN_TRANSITO  = "en_transito"
```
Regla crítica que el agente debe hacer cumplir:
El catálogo público muestra únicamente unidades en
estado `disponible`. El agente no puede exponer
`apartado` ni `en_transito` en ningún endpoint
del catálogo bajo ninguna condición.

**Enum `EstadoReabastecimiento`**
```python
class EstadoReabastecimiento(str, Enum):
    SOLICITADO             = "SOLICITADO"
    CONFIRMADO_PROVEEDOR   = "CONFIRMADO_PROVEEDOR"
    EN_TRANSITO            = "EN_TRANSITO"
    RECIBIDO               = "RECIBIDO"
    CANCELADO              = "CANCELADO"
```

**Enum `EstadoEnvio`**
```python
class EstadoEnvio(str, Enum):
    PREPARADO           = "PREPARADO"
    ENTREGADO_AGENCIA   = "ENTREGADO_AGENCIA"
    EN_TRANSITO         = "EN_TRANSITO"
    ENTREGADO_CLIENTE   = "ENTREGADO_CLIENTE"
    INCIDENCIA          = "INCIDENCIA"
    RESUELTO            = "RESUELTO"
```

**Enum `EstadoComprobante`**
```python
class EstadoComprobante(str, Enum):
    PENDIENTE_VALIDACION = "PENDIENTE_VALIDACION"
    EMITIDO              = "EMITIDO"
    ENVIADO_CLIENTE      = "ENVIADO_CLIENTE"
    ANULADO              = "ANULADO"
```
Regla que el agente debe hacer cumplir:
Un comprobante en `ENVIADO_CLIENTE` no se elimina.
Solo se anula mediante nota de crédito. El agente
no puede implementar `DELETE` sobre un comprobante
emitido bajo ninguna condición.

---

### 1.4 Roles — qué construir en RBAC

El agente construye exactamente estos seis roles.
Sin roles adicionales. Sin renombrados.

```python
class Rol(str, Enum):
    SUPERADMIN       = "SUPERADMIN"
    ADMINISTRADOR    = "ADMINISTRADOR"
    VENDEDOR         = "VENDEDOR"
    MECANICO_MASTER  = "MECANICO_MASTER"
    MECANICO_JUNIOR  = "MECANICO_JUNIOR"
    CLIENTE          = "CLIENTE"
```

Sub-roles del rol `CLIENTE` — campo adicional
en la entidad de usuario cliente:

```python
class SubRolCliente(str, Enum):
    CLIENTE_CONDUCTOR        = "CLIENTE_CONDUCTOR"
    CLIENTE_DISTRITO         = "CLIENTE_DISTRITO"
    CLIENTE_FLOTA_DUENO      = "CLIENTE_FLOTA_DUENO"
    CLIENTE_FLOTA_CONDUCTOR  = "CLIENTE_FLOTA_CONDUCTOR"
    CLIENTE_RURAL            = "CLIENTE_RURAL"
    CLIENTE_MOTOLINEAL       = "CLIENTE_MOTOLINEAL"
```

---

### 1.5 Discriminador de universo — campo obligatorio en Repuesto

Todo `Repuesto` tiene campo `universo`. El agente
construye este enum y lo usa como discriminador
estructural en la tabla de base de datos (ADR-004).

```python
class UniversoRepuesto(str, Enum):
    MOTOTAXI      = "mototaxi"
    MOTOLINEAL    = "motolineal"
```

Regla que el agente debe hacer cumplir:
Un repuesto de universo `mototaxi` nunca aparece
en resultados de búsqueda de universo `motolineal`
y viceversa. Esta separación opera en la query de
base de datos — no en un filtro posterior en código.

Campos de búsqueda primaria en `Repuesto`:
`modelo` · `año` · `codigo`
Estos tres campos tienen índice en base de datos.
`universo` es discriminador estructural — no campo
de búsqueda inicial.

---
### §1.6 — Logging estructurado ejecutable (RNT-06)
> Fuente: Gobierno Técnico — 10-monitoring-logging.md
> Tramo 2 (Logging estructurado) · Tramo 9 (Estrategia Tecnimotos)

Instrucción al agente: todo log emitido por cualquier
módulo usa el formato JSON declarado aquí — sin
excepción, desde el primer módulo construido (catalogo).

CAMPOS OBLIGATORIOS — el agente implementa un
JSONFormatter que lanza excepción en desarrollo si
falta cualquiera de estos cinco campos:

  timestamp     ISO 8601 UTC
  level         DEBUG | INFO | WARNING | ERROR | CRITICAL
  service       nombre del módulo: catalogo|pedidos|stock|taller|shared
  version       versión del servicio desplegado
  environment   development|staging|production

CAMPO DE CORRELACIÓN — obligatorio, generado
automáticamente, nunca manual:

  request_id    UUID v4 · generado por
                CorrelationMiddleware (primer
                middleware de la cadena) ·
                propagado vía ContextVar ·
                devuelto en header X-Request-ID
                de toda respuesta

Mecanismo de propagación: el ContextVar es por
corrutina — el middleware debe establecer el contexto
ANTES de que call_next cree corrutinas hijas, o la
propagación se pierde en handlers asíncronos del EDA
interno.

trace_id (opcional en MVP): solo se añade cuando un
evento cruza hacia un worker asíncrono o servicio
externo que necesita correlacionarse con la request
HTTP original. En el Modular Monolith del MVP,
request_id es suficiente para la mayoría de los casos
— trace_id no es obligatorio hasta que exista una
necesidad real de correlación fuera de proceso.

Librería: el agente implementa esto sobre la librería
estándar `logging` de Python con formatter JSON
custom — NO introduce una librería de logging nueva
(structlog, loguru) sin parche formal sobre este
archivo, para mantener consistencia con el resto del
stack ya declarado en 03-diseno-sistema §3.

Verificación: 09-criterios-avance-automatico §4.1
("Logs estructurados") ejecuta el test contra ESTA
especificación — sin esta sección, ese test no tenía
contrato contra el cual validar.

---

## §2 — Bounded contexts y contratos

> Fuente: DOC-2/03-B-modelo-dominio §1–3
>
> Instrucción al agente:
> Cada módulo vive en `src/{modulo}/`.
> La estructura interna de cada módulo es:
>
>   src/{modulo}/
>   ├── domain/          ← entidades, value objects, eventos
>   ├── application/     ← casos de uso, servicios
>   ├── infrastructure/  ← repositorios, adaptadores externos
>   └── api/             ← controladores, schemas de entrada/salida
>
> Verificación automática antes de cerrar módulo:
>   python scripts/check_dip.py src/{modulo}
> Si encuentra imports de infrastructure/ en domain/
> → criterio de arquitectura fallido → corrección
> antes de avanzar.

---

### 2.1 Qué construye cada módulo

**Módulo `catalogo`**

Construye:
- CRUD de `Repuesto` con todos sus atributos:
  `codigo` · `nombre` · `descripcion` · `precio_venta`
  · `categoria` · `universo` · `modelo` · `año`
- Endpoint de búsqueda por `modelo` + `año` (combinados)
  y por `codigo` (individual)
- Filtro de universo aplicado en query de base de datos
- Exposición de `precio_venta` vigente para consumo
  interno de `pedidos` y `taller`
- Advertencia visible en repuestos de categoría
  `tecnico_especializado`

No construye en este módulo:
- Lógica de stock — eso es `stock`
- Lógica de pedidos o reservas — eso es `pedidos`
- Lógica de taller — eso es `taller`
- Descuentos — eso es `pedidos` bajo criterio exclusivo
  de `ADMINISTRADOR`

**Módulo `pedidos`**

Construye:
- Ciclo de vida completo de `Pedido` con los siete
  estados declarados en §1.3
- Ciclo de vida de `Reserva` con tiempo diferenciado:
  presencial 1 día · distrito y rural 2-3 días
  Notificaciones automáticas: 3 antes de liberar
  Liberación automática si no hay pago ni respuesta
- Emisión de `Proforma` como documento formal
- Gestión de `Envio` para pedidos externos a la ciudad
- Gestión de `Comprobante` con flujo:
  `VENDEDOR` genera en `PENDIENTE_VALIDACION` →
  `ADMINISTRADOR` aprueba → emite ante SUNAT →
  pasa a `EMITIDO`
- Aplicación de descuentos por `ADMINISTRADOR` —
  invisibles para cualquier otro rol
- Deuda activa por excepción del 80% con alertas
  al 50% del plazo y un día antes del vencimiento
- `pedido_por_lista` para `CLIENTE_DISTRITO`

No construye en este módulo:
- Precio de repuestos — lo consulta a `catalogo`
- Movimientos de stock — los solicita a `stock`
- Trabajo técnico — eso es `taller`

**Módulo `stock`**

Construye:
- Registro de stock por `Repuesto` en tres estados:
  `disponible` · `apartado` · `en_transito`
- Descuento de `disponible` → `apartado` al confirmar
  reserva (solicitud de `pedidos`)
- Devolución de `apartado` → `disponible` al expirar
  o liberar reserva
- Descuento atómico permanente al cierre de
  `orden_trabajo` — todos los repuestos en una
  sola operación transaccional
- Registro de entradas al recibir `reabastecimiento`
- Detección de stock bajo umbral mínimo → notificación
  a `ADMINISTRADOR`
- Ciclo de vida de `Reabastecimiento` con cinco estados
- Historial de movimientos con trazabilidad completa:
  `repuesto_id` · `cantidad` · `tipo_movimiento`
  · `actor_id` · `modulo_origen` · `referencia_id`
  · `timestamp`

No construye en este módulo:
- Precio de venta — eso es `catalogo`
- Ciclo de vida del pedido — eso es `pedidos`
- Trabajo técnico — eso es `taller`

**Módulo `taller`**

Construye:
- Ciclo de vida completo de `OrdenTrabajo` con
  seis estados declarados en §1.3
- Apertura de orden con campos obligatorios:
  `vehiculo_id` · `tipo_servicio` · `tipo_urgencia`
  · `mecanico_id`
- Lista de repuestos presentada al cliente con monto
  estimado antes de iniciar — sin aprobación no avanza
- Registro de consumo real de repuestos durante
  `EN_EJECUCION`
- Lógica de costos adicionales por tramos de precio:
  < S/30: aprobación automática
  S/30–S/100: espera 30 min → aprobación tácita
  > S/100: detención hasta confirmación explícita
- Excepción del 80%: con aprobación conjunta de
  `ADMINISTRADOR` y `MECANICO_MASTER` el vehículo
  puede salir. Saldo queda como deuda activa.
- Historial de intervenciones por `vehiculo`
- Disponibilidad de `mecanico` para asignación
- Flujo de cierre coordinado con `pedidos`:
  mecánico confirma → envía lista a `pedidos` →
  `pedidos` cobra → envía `cobro.confirmado` →
  `taller` cierra y libera vehículo

No construye en este módulo:
- Cobro ni comprobante — eso es `pedidos`
- Movimientos de stock directos — los solicita a `stock`
- Precios — los consulta a `catalogo`

---

### 2.2 Contratos síncronos — qué implementar

El agente implementa estos contratos como llamadas
internas entre puertos (arquitectura hexagonal).
Cada contrato tiene un puerto de salida en el módulo
consumidor y un adaptador en el módulo proveedor.

**Contrato 1: `pedidos` consulta precio a `catalogo`**

Cuándo: al crear pedido · al emitir proforma
Qué retorna `catalogo`:
```python
{
  "repuesto_id": str,
  "codigo": str,
  "precio_venta": Decimal,
  "nombre": str,
  "categoria": str,
  "universo": str,
  "activo": bool
}
```
Qué hace `pedidos` si `activo == False`:
→ bloquea el pedido
→ notifica a `ADMINISTRADOR`
→ no crea el pedido

Qué hace `pedidos` si `repuesto_id` no existe:
→ rechaza el ítem con error `REPUESTO_NO_ENCONTRADO`
→ no crea el pedido

**Contrato 2: `taller` consulta precio a `catalogo`**

Cuándo: al armar lista de orden_trabajo · al agregar
repuesto durante `EN_EJECUCION`
Mismo schema de retorno que Contrato 1.
Qué hace `taller` si no encuentra el código:
→ bloquea el agregado
→ alerta al `MECANICO` o `ADMINISTRADOR` en UI
→ no agrega el repuesto a la lista

**Contrato 3: `pedidos` consulta stock a `stock`**

Cuándo: al confirmar reserva · al confirmar pedido
Qué retorna `stock`:
```python
{
  "repuesto_id": str,
  "cantidad_disponible": int
}
```
Qué hace `pedidos` si `cantidad_disponible == 0`:
→ pedido vuelve a `BORRADOR`
→ notifica al cliente que el repuesto no está disponible
→ no confirma la reserva

**Contrato 4: `taller` envía lista a `pedidos` en REVISION_FINAL**

Cuándo: `MECANICO_MASTER` declara vehículo listo
Qué envía `taller`:
```python
{
  "orden_trabajo_id": str,
  "repuestos_consumidos": [
    {"repuesto_id": str, "codigo": str,
     "cantidad": int, "precio_unitario": Decimal}
  ],
  "costo_mano_obra": Decimal,
  "mecanico_id": str
}
```
Qué hace `pedidos` si detecta discrepancia entre
repuestos listados y movimientos en `stock`:
→ rechaza el cierre
→ notifica a `ADMINISTRADOR` con detalle
→ `orden_trabajo` permanece en `REVISION_FINAL`

Qué hace `pedidos` si el cliente pagó menos del 80%
sin aprobación conjunta registrada:
→ bloquea el cierre
→ el vehículo no se libera

---

### 2.3 Verificación de contratos

Antes de cerrar cada módulo el agente verifica:

```bash
# Verifica que el puerto de salida existe
grep -r "CatalogoPort\|StockPort\|PedidosPort\|TallerPort" \
     src/{modulo}/domain/

# Verifica que el adaptador existe
grep -r "CatalogoAdapter\|StockAdapter\|PedidosAdapter\|TallerAdapter" \
     src/{modulo}/infrastructure/
```

Si el puerto existe pero el adaptador no → el contrato
no está implementado → criterio de contrato fallido.

---
## §3 — Eventos de dominio

> Fuente: DOC-2/03-B-modelo-dominio §4
>
> Instrucción al agente:
> Cada evento de esta sección es una clase en
> src/{modulo}/domain/events/
> El agente publica eventos usando Redis Streams
> (ADR-001). El agente no reacciona a ningún
> evento que no esté declarado en esta sección.
>
> Todo evento tiene estos campos obligatorios:
>
> {
>   "evento_id": str,        ← UUID generado al publicar
>   "tipo": str,             ← nombre exacto del evento
>   "timestamp": datetime,   ← UTC ISO 8601
>   "modulo_origen": str,    ← nombre del módulo que publica
>   "payload": dict          ← campos declarados por evento
> }
>
> Verificación antes de cerrar módulo:
> El agente ejecuta los tests de integración que
> verifican que cada evento declarado aquí es
> publicado en el stream correcto con el payload
> mínimo completo. Si un evento no tiene test
> de integración → criterio de contrato fallido.

---

### 3.1 Eventos del módulo `catalogo`

**`repuesto.creado`**

Cuándo lo publica: `ADMINISTRADOR` registra un
repuesto nuevo en el catálogo.

Payload mínimo:
```python
{
  "repuesto_id": str,
  "codigo": str,
  "universo": str,   # "mototaxi" | "motolineal"
  "modelo": str,
  "año": int,
  "categoria": str
}
```
Quién lo consume y qué hace:
- `stock` → inicializa registro de stock en cero
  para ese repuesto. Sin este paso el repuesto
  existe en catálogo pero no tiene stock registrado.

---

**`repuesto.precio_actualizado`**

Cuándo lo publica: `ADMINISTRADOR` modifica el
precio de venta de un repuesto existente.

Payload mínimo:
```python
{
  "repuesto_id": str,
  "codigo": str,
  "precio_anterior": Decimal,
  "precio_nuevo": Decimal,
  "timestamp": datetime
}
```
Quién lo consume y qué hace:
- `pedidos` → busca pedidos en `BORRADOR` que
  contengan ese repuesto → notifica al cliente
  que el precio cambió → pedido permanece en
  `BORRADOR` hasta nueva confirmación del cliente.
  Pedidos ya confirmados con pago activo: no se
  tocan bajo ninguna condición.
- `taller` → busca órdenes_trabajo en
  `LISTA_REPUESTOS` que contengan ese repuesto
  → recalcula el monto estimado → notifica al
  cliente con el nuevo monto.

---

**`repuesto.dado_de_baja`**

Cuándo lo publica: `ADMINISTRADOR` desactiva un
repuesto del catálogo.

Payload mínimo:
```python
{
  "repuesto_id": str,
  "codigo": str,
  "motivo": str
}
```
Quién lo consume y qué hace:
- `pedidos` → bloquea nuevos pedidos con ese código.
- `stock` → congela movimientos de ese repuesto.
- `taller` → alerta si hay orden_trabajo activa
  que lo incluye — no cancela automáticamente,
  alerta a `ADMINISTRADOR`.

---

### 3.2 Eventos del módulo `stock`

**`stock.agotado`**

Cuándo lo publica: stock `disponible` de un
repuesto llega a cero.

Payload mínimo:
```python
{
  "repuesto_id": str,
  "codigo": str
}
```
Quién lo consume y qué hace:
- `catalogo` → marca el repuesto como no disponible
  en catálogo público. Clientes no lo ven como
  disponible desde ese momento.
- `pedidos` → bloquea nuevas reservas para ese
  código.

---

**`stock.bajo_umbral`**

Cuándo lo publica: stock `disponible` cae al
umbral mínimo configurado por `ADMINISTRADOR`.

Payload mínimo:
```python
{
  "repuesto_id": str,
  "codigo": str,
  "cantidad_actual": int,
  "umbral_minimo": int
}
```
Quién lo consume y qué hace:
- Notificación a `ADMINISTRADOR` vía canal
  configurado. El sistema informa — no activa
  reabastecimiento automático bajo ninguna
  condición. La decisión es exclusiva de Elena.

---

**`stock.disponible`**

Cuándo lo publica: reabastecimiento recibido
o reserva liberada devuelve stock a disponible.

Payload mínimo:
```python
{
  "repuesto_id": str,
  "codigo": str,
  "cantidad_nueva": int
}
```
Quién lo consume y qué hace:
- `catalogo` → reactiva visibilidad del repuesto
  en catálogo público.
- `pedidos` → notifica a clientes con solicitud
  de notificación activa para ese repuesto.

---

**`stock.consumo_registrado`**

Cuándo lo publica: `stock` ejecuta el descuento
atómico al cierre de una orden_trabajo.

Payload mínimo:
```python
{
  "orden_trabajo_id": str,
  "repuestos_descontados": [
    {"repuesto_id": str, "cantidad": int}
  ],
  "timestamp": datetime
}
```
Quién lo consume y qué hace:
- `taller` → confirma que el consumo quedó
  registrado → procede al cierre definitivo
  de la orden_trabajo.

Regla crítica que el agente debe implementar:
Este descuento es una operación transaccional
atómica. Si falla cualquier repuesto de la lista
→ rollback completo → ningún repuesto se descuenta
→ `taller` bloquea el cierre hasta resolución.

---

**`reabastecimiento.recibido`**

Cuándo lo publica: `ADMINISTRADOR` confirma
recepción física del reabastecimiento.

Payload mínimo:
```python
{
  "reabastecimiento_id": str,
  "repuestos_recibidos": [
    {
      "repuesto_id": str,
      "codigo": str,
      "cantidad": int,
      "precio_costo_unitario": Decimal
    }
  ]
}
```
Quién lo consume y qué hace:
- `catalogo` → señal para que `ADMINISTRADOR`
  evalúe ajuste de precio de venta. El sistema
  no actualiza precio automáticamente.
- `pedidos` → notifica a clientes en espera
  de ese repuesto.

---

**`margen.alerta`**

Cuándo lo publica: el precio de costo de un lote
nuevo varía más del umbral configurado (inicial
10%) respecto al lote anterior.

Payload mínimo:
```python
{
  "repuesto_id": str,
  "codigo": str,
  "precio_costo_anterior": Decimal,
  "precio_costo_nuevo": Decimal,
  "variacion_porcentual": float,
  "precio_venta_vigente": Decimal
}
```
Quién lo consume y qué hace:
- Notificación a `ADMINISTRADOR` con la variación
  exacta para que evalúe si ajusta el precio de
  venta. El sistema no cambia nada automáticamente.

---

### 3.3 Eventos del módulo `pedidos`

**`reserva.creada`**

Cuándo lo publica: cliente solicita reserva y
`pedidos` la crea exitosamente.

Payload mínimo:
```python
{
  "reserva_id": str,
  "repuesto_id": str,
  "cantidad": int,
  "cliente_id": str,
  "segmento": str,   # sub-rol del cliente
  "expira_en": datetime
}
```
Quién lo consume y qué hace:
- `stock` → descuenta de `disponible` a `apartado`
  de forma inmediata. Si no puede descontar →
  publica error → `pedidos` cancela la reserva
  y notifica al cliente.

---

**`reserva.liberada`**

Cuándo lo publica: reserva expira automáticamente
o `ADMINISTRADOR` / `VENDEDOR` la libera manual.

Payload mínimo:
```python
{
  "reserva_id": str,
  "repuesto_id": str,
  "cantidad": int,
  "motivo": str   # "EXPIRADA" | "LIBERADA_MANUAL" | "PRIORIDAD_TALLER"
}
```
Quién lo consume y qué hace:
- `stock` → devuelve de `apartado` a `disponible`.

---

**`reserva.prioridad_taller`**

Cuándo lo publica: `taller` necesita un repuesto
con urgencia y la reserva activa no tiene pago
registrado.

Payload mínimo:
```python
{
  "reserva_id": str,
  "repuesto_id": str,
  "orden_trabajo_id": str
}
```
Quién lo consume y qué hace:
- `stock` → libera el apartado.
- Cliente notificado con motivo explícito:
  "Tu reserva fue liberada por prioridad del taller"
  + opción de crear nueva reserva.

Condición que el agente debe verificar antes de
publicar este evento: el cliente debe haber recibido
al menos una notificación previa. Si no recibió
ninguna → el sistema notifica primero y espera
antes de liberar.

---

**`pedido.confirmado`**

Cuándo lo publica: pedido pasa de `BORRADOR`
a `CONFIRMADO` con stock verificado.

Payload mínimo:
```python
{
  "pedido_id": str,
  "repuestos": [
    {"repuesto_id": str, "cantidad": int}
  ],
  "cliente_id": str,
  "canal_origen": str   # "presencial" | "remoto"
}
```
Quién lo consume y qué hace:
- `stock` → confirma disponibilidad final.
- `taller` → si hay orden_trabajo vinculada,
  registra que el pedido está confirmado.

---

**`pedido.cancelado`**

Cuándo lo publica: pedido se cancela en cualquier
estado antes de `DESPACHADO`.

Payload mínimo:
```python
{
  "pedido_id": str,
  "repuestos": [
    {"repuesto_id": str, "cantidad": int}
  ],
  "motivo": str
}
```
Quién lo consume y qué hace:
- `stock` → libera stock `apartado` si había
  reserva activa vinculada.

---

**`cobro.confirmado`**

Cuándo lo publica: pago registrado y comprobante
en `EMITIDO` o `PENDIENTE_VALIDACION`.

Payload mínimo:
```python
{
  "pedido_id": str,
  "orden_trabajo_id": str,
  "monto_total": Decimal,
  "monto_pagado": Decimal,
  "deuda_activa": Decimal   # 0 si pagó completo
}
```
Quién lo consume y qué hace:
- `taller` → pasa `orden_trabajo` a `CERRADA`
  → libera el vehículo para prueba de ruta.

---

**`comprobante.pendiente_validacion`**

Cuándo lo publica: `VENDEDOR` genera comprobante
— queda pendiente de aprobación de Elena.

Payload mínimo:
```python
{
  "comprobante_id": str,
  "pedido_id": str,
  "monto": Decimal,
  "tipo": str   # "boleta" | "factura"
}
```
Quién lo consume y qué hace:
- Notificación a `ADMINISTRADOR` para aprobación.
  El comprobante no se emite ante SUNAT hasta
  que `ADMINISTRADOR` lo apruebe explícitamente.

---

### 3.4 Eventos del módulo `taller`

**`orden_trabajo.abierta`**

Cuándo lo publica: `MECANICO_MASTER` o
`ADMINISTRADOR` abre una orden_trabajo nueva.

Payload mínimo:
```python
{
  "orden_trabajo_id": str,
  "vehiculo_id": str,
  "mecanico_id": str,
  "tipo_servicio": str   # "preventivo"|"correctivo"|"diagnostico"|"soldadura"
}
```
Quién lo consume y qué hace:
- `stock` → verifica disponibilidad de los
  repuestos de la lista inicial.

---

**`orden_trabajo.lista_aprobada`**

Cuándo lo publica: cliente aprueba la lista
de repuestos y monto estimado.

Payload mínimo:
```python
{
  "orden_trabajo_id": str,
  "repuestos": [
    {
      "repuesto_id": str,
      "cantidad": int,
      "precio_unitario": Decimal
    }
  ],
  "monto_estimado": Decimal,
  "cliente_id": str
}
```
Quién lo consume y qué hace:
- `pedidos` → inicia el flujo comercial vinculado
  a la orden.

---

**`orden_trabajo.repuesto_agregado`**

Cuándo lo publica: mecánico, Elena o Sant agregan
un repuesto durante `EN_EJECUCION`.

Payload mínimo:
```python
{
  "orden_trabajo_id": str,
  "repuesto_id": str,
  "cantidad": int,
  "precio_vigente": Decimal,
  "monto_actualizado": Decimal
}
```
Quién lo consume y qué hace:
- `stock` → verifica disponibilidad del repuesto
  agregado.
- `pedidos` → aplica lógica de tramos de precio
  y notifica al cliente:
  - < S/30 → aprobación automática · trabajo continúa
  - S/30–S/100 → espera 30 min → tácita si no responde
  - > S/100 → detención hasta confirmación explícita

---

**`orden_trabajo.revision_final`**

Cuándo lo publica: `MECANICO_MASTER` declara
vehículo listo con lista verificada y mano de
obra declarada.

Payload mínimo:
```python
{
  "orden_trabajo_id": str,
  "repuestos_consumidos": [
    {
      "repuesto_id": str,
      "codigo": str,
      "cantidad": int,
      "precio_unitario": Decimal
    }
  ],
  "costo_mano_obra": Decimal,
  "mecanico_id": str
}
```
Quién lo consume y qué hace:
- `pedidos` → recibe lista + costo → verifica
  contra movimientos en `stock` → ejecuta cobro
  → emite o pone en `PENDIENTE_VALIDACION`
  el comprobante.

---

**`orden_trabajo.cerrada`**

Cuándo lo publica: `taller` recibe
`cobro.confirmado` de `pedidos`.

Payload mínimo:
```python
{
  "orden_trabajo_id": str,
  "vehiculo_id": str,
  "repuestos_consumidos": [
    {"repuesto_id": str, "cantidad": int}
  ]
}
```
Quién lo consume y qué hace:
- `stock` → ejecuta descuento atómico de todos
  los repuestos consumidos en una sola operación
  transaccional.

---

**`orden_trabajo.cancelada`**

Cuándo lo publica: trabajo no realizado — cliente
retiró el vehículo antes del cierre.

Payload mínimo:
```python
{
  "orden_trabajo_id": str,
  "motivo": str
}
```
Quién lo consume y qué hace:
- `pedidos` → cancela el flujo comercial vinculado.
- `stock` → libera cualquier apartado asociado
  a esa orden.

---

**`vehiculo.liberado`**

Cuándo lo publica: prueba de ruta confirmada —
vehículo listo para retiro del cliente.

Payload mínimo:
```python
{
  "orden_trabajo_id": str,
  "vehiculo_id": str,
  "cliente_id": str
}
```
Quién lo consume y qué hace:
- `pedidos` → registra cierre total de la `entrada`.

---

## §4 — Roles y condiciones de uso

> Fuente: DOC-2/03-A-glosario-dominio §4
>         DOC-2/03-C-perfiles-uso §2–7
>
> Instrucción al agente:
> Esta sección define qué puede hacer cada rol
> y bajo qué condiciones reales opera. El agente
> implementa el RBAC usando esta tabla como única
> fuente de verdad. Toda capacidad no declarada
> aquí está implícitamente prohibida para ese rol.
> La verificación es en cada endpoint y caso de uso —
> no solo en el middleware de autenticación.

---

### 4.1 Capacidades por rol y módulo

**Módulo `catalogo`**

| Capacidad | SUPERADMIN | ADMINISTRADOR | VENDEDOR | MECANICO_MASTER | MECANICO_JUNIOR | CLIENTE |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| Consultar catálogo público | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Buscar por modelo, año, código | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Buscar por descripción libre | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ver precio de venta vigente | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ ver nota §4.2 |
| Ver precio de costo | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver margen por repuesto | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Crear repuesto nuevo | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Modificar precio de venta | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Dar de baja repuesto | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Recibir margen.alerta | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Configurar umbral margen.alerta | ✅ | ✅ vía UI | ❌ | ❌ | ❌ | ❌ |

**Módulo `pedidos`**

| Capacidad | SUPERADMIN | ADMINISTRADOR | VENDEDOR | MECANICO_MASTER | MECANICO_JUNIOR | CLIENTE |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| Crear pedido | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Crear pedido_por_lista | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ solo CLIENTE_DISTRITO |
| Confirmar pedido | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Cancelar pedido | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ solo en BORRADOR |
| Gestionar reserva propia | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Liberar reserva manualmente | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Emitir proforma | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Solicitar proforma | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Aplicar descuento por ítem | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver descuento aplicado | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Generar comprobante pendiente | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Aprobar y emitir comprobante | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Anular comprobante | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Elegir tipo comprobante | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Ver historial propio de pedidos | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Ver historial del negocio | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Registrar deuda activa 80% | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Ver deuda activa | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ solo la propia |

**Módulo `stock`**

| Capacidad | SUPERADMIN | ADMINISTRADOR | VENDEDOR | MECANICO_MASTER | MECANICO_JUNIOR | CLIENTE |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| Consultar stock disponible | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consultar stock apartado | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Consultar stock en tránsito | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Ajuste manual de stock | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Crear reabastecimiento | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Aprobar reabastecimiento | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Registrar recepción | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Registrar precio de costo | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Ver historial de movimientos | ✅ | ✅ | 👁 lectura | ❌ | ❌ | ❌ |
| Ver datos de proveedor | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

**Módulo `taller`**

| Capacidad | SUPERADMIN | ADMINISTRADOR | VENDEDOR | MECANICO_MASTER | MECANICO_JUNIOR | CLIENTE |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| Abrir orden_trabajo | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Asignar mecánico | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Ver orden_trabajo activa | ✅ | ✅ | ✅ | ✅ | ⚠️ solo asignadas | 👁 solo la propia |
| Armar lista de repuestos | ✅ | ✅ | ✅ | ✅ | ⚠️ solo asignadas | ❌ |
| Modificar lista EN_EJECUCION | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Aprobar costos adicionales | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Registrar consumo de repuesto | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Registrar diagnóstico | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Declarar costo de mano de obra | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ |
| Declarar vehículo listo → REVISION_FINAL | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Validar prueba de ruta | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Cerrar orden_trabajo | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Liberar vehículo | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Ver historial de orden_trabajo | ✅ | ✅ | ✅ | ✅ | ⚠️ solo asignadas | 👁 solo las propias |
| Ver disponibilidad de mecánicos | ✅ | ✅ | ✅ | ✅ | ❌ | 👁 básica |
| Cancelar orden_trabajo | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Autorizar visibilidad de precio a cliente | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |

---

### 4.2 Nota — visibilidad de precio para CLIENTE

El agente implementa dos niveles de visibilidad
de precio para el rol `CLIENTE`:

**Nivel 0 — visitante sin cuenta:**
Puede ver disponibilidad general del repuesto.
No puede ver el precio exacto bajo ninguna condición.
El endpoint retorna `precio_visible: false` y
`precio: null`.

**Nivel 1 — cliente autenticado:**
Puede ver precio bajo demanda mediante acción
explícita. El sistema lleva contador de consultas
de precio por sesión. Al llegar a 3 consultas
en la misma sesión → el endpoint retorna
`precio_visible: false` con mensaje:
"Para ver más precios visítanos en tienda
o contáctanos". El contador se reinicia en
nueva sesión. La disponibilidad y el stock
nunca se restringen — solo el precio.

**Nivel 2 — autorización manual activa:**
`MECANICO_MASTER`, `ADMINISTRADOR` o `VENDEDOR`
pueden activar visibilidad completa de precio
para un cliente específico durante una sesión
vinculada a una orden_trabajo activa. Esta
autorización es manual y explícita — no se
activa automáticamente por ninguna condición.
`MECANICO_JUNIOR` no puede otorgar esta
autorización bajo ninguna condición.
La autorización queda registrada en log de
auditoría con actor_id y timestamp.

---

### 4.3 Condiciones de uso por perfil — restricciones de diseño

El agente implementa los flujos con estas
restricciones. Son criterios de aceptación
de interfaz — no solo de lógica de negocio.

**ADMINISTRADOR — Elena en `tecnimoto`**

- Ninguna acción crítica requiere más de 3 pasos
  desde la pantalla donde Elena está en ese momento.
- El hardware de `tecnimoto` es el piso de rendimiento:
  AMD Sempron · 4GB RAM · Debian 13 · Chromium.
  Toda funcionalidad de `ADMINISTRADOR` debe cargar
  en ≤ 3 segundos en ese hardware.
- Los mensajes de error no muestran códigos HTTP
  ni stack traces. Muestran acción concreta en
  lenguaje del glosario `03-A`.
- MFA obligatorio al iniciar sesión. El flujo
  de MFA completa en ≤ 60 segundos desde `tecnimoto`.

**MECANICO_MASTER y MECANICO_JUNIOR — en área de taller**

- Dispositivo base: Android gama media con manos
  posiblemente ocupadas o sucias.
- El registro de consumo de repuestos durante
  `EN_EJECUCION` es la acción más frecuente.
  Debe completarse en ≤ 4 taps por repuesto.
- Sin teclado libre en flujos críticos de registro.
- `MECANICO_JUNIOR` no ve la opción de declarar
  vehículo listo en su interfaz. La acción no
  existe para su rol — no aparece deshabilitada,
  directamente no existe.
- `MECANICO_MASTER` ve todas sus órdenes_trabajo
  activas incluyendo las delegadas, con indicador
  visual de cuáles están en ejecución por un junior.

**CLIENTE — en campo**

- Dispositivo base: Android gama media-baja
  con pantalla de 5 pulgadas.
- Flujos críticos de S1 y S4 operables con una
  mano sin reposicionar el dispositivo.
- Máximo 2 taps para llegar a consulta de stock
  desde pantalla de inicio.
- Texto grande y contraste alto — legible en
  sol directo.
- Para S4 específicamente: operaciones críticas
  toleran interrupción de conexión de hasta
  30 segundos sin pérdida de estado. Si la
  interrupción supera 30 segundos el sistema
  muestra mensaje claro y cancela la operación
  de forma limpia — nunca deja estado indeterminado.
- Notificaciones con reintento automático hasta
  3 veces en intervalos de 10 minutos si el
  primer intento falla por falta de conexión.

---
## §5 — Historias de usuario como instrucciones ejecutables

> Fuente: DOC-2/04-requerimientos §2–3
>
> Instrucción al agente:
> Cada HU de esta sección define exactamente qué
> debe construir el agente — qué endpoint, qué
> lógica de dominio y qué escenario Gherkin debe
> pasar antes de avanzar al siguiente módulo.
>
> Estructura de cada HU:
>   - Qué construir → endpoint + caso de uso + entidades
>   - Módulo responsable → dónde vive el código
>   - Escenarios Gherkin → criterios de aceptación
>     ejecutables como tests BDD
>
> El agente no cierra una HU hasta que todos sus
> escenarios Gherkin pasan en la suite de tests.
> Si un escenario falla → corrección automática
> antes de avanzar. Máximo 3 intentos por escenario.
> Tras 3 intentos fallidos → DETENCIÓN con reporte.
>
> Restricciones activas en todos los escenarios:
>   RNN-01 Precio siempre manual — ningún Then
>           actualiza precio automáticamente
>   RNN-02 Descuentos invisibles para el cliente —
>           el cliente ve solo precio final
>   RNN-03 Vehículo no sale sin 80% de pago mínimo
>   RNN-05 Separación de universos en query de BD
>   RNT-01 Hardware tecnimoto como contorno de RNF
>   RNT-05 4G baja recepción para S4 — tolerancia
>           30 segundos sin pérdida de estado

---

### 5.1 HU internas — equipo Tecnimotos Santi

---

#### HU-INT-01 — Gestionar precio de venta de repuesto

**Módulo:** `catalogo`

**Qué construir:**
- Endpoint `PATCH /catalogo/repuestos/{repuesto_id}/precio`
  — solo accesible para `ADMINISTRADOR` y `SUPERADMIN`
- Caso de uso `ActualizarPrecioVentaUseCase`
- Al actualizar: registrar precio anterior en historial
  con timestamp · publicar evento
  `repuesto.precio_actualizado` hacia `pedidos`
  y `taller`
- Endpoint `GET /catalogo/repuestos/{repuesto_id}/historial-precio`
  — solo accesible para `ADMINISTRADOR` y `SUPERADMIN`
- Verificación de RBAC en el endpoint: cualquier rol
  distinto a `ADMINISTRADOR` o `SUPERADMIN` recibe
  HTTP 403 con mensaje en lenguaje de negocio

**Escenario 1 — Registro de precio en repuesto existente**
```gherkin
Given el ADMINISTRADOR está autenticado con MFA completado
  And existe repuesto con codigo "REP-001" y universo "mototaxi"
  And el precio_venta actual es 45.00
When el ADMINISTRADOR envía PATCH /catalogo/repuestos/{id}/precio
     con body {"precio_venta": 52.00}
Then el sistema retorna HTTP 200
  And el repuesto tiene precio_venta 52.00 en base de datos
  And el historial registra precio_anterior 45.00
       con timestamp de la modificación
  And el evento repuesto.precio_actualizado fue publicado
       en Redis Streams con payload completo
  And ningún otro rol puede ejecutar esta operación
```

**Escenario 2 — Intento de modificación por rol no autorizado**
```gherkin
Given un VENDEDOR está autenticado
  And existe repuesto con codigo "REP-001"
When el VENDEDOR envía PATCH /catalogo/repuestos/{id}/precio
     con body {"precio_venta": 52.00}
Then el sistema retorna HTTP 403
  And el mensaje es "Solo el ADMINISTRADOR puede modificar precios"
  And el precio del repuesto no cambió en base de datos
  And el intento quedó registrado en log de auditoría
       con actor_id, timestamp y acción intentada
```

**Escenario 3 — Precio actualizado notifica pedidos en borrador**
```gherkin
Given existe pedido en estado BORRADOR
  And el pedido contiene repuesto con codigo "REP-001"
  And el ADMINISTRADOR actualiza el precio de "REP-001" a 52.00
When pedidos consume el evento repuesto.precio_actualizado
Then el cliente recibe notificación de cambio de precio
  And el pedido permanece en estado BORRADOR
  And el pedido con pago activo confirmado
       no recibe ninguna modificación de precio
```

---

#### HU-INT-02 — Abrir orden de trabajo con lista de repuestos

**Módulo:** `taller`

**Qué construir:**
- Endpoint `POST /taller/ordenes` — accesible para
  `MECANICO_MASTER` y `ADMINISTRADOR`
- Endpoint `POST /taller/ordenes/{id}/lista-repuestos`
  — para armar lista antes de ejecutar
- Endpoint `POST /taller/ordenes/{id}/aprobacion-cliente`
  — registra aprobación del cliente con timestamp
- Endpoint `POST /taller/ordenes/{id}/autorizar-precio`
  — autorización manual de visibilidad de precio
  para el cliente — solo `MECANICO_MASTER`,
  `ADMINISTRADOR` o `VENDEDOR`
- Caso de uso `AbrirOrdenTrabajoUseCase`
- Caso de uso `PresentarListaClienteUseCase`
- Bloqueo de transición a `EN_EJECUCION` sin
  aprobación registrada del cliente

**Escenario 1 — Apertura con campos obligatorios**
```gherkin
Given el MECANICO_MASTER está autenticado
  And el vehículo con vehiculo_id "VEH-001" ingresó al taller
When el mecánico envía POST /taller/ordenes con body:
     {
       "vehiculo_id": "VEH-001",
       "tipo_servicio": "correctivo",
       "tipo_urgencia": "alta",
       "mecanico_id": "MEC-001"
     }
Then el sistema retorna HTTP 201
  And la orden_trabajo existe en base de datos
       con estado ABIERTA y timestamp de apertura
  And el evento orden_trabajo.abierta fue publicado
```

**Escenario 2 — Lista presentada al cliente**
```gherkin
Given existe orden_trabajo "OT-001" en estado ABIERTA
  And el mecánico armó lista con dos repuestos:
      {"repuesto_id": "REP-001", "cantidad": 1}
      {"repuesto_id": "REP-002", "cantidad": 2}
When el mecánico declara la lista completa en
     POST /taller/ordenes/OT-001/lista-repuestos
Then el sistema consulta precio vigente a catalogo
       para cada repuesto de la lista
  And calcula monto_estimado = suma de precios * cantidades
  And retorna al cliente: lista de repuestos,
       precio unitario de cada uno, monto_estimado
       y costo de mano de obra estimado
  And la orden_trabajo permanece en LISTA_REPUESTOS
  And el endpoint POST .../iniciar-ejecucion retorna
       HTTP 409 si se intenta sin aprobación del cliente
```

**Escenario 3 — Cliente aprueba la lista**
```gherkin
Given existe orden_trabajo "OT-001" en estado LISTA_REPUESTOS
  And la lista y monto fueron presentados al cliente
When el cliente confirma su aprobación en
     POST /taller/ordenes/OT-001/aprobacion-cliente
Then el sistema retorna HTTP 200
  And la aprobación queda registrada con timestamp
  And la orden_trabajo pasa a estado EN_EJECUCION
  And stock verifica disponibilidad de cada repuesto
       de la lista al consumir orden_trabajo.lista_aprobada
```

**Escenario 4 — Repuesto sin stock al verificar**
```gherkin
Given existe orden_trabajo "OT-001" en EN_EJECUCION
  And la lista incluye repuesto "REP-003"
  And stock retorna cantidad_disponible 0 para "REP-003"
When stock procesa la verificación de disponibilidad
Then el ADMINISTRADOR recibe alerta de repuesto sin stock
  And el mecánico recibe alerta en su interfaz
  And la orden_trabajo permanece en EN_EJECUCION
       con "REP-003" marcado como pendiente
  And stock evalúa activar reabastecimiento urgente
```

**Escenario 5 — Autorización manual de visibilidad de precio**
```gherkin
Given existe orden_trabajo "OT-001" en EN_EJECUCION
  And el MECANICO_MASTER decide que el cliente
      necesita ver precios para decidir
When el MECANICO_MASTER envía
     POST /taller/ordenes/OT-001/autorizar-precio
     con body {"cliente_id": "CLI-001"}
Then el sistema retorna HTTP 200
  And el cliente accede a precio completo del catálogo
       durante esa sesión vinculada a "OT-001"
  And la autorización queda registrada en log
       con actor_id del MECANICO_MASTER y timestamp
  And un MECANICO_JUNIOR que intente el mismo endpoint
       recibe HTTP 403
```

---

#### HU-INT-03 — Registrar costo adicional durante ejecución

**Módulo:** `taller` + `pedidos`

**Qué construir:**
- Endpoint `POST /taller/ordenes/{id}/repuestos`
  — agrega repuesto durante `EN_EJECUCION`
  Accesible para `MECANICO_MASTER`, `MECANICO_JUNIOR`,
  `ADMINISTRADOR`, `VENDEDOR`
- Caso de uso `AgregarRepuestoEnEjecucionUseCase`
- Lógica de tramos de precio en `pedidos`:
  al consumir `orden_trabajo.repuesto_agregado`
  evalúa el precio_vigente del repuesto y aplica:
  - < S/30 → registra aprobación automática
  - S/30–S/100 → inicia espera de 30 min
    → si no hay respuesta → registra aprobación tácita
  - > S/100 → bloquea avance hasta confirmación
    explícita del cliente

**Escenario 1 — Repuesto adicional menor a S/30**
```gherkin
Given existe orden_trabajo "OT-001" en EN_EJECUCION
  And el mecánico agrega repuesto "REP-010"
       con precio_vigente 25.00
When el mecánico envía
     POST /taller/ordenes/OT-001/repuestos
     con body {"repuesto_id": "REP-010", "cantidad": 1}
Then el sistema retorna HTTP 201
  And el evento orden_trabajo.repuesto_agregado
       fue publicado con monto_actualizado correcto
  And pedidos registra aprobación automática
       sin esperar confirmación del cliente
  And el cliente recibe notificación del nuevo monto total
  And el repuesto queda en la lista de la orden
```

**Escenario 2 — Repuesto adicional entre S/30 y S/100**
```gherkin
Given existe orden_trabajo "OT-001" en EN_EJECUCION
  And el mecánico agrega repuesto "REP-011"
       con precio_vigente 65.00
When el evento orden_trabajo.repuesto_agregado
     llega a pedidos con monto_actualizado
Then pedidos notifica al cliente con el nuevo monto
  And pedidos inicia temporizador de 30 minutos
  And si el cliente no responde en 30 minutos
       pedidos registra aprobación tácita
  And el trabajo continúa y el repuesto queda en lista
  And si el cliente confirma antes de los 30 min
       pedidos registra aprobación explícita con timestamp
```

**Escenario 3 — Repuesto adicional mayor a S/100**
```gherkin
Given existe orden_trabajo "OT-001" en EN_EJECUCION
  And el mecánico agrega repuesto "REP-012"
       con precio_vigente 150.00
When el evento orden_trabajo.repuesto_agregado
     llega a pedidos con precio_vigente 150.00
Then pedidos notifica al cliente con el nuevo monto
  And pedidos bloquea avance de la orden_trabajo
  And el endpoint de avance retorna HTTP 409
       con mensaje: "Esperando confirmación del cliente
       para repuesto mayor a S/100"
  And el bloqueo no se levanta sin confirmación
       explícita del cliente bajo ninguna condición
```

**Escenario 4 — Cliente rechaza el costo adicional**
```gherkin
Given pedidos espera confirmación de un adicional
  And el cliente envía rechazo explícito
When pedidos recibe el rechazo
Then el repuesto adicional se retira de la lista
  And el monto_estimado vuelve al total anterior aprobado
  And el mecánico recibe notificación del rechazo
  And la orden_trabajo continúa sin ese repuesto
  And el trabajo no se interrumpe por el rechazo
```

---

#### HU-INT-04 — Cerrar orden de trabajo y coordinar cobro

**Módulo:** `taller` + `pedidos`

**Qué construir:**
- Endpoint `POST /taller/ordenes/{id}/revision-final`
  — solo `MECANICO_MASTER`, `ADMINISTRADOR`, `VENDEDOR`
- Endpoint `POST /taller/ordenes/{id}/excepcion-pago`
  — registra aprobación conjunta de excepción del 80%
  — requiere firma de `ADMINISTRADOR` y `MECANICO_MASTER`
- Caso de uso `DeclararRevisionFinalUseCase`
- Caso de uso `CerrarOrdenTrabajoUseCase`
  — se activa al consumir `cobro.confirmado`
- Operación atómica en `stock` al consumir
  `orden_trabajo.cerrada` — transacción única
  para todos los repuestos de la lista

**Escenario 1 — Declaración de revisión final**
```gherkin
Given existe orden_trabajo "OT-001" en EN_EJECUCION
  And el MECANICO_MASTER verificó todos los repuestos
When el mecánico envía
     POST /taller/ordenes/OT-001/revision-final
     con body:
     {
       "repuestos_consumidos": [
         {"repuesto_id": "REP-001", "cantidad": 1,
          "precio_unitario": 45.00},
         {"repuesto_id": "REP-002", "cantidad": 2,
          "precio_unitario": 30.00}
       ],
       "costo_mano_obra": 80.00,
       "mecanico_id": "MEC-001"
     }
Then el sistema retorna HTTP 200
  And la orden_trabajo pasa a estado REVISION_FINAL
  And el evento orden_trabajo.revision_final fue publicado
  And pedidos recibe la lista y calcula monto_total 185.00
  And pedidos habilita el cobro al cliente
```

**Escenario 2 — Cobro completo y liberación**
```gherkin
Given existe orden_trabajo "OT-001" en REVISION_FINAL
  And pedidos ejecutó el cobro del monto_total completo
When pedidos publica evento cobro.confirmado
     con monto_pagado igual a monto_total
     y deuda_activa 0
Then taller pasa orden_trabajo a estado CERRADA
  And stock ejecuta descuento atómico de todos
       los repuestos en una sola transacción
  And si algún repuesto no puede descontarse
       → rollback completo → ninguno se descuenta
       → taller bloquea cierre hasta resolución
  And el vehículo queda habilitado para prueba de ruta
  And el sistema registra timestamp de cierre
```

**Escenario 3 — Excepción del 80%**
```gherkin
Given existe orden_trabajo "OT-001" en REVISION_FINAL
  And el monto_total es 200.00
  And el cliente paga 170.00 (85% del total)
  And ADMINISTRADOR y MECANICO_MASTER aprueban la excepción
When se registra el pago parcial con plazo acordado 7 días
     en POST /taller/ordenes/OT-001/excepcion-pago
Then el sistema retorna HTTP 200
  And pedidos registra deuda_activa 30.00
       con fecha_limite calculada a 7 días
  And el sistema programa alerta al día 3 (50% del plazo)
  And el sistema programa alerta al día 6 (día antes)
  And ambas alertas van al cliente y a ADMINISTRADOR
       y VENDEDOR
  And cobro.confirmado se publica con deuda_activa 30.00
  And taller recibe la señal y libera el vehículo
```

**Escenario 4 — Pago bajo el 80% sin aprobación**
```gherkin
Given existe orden_trabajo "OT-001" en REVISION_FINAL
  And el monto_total es 200.00
  And el cliente paga 140.00 (70% del total)
  And no hay aprobación conjunta registrada
When pedidos intenta confirmar el cobro parcial
Then el sistema retorna HTTP 409
  And el vehículo no se libera bajo ninguna condición
  And el ADMINISTRADOR recibe notificación
       para resolver manualmente
  And la orden_trabajo permanece en REVISION_FINAL
```

**Escenario 5 — Discrepancia entre lista y stock**
```gherkin
Given taller envió lista verificada a pedidos
  And pedidos detecta que "REP-001" en la lista
       no tiene movimiento registrado en stock
When pedidos valida la lista contra stock
Then pedidos retorna HTTP 409 al endpoint de cobro
  And el cierre queda bloqueado
  And ADMINISTRADOR recibe notificación con detalle
       de la discrepancia: repuesto_id y cantidad
  And la orden_trabajo permanece en REVISION_FINAL
       hasta resolución manual
```

---

#### HU-INT-05 — Emitir y aprobar comprobante

**Módulo:** `pedidos`

**Qué construir:**
- Endpoint `POST /pedidos/{id}/comprobante`
  — genera comprobante en `PENDIENTE_VALIDACION`
  Accesible para `VENDEDOR`, `ADMINISTRADOR`,
  `SUPERADMIN`
- Endpoint `POST /pedidos/comprobantes/{id}/aprobar`
  — aprueba y emite ante SUNAT
  Solo `ADMINISTRADOR` y `SUPERADMIN`
- Endpoint `POST /pedidos/comprobantes/{id}/anular`
  — genera nota de crédito · marca como `ANULADO`
  Solo `ADMINISTRADOR` y `SUPERADMIN`
- Lógica de umbrales: boleta si monto > S/20 ·
  factura si monto > S/60 con RUC del cliente
- El agente no implementa `DELETE` sobre comprobante
  bajo ninguna condición

**Escenario 1 — VENDEDOR genera comprobante pendiente**
```gherkin
Given el VENDEDOR ejecutó el cobro de pedido "PED-001"
  And el monto_total es 75.00
When el VENDEDOR envía
     POST /pedidos/PED-001/comprobante
     con body {"tipo": "boleta"}
Then el sistema retorna HTTP 201
  And el comprobante existe con estado PENDIENTE_VALIDACION
  And el evento comprobante.pendiente_validacion
       fue publicado
  And ADMINISTRADOR recibe notificación para aprobación
  And el comprobante no fue emitido ante SUNAT
```

**Escenario 2 — ADMINISTRADOR aprueba y emite**
```gherkin
Given existe comprobante "COMP-001"
     en estado PENDIENTE_VALIDACION
When el ADMINISTRADOR envía
     POST /pedidos/comprobantes/COMP-001/aprobar
Then el sistema retorna HTTP 200
  And el comprobante pasa a estado EMITIDO
  And se registra la emisión ante SUNAT
       (integración o mock en MVP)
  And el cliente recibe copia del comprobante
  And el comprobante queda en historial del pedido
```

**Escenario 3 — Transacción bajo umbral sin comprobante**
```gherkin
Given el monto de la transacción es 15.00
  And el cliente no solicita comprobante
When se cierra la transacción
Then el sistema registra la venta sin emitir comprobante
  And la venta queda en historial interno con trazabilidad
  And el campo comprobante_id del pedido queda en null
```

**Escenario 4 — Factura con RUC del cliente**
```gherkin
Given el monto de la transacción es 200.00
  And el cliente proporciona RUC "20123456789"
When el ADMINISTRADOR aprueba la emisión
Then el sistema emite factura electrónica
  And la factura incluye el RUC del cliente
  And el comprobante pasa a estado EMITIDO
  And queda registrado en historial del pedido
```

**Escenario 5 — Anulación de comprobante emitido**
```gherkin
Given existe comprobante "COMP-001" en ENVIADO_CLIENTE
  And se detectó un error en su contenido
When el ADMINISTRADOR envía
     POST /pedidos/comprobantes/COMP-001/anular
Then el sistema retorna HTTP 200
  And se genera nota de crédito electrónica ante SUNAT
  And el comprobante pasa a estado ANULADO
  And el registro original permanece en base de datos
  And el endpoint DELETE /comprobantes/{id} retorna
       HTTP 405 — método no permitido bajo ninguna condición
```

**Escenario 6 — Cliente solicita comprobante bajo umbral**
```gherkin
Given el monto de la transacción es 15.00
  And el cliente solicita comprobante explícitamente
When el VENDEDOR genera el comprobante bajo solicitud
Then el comprobante se crea en PENDIENTE_VALIDACION
  And ADMINISTRADOR recibe notificación para aprobación
  And el comprobante no se emite sin aprobación
       de ADMINISTRADOR bajo ninguna condición
```

---

#### HU-INT-06 — Gestionar disponibilidad del taller

**Módulo:** `taller`

**Qué construir:**
- Endpoint `GET /taller/disponibilidad`
  Accesible para `SUPERADMIN`, `ADMINISTRADOR`,
  `VENDEDOR`, `MECANICO_MASTER` y `CLIENTE`
  (vista reducida para cliente)
- Endpoint `POST /taller/lista-espera`
  — registra vehículo en lista de espera
- El endpoint no expone nombres de otros clientes
  ni detalles de órdenes activas al rol `CLIENTE`

**Escenario 1 — Consulta de disponibilidad**
```gherkin
Given un rol autorizado accede al sistema
When envía GET /taller/disponibilidad
Then el sistema retorna HTTP 200 con:
     - por cada mecanico activo:
       mecanico_id, nombre, orden_trabajo_id si existe,
       tipo_servicio en curso y tipo_urgencia
     - espacios_ocupados y espacios_totales
  And la información refleja estado en tiempo real
  And el rol CLIENTE recibe solo:
       disponible: true/false y tiempo_estimado
       sin datos internos del taller
```

**Escenario 2 — Taller al máximo de capacidad**
```gherkin
Given todos los mecánicos tienen orden_trabajo activa
When cualquier rol consulta GET /taller/disponibilidad
Then el sistema retorna disponible: false
  And retorna estimacion_proximo_espacio con
       el tiempo calculado desde las órdenes activas
  And el endpoint POST /taller/lista-espera
       está habilitado para registrar el vehículo
```

**Escenario 3 — Mecánico preferido ocupado**
```gherkin
Given el cliente tiene mecanico_preferido_id "MEC-001"
     registrado en su historial
  And "MEC-001" tiene orden_trabajo activa
When el CLIENTE consulta GET /taller/disponibilidad
Then el sistema retorna:
     mecanico_preferido_disponible: false
     tiempo_estimado_liberacion: calculado
  And ofrece asignacion_alternativa con mecánicos
       disponibles sin revelar nombres de clientes
       ni detalles de la orden activa del preferido
```

---

#### HU-INT-07 — Control de acceso por rol

**Módulo:** transversal

**Qué construir:**
- Middleware de autenticación JWT RS256 (ADR-007)
  aplicado a todos los endpoints del sistema
- Middleware de autorización RBAC usando la
  tabla de §4.1 como fuente de verdad
- Log de auditoría para todo intento de acceso
  no autorizado: actor_id · endpoint · timestamp
  · resultado
- MFA obligatorio para `SUPERADMIN` y `ADMINISTRADOR`
  en cada sesión nueva

**Escenario 1 — Acceso correcto por rol**
```gherkin
Given cualquier usuario está autenticado con su rol
  And intenta acceder a una función permitida
       para ese rol según tabla §4.1
When envía la solicitud al endpoint correspondiente
Then el sistema permite la acción con HTTP 200 o 201
  And no requiere pasos adicionales de verificación
```

**Escenario 2 — Intento de acceso fuera del rol**
```gherkin
Given un VENDEDOR autenticado intenta
     POST /catalogo/repuestos/{id}/precio
When el sistema evalúa el rol contra la tabla §4.1
Then retorna HTTP 403
  And el mensaje es "Acción no permitida para tu rol"
  And no expone información sobre la restricción
       más allá del mensaje estándar
  And registra en log: actor_id, endpoint intentado
       y timestamp
```

**Escenario 3 — Precio de costo solo para ADMINISTRADOR**
```gherkin
Given un VENDEDOR autenticado accede al catálogo
When visualiza cualquier repuesto vía
     GET /catalogo/repuestos/{id}
Then el campo precio_costo no aparece en el response
  And el campo margen no aparece en el response
  And solo precio_venta es visible para ese rol
```

**Escenario 4 — Descuento invisible para roles no autorizados**
```gherkin
Given un VENDEDOR procesa pedido "PED-001"
  And el ADMINISTRADOR aplicó descuento de 10.00
       sobre ese pedido
When el VENDEDOR consulta GET /pedidos/PED-001
Then el response muestra precio_final correcto
  And el campo descuento_aplicado no existe
       en el response para ese rol
  And el cliente tampoco ve el descuento en ningún
       endpoint del sistema
```

**Escenario 5 — MFA obligatorio para roles críticos**
```gherkin
Given SUPERADMIN o ADMINISTRADOR intenta iniciar sesión
  And proporcionó credenciales correctas
When el sistema valida las credenciales
Then el sistema exige segundo factor de autenticación
  And sin MFA completado el token JWT no se emite
  And el acceso al sistema no se otorga
       bajo ninguna condición sin MFA completado
```

---

### 5.2 HU segmento S1 — Conductor individual

---

#### HU-S1-01 — Consultar disponibilidad de repuesto

**Módulo:** `catalogo`

**Qué construir:**
- Endpoint `GET /catalogo/repuestos`
  con parámetros: `universo` · `modelo` · `año`
- Endpoint `GET /catalogo/repuestos/{codigo}`
  búsqueda por código exacto
- El endpoint aplica filtro de universo en query
  de base de datos — no en código posterior
- El response incluye solo repuestos con
  stock `disponible` > 0
- Repuestos de categoría `tecnico_especializado`
  incluyen campo `advertencia_instalacion: true`

**Escenario 1 — Búsqueda exitosa con stock disponible**
```gherkin
Given el CLIENTE_CONDUCTOR está autenticado
  And existen repuestos con universo "mototaxi"
       modelo "Bajaj RE" año 2019 con stock disponible
When envía GET /catalogo/repuestos
     ?universo=mototaxi&modelo=Bajaj RE&año=2019
Then el sistema retorna HTTP 200 con lista de repuestos
  And cada repuesto incluye:
       codigo, nombre, precio_venta (si tiene permiso),
       stock_disponible y advertencia_instalacion
  And ningún repuesto con stock_disponible 0
       aparece en el resultado
  And ningún repuesto de universo "motolineal"
       aparece en el resultado
  And stock apartado no se cuenta como disponible
```

**Escenario 2 — Repuesto sin stock disponible**
```gherkin
Given el CLIENTE_CONDUCTOR busca repuesto "REP-050"
  And ese repuesto tiene stock_disponible 0
When envía GET /catalogo/repuestos/REP-050
Then el sistema retorna HTTP 200 con:
     disponible: false
     opcion_notificacion: true
  And no muestra stock apartado como disponible
  And el cliente puede solicitar notificación
       de llegada sin crear pedido
```

**Escenario 3 — Búsqueda por código con código inexistente**
```gherkin
Given el CLIENTE_CONDUCTOR busca código "REP-999"
  And ese código no existe en el catálogo
When envía GET /catalogo/repuestos/REP-999
Then el sistema retorna HTTP 404 con mensaje:
     "Código no encontrado — intenta con modelo y año"
  And no retorna ningún repuesto de otro universo
       como sugerencia
```

**Escenario 4 — Repuesto de categoría técnica especializada**
```gherkin
Given existe repuesto "REP-060" con
     categoria "tecnico_especializado"
     y stock_disponible 3
When el CLIENTE_CONDUCTOR consulta ese repuesto
Then el response incluye
     advertencia_instalacion: true
     mensaje: "Requiere instalación por mecánico certificado"
  And el cliente puede continuar la consulta o reservar
  And si procede a reservar la advertencia queda
       registrada en el campo advertencias del pedido
```

---

#### HU-S1-02 — Reservar repuesto antes de ir a la tienda

**Módulo:** `pedidos` + `stock`

**Qué construir:**
- Endpoint `POST /pedidos/reservas`
  — crea reserva con tiempo diferenciado por segmento
  `CLIENTE_CONDUCTOR` → `expira_en`: 1 día
  `CLIENTE_DISTRITO` y `CLIENTE_RURAL` → 2-3 días
- Job programado que evalúa reservas cada hora:
  si `ACTIVA` y sin pago ni retiro y se enviaron
  3 notificaciones → libera automáticamente →
  publica `reserva.liberada` con motivo `EXPIRADA`
- Endpoint `DELETE /pedidos/reservas/{id}`
  — liberación manual por `ADMINISTRADOR` o `VENDEDOR`

**Escenario 1 — Reserva exitosa sin pago**
```gherkin
Given el CLIENTE_CONDUCTOR está autenticado
  And el repuesto "REP-001" tiene stock_disponible 2
When envía POST /pedidos/reservas con body:
     {"repuesto_id": "REP-001", "cantidad": 1}
Then el sistema retorna HTTP 201 con:
     reserva_id, estado ACTIVA,
     expira_en (ahora + 1 día),
     repuesto nombre y dirección de tienda
  And stock descuenta 1 unidad de disponible a apartado
  And el evento reserva.creada fue publicado
  And GET /catalogo/repuestos/REP-001 retorna
       stock_disponible 1 (no 2)
```

**Escenario 2 — Reserva con pago anticipado**
```gherkin
Given el CLIENTE_CONDUCTOR crea reserva
  And registra pago anticipado en el mismo flujo
When el pago se registra exitosamente
Then la reserva pasa a estado CONFIRMADA
  And el campo expira_en queda en null
  And la reserva no expira bajo ninguna condición
  And el cliente recibe número de referencia del pago
```

**Escenario 3 — Reserva expirada por falta de respuesta**
```gherkin
Given existe reserva "RES-001" en estado ACTIVA
  And han pasado 1 día sin pago ni retiro
  And el sistema envió 3 notificaciones sin respuesta
When el job programado evalúa la reserva
Then el sistema publica reserva.liberada
     con motivo "EXPIRADA"
  And stock devuelve 1 unidad de apartado a disponible
  And el cliente recibe notificación de expiración
  And la reserva pasa a estado EXPIRADA
```

**Escenario 4 — Reserva liberada por prioridad del taller**
```gherkin
Given existe reserva "RES-001" en ACTIVA sin pago
  And el cliente recibió al menos 1 notificación previa
  And taller necesita el repuesto para "OT-001"
When taller solicita liberación por prioridad
Then el sistema publica reserva.prioridad_taller
  And stock libera el apartado de inmediato
  And el cliente recibe notificación:
       "Tu reserva fue liberada por prioridad del taller"
       con opción de crear nueva reserva
  And la reserva pasa a estado LIBERADA
```

---

#### HU-S1-03 — Consultar disponibilidad del taller

**Módulo:** `taller`

**Qué construir:**
- Reutiliza `GET /taller/disponibilidad` de HU-INT-06
- Vista reducida para rol `CLIENTE`:
  solo `disponible` · `tiempo_estimado` ·
  `mecanico_preferido_disponible` si tiene preferido
- Endpoint `POST /taller/lista-espera`
  para registrar vehículo si no hay disponibilidad

**Escenario 1 — Taller con espacio disponible**
```gherkin
Given el CLIENTE_CONDUCTOR consulta disponibilidad
When envía GET /taller/disponibilidad
Then el sistema retorna HTTP 200 con:
     disponible: true
     tiempo_estimado_atencion: en minutos
  And el response no incluye nombres de otros clientes
  And el response no incluye detalles de órdenes activas
```

**Escenario 2 — Mecánico preferido disponible**
```gherkin
Given el cliente tiene mecanico_preferido_id registrado
  And ese mecánico está disponible
When el cliente consulta GET /taller/disponibilidad
Then el response incluye:
     mecanico_preferido_disponible: true
  And ofrece opción de registrar llegada anticipada
```

**Escenario 3 — Mecánico preferido ocupado**
```gherkin
Given el cliente tiene mecanico_preferido_id registrado
  And ese mecánico tiene orden_trabajo activa
When el cliente consulta GET /taller/disponibilidad
Then el response incluye:
     mecanico_preferido_disponible: false
     tiempo_estimado_liberacion: calculado
     alternativa_disponible: true o false
  And el cliente puede elegir esperar al preferido
       o ser atendido por otro mecánico disponible
  And el sistema no fuerza la asignación
```

**Escenario 4 — Taller sin disponibilidad inmediata**
```gherkin
Given todos los mecánicos tienen orden_trabajo activa
When el CLIENTE_CONDUCTOR consulta disponibilidad
Then el response incluye:
     disponible: false
     estimacion_proximo_espacio: datetime calculado
  And el endpoint POST /taller/lista-espera
       está disponible para registrar el vehículo
```

---

#### HU-S1-04 — Recibir notificación de estado

**Módulo:** `pedidos` + `stock`

**Qué construir:**
- Sistema de notificaciones push integrado en
  cada cambio de estado de `pedido` y `reserva`
- Endpoint `POST /pedidos/notificaciones/suscribir`
  — cliente se suscribe a notificaciones de un
  repuesto sin stock
- Las notificaciones se envían sin acción del cliente
- Para S4: reintento automático hasta 3 veces
  en intervalos de 10 minutos si falla el envío

**Escenario 1 — Notificación de cambio de estado de pedido**
```gherkin
Given el CLIENTE_CONDUCTOR tiene pedido "PED-001"
     en cualquier estado activo
When el estado del pedido cambia a cualquier valor nuevo
Then el cliente recibe notificación con:
     estado_nuevo, nombre del repuesto
     y próximo_paso esperado
  And la notificación llega sin acción del cliente
  And el cliente no necesita consultar activamente
```

**Escenario 2 — Notificación de reserva próxima a expirar**
```gherkin
Given la reserva "RES-001" lleva más del 50%
     de su tiempo sin pago ni retiro
When el sistema detecta el umbral de tiempo
Then envía primera notificación de recordatorio
  And si no hay respuesta envía segunda notificación
  And si no hay respuesta envía tercera notificación
  And tras la tercera sin respuesta libera la reserva
```

**Escenario 3 — Notificación de repuesto llegado**
```gherkin
Given el cliente solicitó notificación para "REP-050"
  And stock registra recepción del reabastecimiento
When stock publica stock.disponible para "REP-050"
Then el cliente recibe notificación:
     "Tu repuesto [nombre] ya está disponible"
  And la notificación incluye acción directa
       para reservar sin abrir el catálogo
```

---

#### HU-S1-05 — Ver precio unificado

**Módulo:** `catalogo`

**Qué construir:**
- Lógica de niveles de visibilidad de precio
  declarada en §4.2
- Contador de consultas de precio por sesión
  almacenado en Redis con TTL de sesión
- El endpoint retorna `precio_venta: null` y
  `precio_visible: false` para visitantes sin cuenta
  y para clientes que superaron el límite de sesión

**Escenario 1 — Precio visible para cliente autenticado**
```gherkin
Given el CLIENTE_CONDUCTOR está autenticado
  And no ha superado 3 consultas de precio
       en la sesión actual
When envía GET /catalogo/repuestos/REP-001
     con header de acción explícita de precio
Then el sistema retorna precio_venta: 45.00
  And incrementa el contador de sesión en Redis
  And ese precio es el mismo que verá en la tienda
```

**Escenario 2 — Precio no visible para visitante**
```gherkin
Given un visitante accede sin autenticación
When envía GET /catalogo/repuestos/REP-001
Then el sistema retorna HTTP 200 con:
     precio_visible: false
     precio_venta: null
     disponible: true (si tiene stock)
  And el response incluye opción de registrarse
       para ver precios
```

**Escenario 3 — Precio congelado al confirmar pedido**
```gherkin
Given el CLIENTE_CONDUCTOR confirmó pedido "PED-001"
     con pago activo al precio 45.00
  And el ADMINISTRADOR actualiza el precio a 52.00
When se consulta GET /pedidos/PED-001
Then el pedido muestra precio_unitario 45.00
  And el nuevo precio 52.00 no afecta el pedido
       confirmado bajo ninguna condición
  And el cliente no recibe notificación de
       cambio de precio en su pedido cerrado
```

**Escenario 4 — Límite de consultas de precio alcanzado**
```gherkin
Given el CLIENTE_CONDUCTOR ya consultó precio
     en 3 repuestos distintos en la sesión actual
When intenta ver el precio de un cuarto repuesto
Then el sistema retorna:
     precio_visible: false
     precio_venta: null
     mensaje: "Para ver más precios visítanos
               en tienda o contáctanos"
  And la disponibilidad del repuesto sigue visible
  And el contador se reinicia en nueva sesión
```

---

#### HU-S1-06 — Registrar compra presencial en cuenta del cliente

**Módulo:** `pedidos`

**Qué construir:**
- Endpoint `POST /pedidos/presencial`
  — crea pedido en estado `ENTREGADO` directamente
  Accesible para `VENDEDOR` y `ADMINISTRADOR`
- Endpoint `POST /pedidos/presencial/anonimo`
  — registra venta sin cuenta de cliente vinculada
- El historial del cliente queda accesible desde
  su cuenta vía `GET /pedidos/mis-pedidos`

**Escenario 1 — Compra presencial con cuenta existente**
```gherkin
Given el CLIENTE_CONDUCTOR tiene cuenta registrada
  And el VENDEDOR está autenticado
When el VENDEDOR envía POST /pedidos/presencial con:
     {
       "cliente_id": "CLI-001",
       "repuestos": [
         {"repuesto_id": "REP-001", "cantidad": 1}
       ]
     }
Then el sistema retorna HTTP 201
  And el pedido existe en estado ENTREGADO
       vinculado a la cuenta del cliente
  And registra: repuestos, cantidades,
       precios vigentes del catálogo y timestamp
  And el cliente puede ver ese pedido en
       GET /pedidos/mis-pedidos desde su celular
```

**Escenario 2 — Compra presencial con cuenta nueva**
```gherkin
Given el CLIENTE_CONDUCTOR no tiene cuenta
  And acepta crear cuenta con nombre y contacto
When el VENDEDOR crea la cuenta y registra la compra
Then el sistema crea la cuenta con datos básicos
  And registra la compra vinculada a la cuenta nueva
  And el cliente recibe confirmación con acceso
       a su historial desde ese momento
```

**Escenario 3 — Cliente no quiere registrar cuenta**
```gherkin
Given el CLIENTE_CONDUCTOR no quiere crear cuenta
When el VENDEDOR envía POST /pedidos/presencial/anonimo
     con los repuestos comprados
Then el sistema registra la venta sin cliente_id
  And la venta queda en historial interno del negocio
  And el sistema no fuerza el registro bajo
       ninguna condición
```

**Escenario 4 — Historial visible para el cliente**
```gherkin
Given el CLIENTE_CONDUCTOR tiene compras registradas
When envía GET /pedidos/mis-pedidos
Then el sistema retorna lista de pedidos con:
     fecha, repuestos, cantidades y monto
  And el cliente puede reenviar un pedido anterior
       con acción directa desde el historial
  And el historial es visible solo para ese cliente
       y para ADMINISTRADOR y VENDEDOR
```
---
### 5.3 HU segmento S2 — Mecánico de distrito

---

#### HU-S2-01 — Consultar disponibilidad para pedido por lista

**Módulo:** `catalogo`

**Qué construir:**
- Endpoint `POST /catalogo/repuestos/consulta-lista`
  — recibe lista de códigos y retorna disponibilidad
  de todos en una sola respuesta
  Accesible para `CLIENTE_DISTRITO` y roles internos
- El response agrupa por estado:
  `disponibles` · `sin_stock` · `bajo_pedido`
- El cliente puede iniciar pedido directamente
  desde el response sin pasos adicionales

**Escenario 1 — Consulta múltiple por lista de códigos**
```gherkin
Given el CLIENTE_DISTRITO está autenticado
  And tiene lista: ["REP-001", "REP-002", "REP-003"]
  And "REP-001" tiene stock_disponible 3
  And "REP-002" tiene stock_disponible 0
  And "REP-003" tiene categoria "bajo_pedido"
When envía POST /catalogo/repuestos/consulta-lista
     con body {"codigos": ["REP-001","REP-002","REP-003"]}
Then el sistema retorna HTTP 200 con:
     disponibles: [{"codigo":"REP-001","stock":3,
                    "precio_venta":45.00}]
     sin_stock:   [{"codigo":"REP-002",
                    "opcion_notificacion":true}]
     bajo_pedido: [{"codigo":"REP-003",
                    "tiempo_estimado": "3-5 días"}]
  And el response incluye accion_pedido: true
       para que el cliente inicie pedido desde esa vista
```

**Escenario 2 — Repuesto en categoría bajo_pedido**
```gherkin
Given el CLIENTE_DISTRITO busca repuesto "REP-070"
  And ese repuesto tiene categoria "bajo_pedido"
When consulta ese código en la lista
Then el sistema retorna estado: "bajo_pedido"
  And retorna tiempo_estimado_reabastecimiento
       si está disponible en sistema
  And retorna opcion_incluir_en_pedido: true
       con condicion_espera declarada
  And el campo disponible: false es explícito
       en el response — nunca "bajo_pedido" como
       sinónimo de disponible
```

**Escenario 3 — Búsqueda por modelo y año sin código**
```gherkin
Given el CLIENTE_DISTRITO no tiene el código exacto
  And conoce modelo "Bajaj RE" y año 2021
When envía GET /catalogo/repuestos
     ?universo=mototaxi&modelo=Bajaj RE&año=2021
Then el sistema retorna todos los repuestos
     compatibles con ese modelo y año
  And cada repuesto incluye foto, nombre y código
  And el cliente puede agregar directamente al pedido
       desde esa vista con un solo paso adicional
```

---

#### HU-S2-02 — Crear pedido remoto por lista con proforma

**Módulo:** `pedidos`

**Qué construir:**
- Endpoint `POST /pedidos/lista`
  — crea pedido_por_lista en estado `BORRADOR`
  Solo `CLIENTE_DISTRITO` y roles internos
- Flujo de revisión de precio por `ADMINISTRADOR`
  antes de emitir proforma al cliente:
  el pedido entra en `BORRADOR` →
  Elena revisa y puede ajustar precio por ítem →
  solo después se genera la proforma con
  precio real para el cliente
- Campo `precio_ajustado` por ítem — invisible
  para cualquier rol distinto a `ADMINISTRADOR`
  y `SUPERADMIN`
- Endpoint `GET /pedidos/{id}/proforma`
  — genera y retorna documento proforma

**Escenario 1 — Creación de pedido por lista**
```gherkin
Given el CLIENTE_DISTRITO tiene lista confirmada:
     [{"repuesto_id":"REP-001","cantidad":2},
      {"repuesto_id":"REP-002","cantidad":1}]
When envía POST /pedidos/lista con esa lista
Then el sistema retorna HTTP 201
  And el pedido existe en estado BORRADOR
  And el pedido incluye precios base del catálogo
       como referencia — no como precio final
  And ADMINISTRADOR recibe notificación de pedido
       de distrito pendiente de revisión de precios
  And el cliente NO recibe la proforma aún —
       la recibe solo después de la aprobación
       de precios por ADMINISTRADOR
```

**Escenario 2 — Confirmación del pedido con proforma**
```gherkin
Given el ADMINISTRADOR revisó y aprobó precios
  And el CLIENTE_DISTRITO recibió la proforma
  And el cliente decide confirmar el pedido
When el cliente envía confirmación con método de pago
Then el pedido pasa a estado CONFIRMADO
  And stock reserva todos los repuestos disponibles
       de la lista de forma inmediata
  And el equipo de tienda recibe notificación:
       "Pedido de distrito confirmado — preparar despacho"
  And el cliente recibe confirmación con:
       estado CONFIRMADO, repuestos confirmados
       y próximo paso esperado
```

**Escenario 3 — Lista con repuestos parcialmente disponibles**
```gherkin
Given el pedido incluye "REP-001" con stock 3
  And el pedido incluye "REP-003" en bajo_pedido
When el ADMINISTRADOR genera la proforma
Then la proforma separa explícitamente:
     seccion_inmediata: repuestos con stock disponible
     seccion_espera: repuestos con tiempo de espera
  And el cliente puede confirmar solo los inmediatos
       o confirmar la lista completa con espera
  And la decisión del cliente queda registrada
       en el campo confirmacion_parcial del pedido
```

**Escenario 4 — Pedido cancelado antes de confirmar**
```gherkin
Given el pedido "PED-010" está en estado BORRADOR
When el CLIENTE_DISTRITO envía
     DELETE /pedidos/PED-010
Then el sistema retorna HTTP 200
  And el pedido queda eliminado de la base de datos
  And ningún movimiento de stock fue realizado
  And ningún cobro fue generado
  And el cliente puede crear nuevo pedido sin restricción
```

---

#### HU-S2-03 — Seguimiento de estado del pedido

**Módulo:** `pedidos`

**Qué construir:**
- Endpoint `GET /pedidos/mis-pedidos`
  — lista pedidos activos del cliente autenticado
- Endpoint `GET /pedidos/{id}`
  — detalle de pedido con estado actual y próximo paso
- Notificaciones automáticas en cada cambio de estado
  sin acción del cliente

**Escenario 1 — Consulta de estado activo**
```gherkin
Given el CLIENTE_DISTRITO tiene pedido "PED-010"
     en estado EN_PREPARACION
When envía GET /pedidos/PED-010
Then el sistema retorna HTTP 200 con:
     estado: "EN_PREPARACION"
     repuestos: lista con cantidades y estados
     fecha_confirmacion: timestamp
     proximo_paso: "Tu pedido está siendo preparado
                    para despacho"
  And el estado refleja la realidad en tiempo real
  And el cliente no necesita llamar para obtenerlo
```

**Escenario 2 — Notificación automática de cambio de estado**
```gherkin
Given el pedido "PED-010" cambia a DESPACHADO
When el sistema registra el cambio de estado
Then el CLIENTE_DISTRITO recibe notificación con:
     estado_nuevo: "DESPACHADO"
     significado: "Tu pedido fue entregado a la agencia"
     proximo_paso: "Recibirás el paquete en tu zona"
  And la notificación llega sin acción del cliente
```

**Escenario 3 — Repuesto bajo pedido llegó**
```gherkin
Given el pedido incluye "REP-003" en espera
  And stock confirma recepción del reabastecimiento
When stock publica reabastecimiento.recibido
     con "REP-003" incluido
Then el CLIENTE_DISTRITO recibe notificación:
     "Tu repuesto [nombre] llegó —
      tu pedido está listo para despacho"
  And el estado del pedido se actualiza
       automáticamente a EN_PREPARACION
```

---

#### HU-S2-04 — Coordinar envío de pedido a distrito

**Módulo:** `pedidos`

**Qué construir:**
- Endpoint `POST /pedidos/{id}/envio`
  — registra datos del envío cuando el pedido
  está en `EN_PREPARACION`
  Accesible para `ADMINISTRADOR` y `VENDEDOR`
- El pedido pasa a `DESPACHADO` al registrar el envío
- Endpoint `POST /pedidos/{id}/envio/confirmar-recepcion`
  — cliente confirma recepción → `ENTREGADO`
- Endpoint `POST /pedidos/{id}/envio/incidencia`
  — cliente reporta problema → `INCIDENCIA`

**Escenario 1 — Coordinación de envío al confirmar pedido**
```gherkin
Given el pedido "PED-010" está en EN_PREPARACION
  And el CLIENTE_DISTRITO está fuera de la ciudad
When el VENDEDOR envía POST /pedidos/PED-010/envio
     con body:
     {
       "numero_encomienda": "ENC-12345",
       "empresa_transporte": "Transportes Ayacucho",
       "fecha_estimada_entrega": "2026-06-20"
     }
Then el sistema retorna HTTP 201
  And el pedido pasa a estado DESPACHADO
  And el CLIENTE_DISTRITO recibe notificación con:
       numero_encomienda, empresa_transporte
       y fecha_estimada_entrega
```

**Escenario 2 — Confirmación de recepción por el cliente**
```gherkin
Given el pedido "PED-010" está en DESPACHADO
When el CLIENTE_DISTRITO envía
     POST /pedidos/PED-010/envio/confirmar-recepcion
Then el sistema retorna HTTP 200
  And el pedido pasa a estado ENTREGADO
  And se registra timestamp de entrega
  And el historial del pedido queda completo
       con trazabilidad desde BORRADOR hasta ENTREGADO
```

**Escenario 3 — Incidencia en el envío**
```gherkin
Given el pedido "PED-010" está en DESPACHADO
When el CLIENTE_DISTRITO reporta incidencia en
     POST /pedidos/PED-010/envio/incidencia
     con body {"descripcion": "Paquete no llegó"}
Then el sistema retorna HTTP 200
  And el pedido pasa a estado INCIDENCIA
  And ADMINISTRADOR recibe notificación con
       el detalle del reporte
  And el cliente recibe confirmación de que
       la incidencia fue registrada
  And la gestión posterior es manual por ADMINISTRADOR
```

---

#### HU-S2-05 — Notificación de llegada de repuesto bajo pedido

**Módulo:** `stock` + `pedidos`

**Qué construir:**
- Endpoint `POST /pedidos/notificaciones/suscribir`
  — cliente se suscribe a notificación de llegada
  de repuesto específico
- Al recibir `reabastecimiento.recibido` en `pedidos`:
  busca todas las suscripciones activas para ese
  repuesto → envía notificación a cada cliente →
  marca suscripciones como completadas
- Si el reabastecimiento es parcial: notifica a todos
  informando cantidad disponible

**Escenario 1 — Solicitud de notificación en repuesto sin stock**
```gherkin
Given el CLIENTE_DISTRITO consultó "REP-050"
  And ese repuesto tiene stock_disponible 0
When el cliente envía
     POST /pedidos/notificaciones/suscribir
     con body {"repuesto_id": "REP-050"}
Then el sistema retorna HTTP 201
  And la suscripción queda registrada vinculada
       a cliente_id y repuesto_id
  And el cliente recibe confirmación de suscripción
  And la suscripción permanece activa hasta que
       el repuesto llegue o el cliente la cancele
```

**Escenario 2 — Notificación automática al recibir stock**
```gherkin
Given existen suscripciones activas de 3 clientes
     para el repuesto "REP-050"
  And stock publica stock.disponible para "REP-050"
       con cantidad_nueva 10
When pedidos consume el evento stock.disponible
Then los 3 clientes reciben notificación:
     "Tu repuesto [nombre] ya está disponible —
      stock: 10 unidades"
  And la notificación incluye acción directa
       para crear pedido sin abrir el catálogo
  And las 3 suscripciones pasan a estado completada
```

**Escenario 3 — Reabastecimiento parcial**
```gherkin
Given existen 5 suscripciones activas para "REP-050"
  And el reabastecimiento llegó con 3 unidades
       cuando se esperaban 10
When stock publica stock.disponible con cantidad_nueva 3
Then los 5 clientes suscritos reciben notificación
     informando cantidad_disponible: 3
  And el mensaje indica que el stock es limitado
  And los pedidos se procesan por orden de confirmación
       — primero en confirmar, primero en ser atendido
  And el sistema no reserva automáticamente sin
       confirmación explícita del cliente
```

---

#### HU-S2-06 — Gestionar lista de reserva progresiva

**Módulo:** `pedidos` + `stock`

**Qué construir:**
- Entidad `ListaProgresiva` con vínculo a
  `CLIENTE_DISTRITO` — un cliente tiene una
  lista activa a la vez
- Endpoint `GET /pedidos/lista-progresiva`
  — retorna la lista actual del cliente con
  stock y precio vigentes en tiempo real
- Endpoint `POST /pedidos/lista-progresiva/items`
  — agrega ítem a la lista
- Endpoint `DELETE /pedidos/lista-progresiva/items/{id}`
  — elimina ítem de la lista
- Endpoint `POST /pedidos/lista-progresiva/formalizar`
  — convierte la lista en pedido formal →
  aplica flujo de HU-S2-02 desde ese punto
- Job programado: si la lista no tuvo cambios
  ni consultas en 7 días → envía notificación
  al cliente para que revise

**Escenario 1 — Agregar repuesto a lista progresiva**
```gherkin
Given el CLIENTE_DISTRITO está autenticado
  And accede a su lista progresiva activa
When envía POST /pedidos/lista-progresiva/items
     con body {"repuesto_id": "REP-001", "cantidad": 2}
Then el sistema retorna HTTP 201
  And el ítem se registra en la lista con:
       stock_referencia y precio_referencia
       del momento de agregado (solo informativo)
  And el response incluye advertencia_visible:
       "Stock y precio se actualizan en tiempo real —
        los valores actuales son referencia, no compromiso"
  And el repuesto NO queda apartado en stock
```

**Escenario 2 — Stock o precio cambia en ítem de la lista**
```gherkin
Given el CLIENTE_DISTRITO tiene "REP-001" en su lista
  And el precio de "REP-001" cambia de 45.00 a 52.00
When pedidos consume el evento
     repuesto.precio_actualizado para "REP-001"
Then el ítem en la lista se actualiza con
     precio_referencia: 52.00
  And el ítem queda marcado con
       indicador_cambio: "Precio actualizado"
  And el cliente recibe notificación:
       "Tu lista tiene cambios — revisa antes de pedir"
```

**Escenario 3 — Repuesto de la lista se agota**
```gherkin
Given el CLIENTE_DISTRITO tiene "REP-002" en su lista
  And stock publica stock.agotado para "REP-002"
When pedidos consume el evento stock.agotado
Then el ítem en la lista se marca con
     disponible: false
  And el cliente recibe notificación:
       "[Repuesto nombre] ya no tiene stock
        disponible en tu lista"
  And el ítem permanece en la lista —
       el cliente decide si espera o lo elimina
```

**Escenario 4 — Formalizar pedido desde lista progresiva**
```gherkin
Given el CLIENTE_DISTRITO quiere formalizar su lista
  And la lista tiene 3 ítems con stock disponible
When envía POST /pedidos/lista-progresiva/formalizar
Then el sistema toma stock y precio vigentes en
     ese momento exacto — no los valores de referencia
     del momento en que se agregaron los ítems
  And crea el pedido en estado BORRADOR
  And el cliente recibe confirmación de que
       los valores son los del momento de formalización
  And desde ese punto aplica flujo de HU-S2-02
```

**Escenario 5 — Lista sin actividad prolongada**
```gherkin
Given la lista del CLIENTE_DISTRITO no tuvo
     cambios ni consultas por más de 7 días
When el job programado detecta la inactividad
Then el sistema envía notificación al cliente:
     "Tu lista tiene ítems sin actividad —
      revisa disponibilidad actual"
  And la lista NO se elimina automáticamente
  And el cliente decide si la mantiene,
       limpia o formaliza
```

---

### 5.4 HU segmento S4 — Cliente rural

---

#### HU-S4-01 — Confirmar disponibilidad antes del viaje

**Módulo:** `catalogo`

**Qué construir:**
- Reutiliza `GET /catalogo/repuestos` de HU-S1-01
- El agente implementa respuesta optimizada para
  conexión degradada: payload mínimo sin imágenes
  pesadas en flujos críticos de S4
- Tiempo de respuesta del servidor ≤ 3 segundos
  bajo carga normal — medido en servidor, no en cliente
- Si la conexión se interrumpe durante la búsqueda
  y se restaura en ≤ 30 segundos → el sistema
  retoma sin pérdida de estado
- Si la interrupción supera 30 segundos → el sistema
  retorna mensaje claro y cancela limpiamente —
  nunca deja estado indeterminado

**Escenario 1 — Confirmación exitosa con conectividad degradada**
```gherkin
Given el CLIENTE_RURAL está autenticado
  And tiene conectividad 4G con recepción baja
  And seleccionó universo "mototaxi"
When envía GET /catalogo/repuestos
     ?universo=mototaxi&modelo=Bajaj RE&año=2019
Then el servidor responde en ≤ 3 segundos
  And retorna disponibilidad real:
       disponible: true/false o bajo_pedido
  And retorna precio_venta bajo demanda
       con el límite de sesión activo igual
       que otros segmentos
  And el resultado es confiable — no estimado
```

**Escenario 2 — Interrupción de conexión durante consulta**
```gherkin
Given el CLIENTE_RURAL inició búsqueda de "REP-001"
  And la conexión se interrumpe durante la consulta
When la conexión se restaura en menos de 30 segundos
Then el sistema retoma la operación
  And retorna el resultado sin necesidad de
       reiniciar la búsqueda desde cero
  And el cliente ve el resultado sin mensaje de error
When la interrupción supera 30 segundos
Then el sistema retorna HTTP 408 con mensaje:
     "Sin conexión — intenta de nuevo cuando tengas señal"
  And no deja ninguna operación en estado indeterminado
```

**Escenario 3 — Repuesto no disponible antes del viaje**
```gherkin
Given el CLIENTE_RURAL busca "REP-050"
  And ese repuesto tiene stock_disponible 0
When recibe el resultado
Then el sistema retorna:
     disponible: false
     tiempo_estimado_reabastecimiento: si existe
     opcion_notificacion: true
     repuestos_alternativos: lista de compatibles
       con el modelo y año del cliente si existen
  And el cliente tiene información suficiente
       para decidir sin hacer el viaje
```

**Escenario 4 — Repuesto técnico especializado**
```gherkin
Given el CLIENTE_RURAL encuentra "REP-060"
  And ese repuesto tiene categoria "tecnico_especializado"
When visualiza ese repuesto
Then el response incluye:
     advertencia_instalacion: true
     mensaje: "Requiere instalación por mecánico
               certificado — coordina tu visita
               antes de viajar"
     opcion_reservar_con_turno: true
  And el sistema no bloquea la compra —
       solo informa con claridad
```

---

#### HU-S4-02 — Reservar repuesto y coordinar visita

**Módulo:** `pedidos` + `stock` + `taller`

**Qué construir:**
- Reutiliza `POST /pedidos/reservas` de HU-S1-02
  con segmento `CLIENTE_RURAL` → `expira_en` 2-3 días
- Endpoint `POST /pedidos/reservas/{id}/coordinar-visita`
  — vincula la reserva con disponibilidad del taller
  para un día específico
- Tolerancia de 30 segundos ante interrupción de
  conexión durante el proceso de reserva:
  si la conexión cae antes de confirmar →
  ningún movimiento de stock se realizó →
  el cliente debe reiniciar
  si la conexión cae después de confirmar →
  la reserva existe y el stock fue descontado

**Escenario 1 — Reserva con tiempo extendido para rural**
```gherkin
Given el CLIENTE_RURAL está autenticado
  And el repuesto "REP-001" tiene stock_disponible 2
When envía POST /pedidos/reservas con body:
     {
       "repuesto_id": "REP-001",
       "cantidad": 1,
       "segmento": "CLIENTE_RURAL"
     }
Then el sistema retorna HTTP 201 con:
     reserva_id, estado ACTIVA,
     expira_en (ahora + 2 días mínimo),
     referencia para identificarse al llegar
  And stock descuenta 1 de disponible a apartado
  And el cliente recibe confirmación con:
       nombre del repuesto, tiempo de reserva
       y dirección de la tienda
```

**Escenario 2 — Reserva con pago anticipado antes del viaje**
```gherkin
Given el CLIENTE_RURAL quiere máxima certeza
  And realiza pago anticipado al crear la reserva
When el pago se registra exitosamente
Then la reserva pasa a estado CONFIRMADA
  And expira_en queda en null — no expira
  And el cliente recibe número de referencia
       verificable al llegar a la tienda
```

**Escenario 3 — Interrupción de conexión durante la reserva**
```gherkin
Given el CLIENTE_RURAL inició el proceso de reserva
  And la conexión se interrumpe antes de confirmar
When la conexión se restaura en menos de 30 segundos
Then el sistema retoma el proceso desde el punto
     de interrupción sin pérdida de datos ingresados
When la interrupción supera 30 segundos
Then el sistema cancela la operación de forma limpia
  And retorna mensaje: "Sin conexión — ninguna reserva
       fue creada, intenta de nuevo"
  And no realizó ningún movimiento de stock
  And ninguna reserva quedó en estado indeterminado
```

**Escenario 4 — Compatibilidad por modelo y año**
```gherkin
Given el CLIENTE_RURAL no sabe el código exacto
  And conoce modelo "Bajaj RE" y año 2020
When envía GET /catalogo/repuestos
     ?universo=mototaxi&modelo=Bajaj RE&año=2020
Then el sistema retorna repuestos compatibles
     con foto, nombre y código
  And el cliente puede identificar el repuesto
       visualmente sin conocer el código
  And puede reservar directamente desde esa vista
  And el sistema registra modelo y año del vehículo
       en el perfil del cliente para búsquedas futuras
```

---

#### HU-S4-03 — Pedido remoto con envío a zona rural

**Módulo:** `pedidos`

**Qué construir:**
- Endpoint `POST /pedidos/remoto`
  — crea pedido con dirección de destino y
  método de envío preferido
  Accesible para `CLIENTE_RURAL` y roles internos
- La proforma incluye costo de envío calculado
- Si la consulta del estado falla por conexión:
  el sistema retorna el último estado conocido
  con campo `ultima_actualizacion` timestamp

**Escenario 1 — Pedido remoto con solicitud de envío**
```gherkin
Given el CLIENTE_RURAL no puede viajar
  And el repuesto "REP-001" tiene stock_disponible 2
When envía POST /pedidos/remoto con body:
     {
       "repuesto_id": "REP-001",
       "cantidad": 1,
       "direccion_destino": "Comunidad Vinchos, Ayacucho",
       "metodo_envio": "encomienda"
     }
Then el sistema retorna HTTP 201
  And el pedido existe en estado BORRADOR
  And el sistema genera proforma con:
       precio del repuesto + costo_envio_estimado
  And el pedido permanece en BORRADOR hasta
       que el cliente confirme con pago
```

**Escenario 2 — Confirmación de pedido con pago**
```gherkin
Given el CLIENTE_RURAL revisó la proforma
  And decide confirmar el pedido
When registra el pago por el método acordado
Then el pedido pasa a CONFIRMADO
  And stock reserva el repuesto de inmediato
  And el cliente recibe confirmación con:
       datos del pedido y tiempo estimado de llegada
  And el equipo de tienda recibe notificación:
       "Pedido rural confirmado — preparar despacho"
```

**Escenario 3 — Seguimiento con conectividad limitada**
```gherkin
Given el pedido "PED-020" está en DESPACHADO
  And el CLIENTE_RURAL tiene conectividad 4G baja
When envía GET /pedidos/PED-020
Then el servidor responde en ≤ 3 segundos
  And retorna estado actual y datos de encomienda
  And la consulta no requiere conexión sostenida
When la conexión falla durante la consulta
Then el sistema retorna el último estado conocido con:
     estado: "DESPACHADO" (último registrado)
     ultima_actualizacion: timestamp
  And la pantalla no queda en blanco
```

---

#### HU-S4-04 — Notificaciones con conexión intermitente

**Módulo:** `pedidos` + `stock`

**Qué construir:**
- Sistema de notificaciones con reintento automático
  para `CLIENTE_RURAL`:
  intento 1 → si falla → espera 10 min → intento 2
  → si falla → espera 10 min → intento 3
  → si falla → registra en log y notifica a
  `ADMINISTRADOR` para seguimiento manual
- Log de entrega de notificaciones con estado
  por cada intento: `enviado` · `fallido` · `entregado`

**Escenario 1 — Notificación de confirmación de reserva**
```gherkin
Given el CLIENTE_RURAL completó una reserva
When el sistema confirma la operación
Then el cliente recibe notificación inmediata con:
     nombre del repuesto, tiempo de reserva
     y referencia para identificarse al llegar
  And si el primer intento falla por conexión
       el sistema reintenta automáticamente
       hasta 3 veces en intervalos de 10 minutos
  And el log registra el estado de cada intento
```

**Escenario 2 — Notificación de repuesto llegado**
```gherkin
Given el CLIENTE_RURAL solicitó notificación
     de llegada de "REP-050"
  And stock confirma recepción del reabastecimiento
When pedidos consume stock.disponible para "REP-050"
Then el cliente recibe notificación:
     "Tu repuesto [nombre] ya está disponible —
      puedes reservarlo antes de viajar"
  And la notificación incluye acción directa
       para reservar sin abrir el catálogo
  And el sistema aplica reintento automático
       si el primer envío falla
```

**Escenario 3 — 3 intentos fallidos de notificación**
```gherkin
Given el sistema necesita notificar al CLIENTE_RURAL
  And los 3 intentos de envío fallaron
       por falta de conexión del cliente
When se agota el tercer intento
Then el sistema registra en log:
     cliente_id, notificacion_tipo, intentos: 3,
     estado: "fallido", timestamp_ultimo_intento
  And el ADMINISTRADOR recibe notificación:
       "No se pudo contactar al cliente [id] —
        seguimiento manual requerido"
  And el agente no intenta un cuarto envío automático
```

---

#### HU-S4-05 — Compra múltiple coordinada por visita

**Módulo:** `pedidos`

**Qué construir:**
- Endpoint `POST /pedidos/visita-coordinada`
  — recibe lista de repuestos y reserva todos
  los disponibles en una sola operación
  Accesible para `CLIENTE_RURAL` y roles internos
- El response separa ítems reservados de ítems
  sin stock con sus estados reales
- Si el cliente llega sin pedido previo coordinado:
  aplica flujo de HU-S1-06 adaptado al contexto

**Escenario 1 — Pedido con múltiples repuestos antes del viaje**
```gherkin
Given el CLIENTE_RURAL armó lista:
     [{"repuesto_id":"REP-001","cantidad":1},
      {"repuesto_id":"REP-002","cantidad":2},
      {"repuesto_id":"REP-050","cantidad":1}]
  And "REP-001" y "REP-002" tienen stock disponible
  And "REP-050" tiene stock_disponible 0
When envía POST /pedidos/visita-coordinada
     con esa lista
Then el sistema retorna HTTP 201 con:
     reservados: [REP-001 con reserva_id,
                  REP-002 con reserva_id]
     no_disponibles: [REP-050 con estado "sin_stock"]
  And stock descuenta REP-001 y REP-002 de disponible
  And el cliente viaja sabiendo exactamente
       qué lo espera y qué no estará disponible
  And el pedido queda registrado con todos
       los ítems y sus estados
```

**Escenario 2 — Repuesto adicional detectado al llegar**
```gherkin
Given el CLIENTE_RURAL llegó con pedido coordinado
  And el mecánico detecta necesidad adicional
       de "REP-070" durante la revisión
When el mecánico agrega "REP-070" a la orden_trabajo
Then aplica el flujo de HU-INT-03 con los
     tramos de precio declarados en §5.1
  And el cliente decide con información completa
       antes de que el mecánico ejecute el trabajo
  And el registro queda vinculado al pedido
       original del cliente
```

**Escenario 3 — Visita sin pedido previo coordinado**
```gherkin
Given el CLIENTE_RURAL llegó sin coordinar pedido previo
When el VENDEDOR o ADMINISTRADOR atiende al cliente
Then el sistema permite registrar la compra presencial
     vinculada a su cuenta usando
     POST /pedidos/presencial de HU-S1-06
  And el historial acumula la visita con:
       canal_origen: "presencial_rural"
  And los datos quedan disponibles para
       análisis de segmento en Fase 2
```

---

## §6 — Criterios de verificación del módulo

> Fuente: DOC-2/04-requerimientos §6
>         DOC-3/07-criterios-avance-automatico
>
> Instrucción al agente:
> Antes de declarar cualquier módulo como completo
> el agente ejecuta todos los criterios de esta
> sección en el orden declarado.
> Si cualquier criterio falla → el módulo no está
> completo → corrección automática antes de avanzar.
> Los umbrales son vinculantes — no son sugerencias.

---

### 6.1 Umbrales de cobertura por módulo

El agente ejecuta el reporte de cobertura después
de cada suite de tests y verifica contra estos
umbrales antes de avanzar al siguiente módulo:

```bash
# Ejecutar suite y generar reporte
pytest tests/ --cov=src/{modulo} \
              --cov-report=term-missing \
              --cov-branch

# Umbrales vinculantes por módulo
# stock:    branch ≥ 95% · line ≥ 70%
# catalogo: branch ≥ 90% · line ≥ 70%
# pedidos:  branch ≥ 90% · line ≥ 70%
# taller:   branch ≥ 85% · line ≥ 70%
# infra:    line ≥ 70% (sin umbral de branch)
```

Si el reporte muestra cobertura por debajo del
umbral del módulo actual → el agente no avanza →
identifica las ramas sin cubrir → escribe los
tests faltantes → vuelve a ejecutar.

---

### 6.2 Criterios de vocabulario

El agente ejecuta este comando antes de cerrar
cada módulo:

```bash
grep -rn "producto\|item\|articulo\|orden\b\|ticket\
         \|servicio\b\|trabajo\b\|apartado\b\|moto\b\
         \|inventario\b\|existencia\|despacho\b\
         \|voucher\|recibo\b\|presupuesto\|tecnico\b\
         \|operario\|chofer\|visita\b" \
     src/{modulo}/domain/
```

Resultado esperado: cero coincidencias.
Si encuentra coincidencias → lista los archivos
y líneas con el término prohibido → corrige →
vuelve a ejecutar el grep → verifica cero antes
de avanzar.

---

### 6.3 Criterios de arquitectura

El agente ejecuta este script antes de cerrar
cada módulo:

```bash
python scripts/check_dip.py src/{modulo}
```

El script verifica que ningún archivo en
`src/{modulo}/domain/` importa desde
`src/{modulo}/infrastructure/` ni desde
`src/{otro_modulo}/domain/`.

Resultado esperado: cero violaciones.
Si encuentra violaciones → lista los imports
inválidos → refactoriza para invertir la
dependencia usando el puerto declarado en §2.2
→ vuelve a ejecutar → verifica cero antes de
avanzar.

---

### 6.4 Criterios de pipeline

El agente verifica que el pipeline CI/CD pasa
completamente antes de declarar el módulo cerrado:

```bash
# Orden de ejecución en pipeline
# 1. Linting
ruff check src/{modulo}/
# Resultado esperado: cero errores

# 2. Tests con cobertura
pytest tests/ --cov=src/{modulo} --cov-branch
# Resultado esperado: todos los tests pasan
#                     cobertura sobre umbral

# 3. Build
docker build -t tecnimotos-{modulo}:test .
# Resultado esperado: imagen construida sin error

# 4. Security scan
bandit -r src/{modulo}/ -ll
# Resultado esperado: cero hallazgos CRITICAL o HIGH

# 5. Secrets scan
detect-secrets scan src/{modulo}/
# Resultado esperado: cero secretos detectados
```

Si cualquier paso falla → el módulo no está
cerrado → el agente corrige y vuelve a ejecutar
el pipeline completo desde el paso 1.

---

### 6.5 Smoke tests por módulo

El agente ejecuta el smoke test del módulo
como última verificación antes de avanzar.
Todos los smoke tests requieren el entorno
de desarrollo levantado con seed nivel 1
(5 registros sintéticos mínimos por entidad).

**`catalogo`**
```bash
# Smoke test: catálogo retorna repuestos disponibles
curl -X GET "$API_URL/catalogo/repuestos\
             ?universo=mototaxi&modelo=Bajaj+RE&año=2019" \
     -H "Authorization: Bearer $TEST_TOKEN"
# Resultado esperado: HTTP 200 con lista no vacía
#                     todos los items tienen stock > 0
#                     ningún item tiene universo motolineal
```

**`pedidos`**
```bash
# Smoke test: creación de pedido
curl -X POST "$API_URL/pedidos" \
     -H "Authorization: Bearer $TEST_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"repuesto_id":"REP-TEST-001","cantidad":1}'
# Resultado esperado: HTTP 201 con pedido en BORRADOR
```

**`stock`**
```bash
# Smoke test: consulta de stock de repuesto existente
curl -X GET "$API_URL/stock/repuestos/REP-TEST-001" \
     -H "Authorization: Bearer $TEST_TOKEN"
# Resultado esperado: HTTP 200 con
#                     cantidad_disponible >= 0
#                     estado en enum válido
```

**`taller`**
```bash
# Smoke test: creación de orden_trabajo
curl -X POST "$API_URL/taller/ordenes" \
     -H "Authorization: Bearer $TEST_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "vehiculo_id":"VEH-TEST-001",
           "tipo_servicio":"correctivo",
           "tipo_urgencia":"alta",
           "mecanico_id":"MEC-TEST-001"
         }'
# Resultado esperado: HTTP 201 con
#                     orden_trabajo en ABIERTA
```

---

### 6.6 Criterio de no regresión entre módulos

Al avanzar al siguiente módulo el agente ejecuta
los smoke tests de todos los módulos anteriores.
Si algún módulo anterior falla su smoke test →
el agente no avanza al módulo nuevo → reporta
la regresión con el formato de detención declarado
en `07-criterios-avance-automatico`.

```bash
# Verificación de no regresión — ejecutar en orden
bash scripts/smoke-catalogo.sh   # debe pasar
bash scripts/smoke-pedidos.sh    # debe pasar si ya construido
bash scripts/smoke-stock.sh      # debe pasar si ya construido
bash scripts/smoke-taller.sh     # debe pasar si ya construido
```

Resultado esperado: todos los scripts retornan
código de salida 0. Cualquier código distinto
de 0 → regresión detectada → detención con reporte.

---

### 6.7 Seed nivel 1 — datos sintéticos mínimos

El agente no puede ejecutar ningún smoke test
sin el seed nivel 1 cargado. El seed es sintético
y no contiene ningún dato real del negocio.

El agente ejecuta el seed antes de los smoke tests:

```bash
python scripts/seed_nivel1.py
# Resultado esperado: script termina con código 0
#                     mensaje: "Seed nivel 1 cargado:
#                     5 repuestos, 2 clientes_test,
#                     1 mecanico_test, 1 vehiculo_test"
```

Si el seed falla → el agente corrige el script
de seed → vuelve a ejecutar → verifica código 0
antes de continuar con los smoke tests.

Datos sintéticos del seed nivel 1:

| Fixture | ID | Descripción |
|---------|----|-------------|
| Repuesto mototaxi disponible | `REP-TEST-001` | Stock disponible: 10 · precio: 45.00 |
| Repuesto mototaxi sin stock | `REP-TEST-002` | Stock disponible: 0 |
| Repuesto bajo_pedido | `REP-TEST-003` | Categoria: bajo_pedido |
| Repuesto tecnico_especializado | `REP-TEST-004` | Advertencia instalación activa |
| Repuesto motolineal | `REP-TEST-005` | Universo: motolineal · stock: 5 |
| Cliente conductor test | `CLI-TEST-S1` | Sub-rol: CLIENTE_CONDUCTOR |
| Cliente distrito test | `CLI-TEST-S2` | Sub-rol: CLIENTE_DISTRITO |
| Mecánico master test | `MEC-TEST-001` | Rol: MECANICO_MASTER |
| Vehículo test | `VEH-TEST-001` | Universo: mototaxi · modelo: Bajaj RE · año: 2019 |

---
## §7 — Índice de construcción

> Instrucción al agente:
> Lee esta sección antes de ejecutar cualquier tarea.
> Define el orden obligatorio de construcción y las
> dependencias entre módulos. No se salta ningún paso.
> No se construye en paralelo sin instrucción explícita.

---

### 7.1 Orden de construcción de módulos

| Orden | Módulo | Razón de la secuencia |
|-------|--------|-----------------------|
| 1° | `catalogo` | Sin dependencias de otros módulos — es la fuente de verdad del catálogo |
| 2° | `stock` | Depende de `catalogo` para inicializar registro al crear repuesto |
| 3° | `pedidos` | Depende de `catalogo` para precio y de `stock` para disponibilidad |
| 4° | `taller` | Depende de `catalogo` para precio · de `stock` para consumo · de `pedidos` para cierre |

El agente no inicia `stock` hasta que `catalogo`
pasa todos sus criterios de §6.
El agente no inicia `pedidos` hasta que `stock`
pasa todos sus criterios de §6.
El agente no inicia `taller` hasta que `pedidos`
pasa todos sus criterios de §6.

---

### 7.2 HU por módulo — mapa de construcción

El agente construye las HU de cada módulo en
el orden declarado. Dentro de un módulo las HU
son independientes salvo dependencia explícita.

**Módulo `catalogo`**

| Orden | HU | Endpoint principal |
|-------|----|--------------------|
| 1° | HU-INT-01 | `PATCH /catalogo/repuestos/{id}/precio` |
| 2° | HU-S1-01 | `GET /catalogo/repuestos` |
| 3° | HU-S1-05 | Lógica de visibilidad de precio por nivel |
| 4° | HU-S2-01 | `POST /catalogo/repuestos/consulta-lista` |
| 5° | HU-S4-01 | Optimización de respuesta para conexión degradada |

**Módulo `stock`**

| Orden | HU | Endpoint principal |
|-------|----|--------------------|
| 1° | HU-S1-02 (parcial) | Lógica de apartado y liberación de stock |
| 2° | HU-S2-05 | `POST /pedidos/notificaciones/suscribir` |
| 3° | HU-S4-04 | Sistema de reintento de notificaciones |

**Módulo `pedidos`**

| Orden | HU | Endpoint principal |
|-------|----|--------------------|
| 1° | HU-S1-02 | `POST /pedidos/reservas` |
| 2° | HU-S1-04 | Sistema de notificaciones de estado |
| 3° | HU-S1-06 | `POST /pedidos/presencial` |
| 4° | HU-S2-02 | `POST /pedidos/lista` |
| 5° | HU-S2-03 | `GET /pedidos/mis-pedidos` |
| 6° | HU-S2-04 | `POST /pedidos/{id}/envio` |
| 7° | HU-S2-06 | `POST /pedidos/lista-progresiva/items` |
| 8° | HU-S4-02 (parcial) | `POST /pedidos/reservas` con segmento rural |
| 9° | HU-S4-03 | `POST /pedidos/remoto` |
| 10° | HU-S4-05 | `POST /pedidos/visita-coordinada` |
| 11° | HU-INT-05 | `POST /pedidos/{id}/comprobante` |

**Módulo `taller`**

| Orden | HU | Endpoint principal |
|-------|----|--------------------|
| 1° | HU-INT-06 | `GET /taller/disponibilidad` |
| 2° | HU-S1-03 | Vista reducida de disponibilidad para CLIENTE |
| 3° | HU-INT-02 | `POST /taller/ordenes` |
| 4° | HU-INT-03 | `POST /taller/ordenes/{id}/repuestos` |
| 5° | HU-INT-04 | `POST /taller/ordenes/{id}/revision-final` |
| 6° | HU-S4-02 (parcial) | `POST /taller/ordenes/{id}/coordinar-visita` |

**Transversal — construir antes que cualquier módulo**

| Orden | HU | Qué construye |
|-------|----|--------------------|
| 0° | HU-INT-07 | Middleware JWT RS256 · RBAC · log de auditoría · MFA |

---

### 7.3 Dependencias entre HU

Estas dependencias son vinculantes. El agente
no construye una HU dependiente sin que la HU
de la que depende esté cerrada y con smoke test
pasando.

| HU dependiente | Depende de | Razón |
|----------------|-----------|-------|
| HU-S1-02 | HU-S1-01 | La reserva requiere que el catálogo exponga disponibilidad |
| HU-S2-02 | HU-S2-01 | El pedido por lista requiere la consulta por lista |
| HU-S2-03 | HU-S2-02 | El seguimiento requiere que el pedido exista |
| HU-S2-04 | HU-S2-02 | El envío requiere que el pedido esté confirmado |
| HU-S2-06 | HU-S2-01 | La lista progresiva requiere la consulta por lista |
| HU-INT-02 | HU-INT-07 | El taller requiere RBAC para controlar quién abre órdenes |
| HU-INT-03 | HU-INT-02 | Los costos adicionales requieren la orden abierta |
| HU-INT-04 | HU-INT-03 | El cierre requiere la lógica de costos adicionales |
| HU-INT-05 | HU-INT-04 | El comprobante requiere el cierre de la orden |
| HU-S4-02 | HU-S1-02 | La reserva rural reutiliza la lógica base de reserva |
| HU-S4-03 | HU-S2-04 | El pedido rural reutiliza la lógica de envío |
| HU-S4-04 | HU-S1-04 | Las notificaciones rurales extienden el sistema base |
| HU-S4-05 | HU-S4-02 | La compra coordinada requiere la reserva rural |

---

## §8 — Registro de observaciones al DOC-2

> Fuente: P7 — reflejo fiel del DOC-2
>
> Instrucción al agente:
> Si durante la construcción detectas una
> inconsistencia entre lo declarado en este
> archivo y el comportamiento real del sistema
> construido → no corrijas en este archivo →
> registra la observación aquí con formato exacto
> y detente con reporte hacia el humano.
> El DOC-2 es la fuente de verdad — este archivo
> lo refleja, no lo reemplaza.

---

### 8.1 Observaciones activas

| ID | Observación | Sección afectada | Estado |
|----|-------------|-----------------|--------|
| OBS-001 | CT-04-02 declara contador de consultas de precio por sesión — requiere campo en modelo de sesión de usuario en `07 modelo-datos` del DOC-2 | §4.2 visibilidad de precio Nivel 1 | Pendiente en DOC-2 |
| OBS-002 | CT-04-03 declara lista de reserva progresiva de S2 como entidad propia — requiere tabla en `07 modelo-datos` del DOC-2 | §5.3 HU-S2-06 | Pendiente en DOC-2 |
| OBS-003 | CT-04-04 declara autorización manual de visibilidad de precio como campo en orden_trabajo — requiere campo en modelo de datos del DOC-2 | §5.1 HU-INT-02 Escenario 5 | Pendiente en DOC-2 |
| OBS-004 | CT-04-05 declara precio_ajustado por ítem en pedido de S2 — requiere campo en modelo de pedido del DOC-2 | §5.3 HU-S2-02 | Pendiente en DOC-2 |
| OBS-005 | CT-04-09 declara cola de reintentos para notificaciones de S4 — requiere mecanismo declarado en `08 contratos-interfaces` del DOC-2 | §5.4 HU-S4-04 | Pendiente en DOC-2 |

Estas observaciones no bloquean la construcción
con este archivo — bloquean la construcción de
`03-diseno-sistema` hasta que el DOC-2 las resuelva
en sus secciones correspondientes.

---

## §9 — Historial de versiones

| Versión | Fecha   | Cambio                                                                                                                                                                                                                              | Impacto                                                                                                                                                                                                                          |
| ------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0.1.0   | 2026-06 | Primera versión completa — §1 vocabulario · §2 bounded contexts · §3 eventos · §4 roles · §5 HU ejecutables (25 HU · 107 escenarios Gherkin) · §6 criterios de verificación · §7 índice de construcción · §8 observaciones al DOC-2 | Base ejecutable para CLI o agente — pendiente validación en primera ejecución real                                                                                                                                               |
| 1.0.1   | 2026-06 | PCT-CIERRE-007 — añadida §1.6 Logging estructurado ejecutable (RNT-06), sintetizada desde Gobierno Técnico `10-monitoring-logging.md` Tramos 2 y 9                                                                                  | Cierra OBS-CIERRE-002 — RNT-06 ahora tiene especificación ejecutable completa (formato, campos obligatorios, mecanismo de correlación, librería). Da contrato real al test referenciado en `09-criterios-avance-automatico` §4.1 |

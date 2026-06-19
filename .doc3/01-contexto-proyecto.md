---
version: 1.0.1
estado: cerrado
archivo: "01"
titulo: Contexto del proyecto
fecha: 2026-06
scope: límites, propósito y restricciones del sistema para el agente
fuente-doc2: 01-descubrimiento · 02-alcance
sensible: false
---

# 01 — Contexto del proyecto
## Protocolo de construcción — Tecnimotos Santi

> El agente lee este archivo antes de iniciar
> cualquier módulo. Define el problema que resuelve
> el sistema, los límites que no puede cruzar y
> las preguntas de negocio que cada módulo responde.
> El agente no necesita leer el DOC-2 para entender
> el contexto — este archivo es suficiente.

---

## Problema raíz

El negocio pierde ventas diarias por operar sin sistema
de información propio. El stock vive en la memoria de
una sola persona. Los precios no tienen fuente única.
Los pedidos no dejan registro. El consumo de repuestos
en taller no se registra antes de que el vehículo salga.

**El sistema no es el objetivo — es el instrumento
de medición.** Su propósito es producir datos reales
que hoy no existen: ventas perdidas medibles, LTV real
por segmento, canal de conversión trazable, rotación
de stock visible, margen real por orden de trabajo.

---

## Segmentos activos en el MVP

| Segmento | Descripción | Dolor principal |
|----------|-------------|-----------------|
| S1 | Conductor individual de mototaxi | No puede confirmar stock antes de viajar a la tienda |
| S2 | Mecánico de distrito | No puede coordinar pedidos por lote con trazabilidad |
| S4 | Cliente rural | Opera con conectividad degradada — necesita confirmación antes del viaje |

**S3 (dueño de flota) y S5 (motolineal) no están activos en el MVP.**

---

## Módulos del MVP — MUST únicamente

| ID | Módulo | Qué resuelve |
|----|--------|-------------|
| M-01 | `catalogo` | Stock visible en tiempo real · precio unificado · búsqueda por modelo, año y código |
| M-04 | `pedidos` | Flujo formal de pedido con estados rastreables · notificación automática · envío a distrito |
| M-08 | `stock` | Registro de consumo en taller · reabastecimiento · umbral de alerta |
| M-09 | `taller` | Orden de trabajo con estados · lista de repuestos · aprobación de costos adicionales |

El agente construye estos cuatro módulos en este orden:
**`catalogo` → `stock` → `pedidos` → `taller`**

---

## Preguntas de negocio que el sistema debe responder

| Módulo | Pregunta |
|--------|----------|
| `catalogo` | ¿Cuántos clientes confirman stock antes de venir a la tienda? |
| `pedidos` | ¿Qué porcentaje de pedidos remotos se registra en sistema vs WhatsApp? |
| `stock` | ¿Cuál es la discrepancia entre stock visible y stock físico? |
| `taller` | ¿Qué repuestos se consumen sin registrar por orden de trabajo? |

Estas preguntas se responden con datos reales al día 60
de operación. Son el criterio de éxito del MVP.

---

## Lo que el sistema NO construye en el MVP

| Excluido | Razón |
|----------|-------|
| Historial navegable de reparaciones por vehículo | Requiere datos acumulados — se activa en Fase 2 |
| Canal B2B motolineal completo | S5 sin tracción validada — se activa en Fase 3 |
| Diagnóstico por videollamada | Requiere disponibilidad del mecánico en tiempo real |
| Agenda formal de visitas a distrito | Requiere módulo de disponibilidad no incluido en MVP |
| Módulos independientes: clientes, notificaciones, mecánicos | Sin complejidad suficiente que justifique extracción |
| Pronóstico automático de demanda | Requiere mínimo 6 meses de datos reales |
| Venta de motos nuevas | Línea de negocio independiente — Fase 4 |

**Regla de integridad:** si durante la construcción
aparece una necesidad no documentada aquí, el agente
se detiene y reporta — no implementa por iniciativa propia.

---

## Restricciones no negociables

El agente nunca puede producir código que viole estas
restricciones. Son condiciones de diseño, no preferencias.

### Restricciones de negocio

| ID | Restricción |
|----|------------|
| RNN-01 | Los precios de venta son siempre manuales — ningún precio se actualiza automáticamente |
| RNN-02 | Los descuentos son invisibles para el cliente — solo `ADMINISTRADOR` puede aplicarlos |
| RNN-03 | El vehículo no sale del taller sin pago mínimo del 80% salvo aprobación conjunta |
| RNN-04 | El `comprobante` solo lo emite `ADMINISTRADOR` — `VENDEDOR` genera `PENDIENTE_VALIDACION` |
| RNN-05 | Los catálogos de `mototaxi` y `motolineal` son estructuralmente separados — nunca se mezclan |
| RNN-07 | El sistema informa — no decide. Toda acción sobre precios, descuentos y reabastecimiento es decisión humana |

### Restricciones técnicas

| ID | Restricción |
|----|------------|
| RNT-02 | MFA obligatorio para `SUPERADMIN` y `ADMINISTRADOR` |
| RNT-03 | Ningún secreto, credencial ni clave en el código fuente |
| RNT-04 | El descuento atómico de stock ocurre al cierre de `orden_trabajo` — no durante la ejecución |
| RNT-05 | Flujos críticos de S4 deben funcionar con conexión 4G degradada — tolerancia de 30 segundos |
| RNT-06 | Logs estructurados en JSON desde el primer módulo — no como capa posterior |

### Restricciones legales

| ID | Restricción |
|----|------------|
| RNL-01 | Boleta electrónica para montos superiores a S/ 20 |
| RNL-02 | Factura electrónica para montos superiores a S/ 60 con RUC |
| RNL-03 | Comprobante anulado solo con nota de crédito — nunca eliminado del sistema |
| RNL-04 | Datos de cliente con política de privacidad y consentimiento explícito |
| RNL-05 | Derecho al olvido implementable desde el diseño |
| RNL-06 | Credencial tributaria nunca almacenada en el sistema |

---

## Roles del sistema

| Rol | Responsabilidad operativa en el MVP |
|-----|-----------------------------------|
| `SUPERADMIN` | Control total · configuración técnica · logs |
| `ADMINISTRADOR` | Stock · precios · comprobantes · configuración de negocio |
| `VENDEDOR` | Catálogo (lectura) · pedidos (crear/ver) · comprobantes (PENDIENTE_VALIDACION) |
| `MECANICO_MASTER` | Órdenes de trabajo · autorización de precio al cliente |
| `MECANICO_JUNIOR` | Órdenes de trabajo asignadas · sin autorización de precio |
| `CLIENTE_CONDUCTOR` | S1 — pedidos propios · reservas · catálogo con límite de precio |
| `CLIENTE_DISTRITO` | S2 — lista progresiva · pedidos por lote · envío |
| `CLIENTE_RURAL` | S4 — flujos optimizados para conectividad degradada |

---

## Vocabulario canónico — términos que el agente usa

El agente usa exclusivamente estos términos en nombres
de clases, funciones, variables, endpoints y eventos.
Para definiciones completas ver `02-definicion-funcional.md`.

| Término canónico | Nunca usar |
|-----------------|------------|
| `repuesto` | producto, ítem, artículo, pieza |
| `pedido` | orden, orden de compra, solicitud |
| `orden_trabajo` | orden de servicio, ticket, trabajo |
| `reserva` | apartado, separado, hold |
| `reabastecimiento` | reposición, compra, ingreso |
| `stock` | inventario, existencias, cantidad |
| `comprobante` | factura genérica, documento, recibo |
| `conductor` | cliente, usuario, dueño |
| `mecanico` | técnico, operario, trabajador |
| `envio` | despacho, entrega, envío |
| `proforma` | cotización previa, presupuesto |
| `vehiculo` | moto, unidad, equipo |

---

## Fases del sistema

| Fase | Infraestructura | Condición de entrada |
|------|----------------|---------------------|
| Fase 1 — MVP | Railway | DOC-3 construido · checklist pre-deploy verde · Elena validó en staging |
| Fase 2 — Consolidación | VPS Hetzner | SE-07 cumplido · 60 días operativo · HP-01 a HP-03 cerradas |
| Fase 3 — Motolineal | VPS Hetzner o Azure | Fase 2 consolidada · S5 con tracción validada |
| Fase 4 — Expansión | Azure/AWS | Fases 1–3 consolidadas · excedente operativo sostenido |

**El agente construye para Fase 1 — Railway.**
No anticipa Fase 2 ni posteriores salvo que el diseño
lo requiera sin costo adicional (separación de `universo`
en tabla `repuesto` es un ejemplo — ya está en el esquema).

---

## Criterios de cancelación activos

Si alguno de estos criterios se activa a los 60 días
de operación real, el MVP se detiene para revisión.
El agente no construye funcionalidades de Fase 2
si algún criterio está activo.

| ID | Condición |
|----|-----------|
| CC-01 | Menos del 30% de clientes habituales consulta stock digitalmente en 60 días |
| CC-02 | Más del 20% de diferencia entre stock visible y stock físico real |
| CC-03 | El sistema resuelve menos consultas que WhatsApp en el mismo período |
| CC-04 | Cero mejora medible en ventas capturadas vs línea base |
| CC-05 | Menos del 30% de pedidos de distrito registrados en sistema vs WhatsApp |

---

## Criterios de adopción mínima — SE-07

El sistema se considera adoptado cuando se cumplen
los tres indicadores dentro de los primeros 60 días.

| ID | Indicador | Umbral |
|----|-----------|--------|
| SE-07-A | Pedidos remotos en sistema vs WhatsApp | ≥ 70% |
| SE-07-B | Discrepancia stock visible vs físico | < 20% |
| SE-07-C | Autonomía operativa sin intervención del administrador | 2h sin pérdida de venta |

---

## Ubicación en el repositorio
```
repositorio-tecnimotos/  
└── .doc3/  
└── 01-contexto-proyecto.md ← este archivo
```
---

## Historial de versiones

| Versión | Fecha   | Cambio                                                                                                     | Motivo                                                      |
| ------- | ------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 1.0.0   | 2026-06 | Primera versión                                                                                            | DOC-2 completamente cerrado — todas las fuentes disponibles |
| 1.0.1   | 2026-06 | PCT-CIERRE-001: orden de construcción corregido a catalogo→stock→pedidos→taller para coincidir con 02 §7.1 | Detectado en verificación cruzada R-CIERRE-GLOBAL           |
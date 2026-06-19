---
version: 1.0.1
estado: cerrado
archivo: "00"
titulo: Taxonomía documental
fecha: 2026-06
scope: protocolo de navegación para CLI y agentes
fuente-doc2: mapa-de-ejecucion DOC-3 v1.0
sensible: false
---

# 00 — Taxonomía documental
## Protocolo de construcción — Tecnimotos Santi

> Este es el primer archivo que el agente lee.
> Define qué archivos existen en el DOC-3,
> qué rol cumple cada uno y cuándo consultarlo.
> El agente nunca lee el DOC-2 directamente —
> lee los archivos del DOC-3 que sintetizan
> lo que necesita para cada tarea.

---

## Regla fundamental
```
DOC-2 → fuente de verdad del sistema  
DOC-3 → síntesis ejecutable para el agente

El agente construye desde el DOC-3.  
El DOC-3 refleja el DOC-2.  
El DOC-2 nunca se modifica desde el DOC-3.  
Si hay contradicción entre DOC-3 y DOC-2 → el DOC-2 gana.
```
---

## Qué es este repositorio

Sistema de gestión operativa para **Tecnimotos Santi** —
tienda y taller autorizado Bajaj y TVS en Ayacucho, Perú.

El sistema tiene cuatro módulos:

| Módulo     | Responsabilidad principal                      |
| ---------- | ---------------------------------------------- |
| `catalogo` | Repuestos con stock visible y precio unificado |
| `stock`    | Movimientos de inventario y reabastecimiento   |
| `pedidos`  | Flujo formal de pedido con estados rastreables |
| `taller`   | Órdenes de trabajo con consumo de repuestos    |

Stack declarado en DOC-2 ADR-001 a ADR-008:
**FastAPI · PostgreSQL 16 · Redis 7 · Next.js 14 · Docker · Railway**

---

## Mapa de archivos del DOC-3

| # | Archivo | Cuándo consultarlo | Fuente DOC-2 |
|---|---------|-------------------|--------------|
| 00 | `00-taxonomia-documental.md` | Siempre primero — orientación inicial | Mapa DOC-3 |
| 01 | `01-contexto-proyecto.md` | Antes de iniciar cualquier módulo — límites y propósito | `01-descubrimiento` · `02-alcance` |
| 02 | `02-definicion-funcional.md` | Al implementar comportamiento — qué debe hacer y cómo verificarlo | `03-A` · `03-B` · `03-C` · `04` |
| 03 | `03-diseno-sistema.md` | Al estructurar código — arquitectura, contratos y setup | `06` · `07` · `08` |
| 04 | `04-estrategia-pruebas.md` | Al escribir o ejecutar pruebas — umbrales y comandos | `09` |
| 05 | `05-trazabilidad-ligera.md` | Al reportar estado — qué está hecho y qué falta | Generado durante construcción |
| 06 | `06-retrospectiva-viabilidad.md` | Al cerrar un hito — qué funcionó y qué cambiar | Generado al cierre de hito |
| 07 | `07-criterios-avance-automatico.md` | Antes de avanzar al siguiente módulo — criterios de avance y detención | `04` · `09` · `13` |

---

## Flujo de trabajo del agente por tarea

### Iniciar un módulo nuevo
```
1. Leer 00-taxonomia-documental.md ← orientación
2. Leer 01-contexto-proyecto.md ← límites del sistema
3. Leer 02-definicion-funcional.md ← comportamiento esperado
4. Leer 03-diseno-sistema.md ← estructura y contratos
5. Construir el módulo
6. Leer 04-estrategia-pruebas.md ← verificación
7. Ejecutar pruebas hasta criterios verdes
8. Leer 07-criterios-avance-automatico.md ← ¿puedo avanzar?
9. Actualizar 05-trazabilidad-ligera.md ← registrar estado
```
### Verificar si un módulo está completo
```
1. Leer 07-criterios-avance-automatico.md
2. Ejecutar criterios del módulo actual
3. Si todos verdes → avanzar
4. Si alguno falla → corregir (máximo 3 intentos)
5. Si persiste → detención con reporte estructurado
```
### Reportar estado actual
```
1. Leer 05-trazabilidad-ligera.md
2. Actualizar con el estado real
3. Nunca asumir estado sin verificar
```
### Cerrar un hito
```
1. Verificar criterios de todos los módulos del hito  
    con 07-criterios-avance-automatico.md
2. Actualizar 05-trazabilidad-ligera.md
3. Generar 06-retrospectiva-viabilidad.md
```
---

## Reglas de uso que el agente debe respetar

| Regla | Criterio |
|-------|----------|
| **Un archivo por tarea** | El agente consulta el archivo mínimo necesario para la tarea — no lee el DOC-3 completo en cada paso |
| **Sin datos sensibles** | El agente nunca escribe en ningún archivo datos reales de clientes, IPs internas, credenciales ni valores de variables de entorno |
| **Vocabulario canónico** | El agente usa exclusivamente los términos del glosario — nunca sinónimos. Ver `02-definicion-funcional.md` §vocabulario |
| **DOC-2 como árbitro** | Si el agente detecta contradicción entre un archivo del DOC-3 y el DOC-2, detiene y reporta — no resuelve por cuenta propia |
| **Sin modificar DOC-2** | El agente nunca propone cambios al DOC-2 — solo al DOC-3 |
| **Trazabilidad obligatoria** | Toda implementación referencia la HU o el contrato del DOC-3 que la originó |

---

## Separación de responsabilidades

| Responsabilidad | Quién la ejecuta |
|-----------------|-----------------|
| Decidir qué construir | Sant — basado en DOC-2 |
| Construir el código | Agente — basado en DOC-3 |
| Validar comportamiento real | Elena — por uso en `tecnimoto` |
| Actualizar DOC-2 ante cambio de negocio | Sant |
| Actualizar DOC-3 ante cambio de DOC-2 | Sant + agente |

---

## Criterio de actualización de este archivo

Este archivo se actualiza cuando:
- Se agrega un archivo nuevo al DOC-3
- Cambia el rol de un archivo existente
- Se reemplaza el DOC-3 por una versión nueva

No se actualiza por cambios en el código ni por
avance de módulos — eso va en `05-trazabilidad-ligera.md`.

---

## Ubicación en el repositorio
```
repositorio-tecnimotos/  
└── .doc3/  
└── 00-taxonomia-documental.md ← este archivo
```
---

## Historial de versiones

| Versión | Fecha   | Cambio                                                                                                                                  | Motivo                                                                                |
| ------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| 1.0.0   | 2026-06 | Primera versión — DOC-2 completamente cerrado                                                                                           | Todas las condiciones de activación cumplidas                                         |
| 1.0.1   | 2026-06 | PCT-CIERRE-001: orden de módulos corregido a catalogo→stock→pedidos→taller para coincidir con dependencias reales declaradas en 02 §7.1 | Detectado en verificación cruzada R-CIERRE-GLOBAL — 00 reflejaba orden desactualizado |
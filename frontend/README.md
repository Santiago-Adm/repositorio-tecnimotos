# SANTI — Frontend (Tecnimotos Santi)

Este es el frontend del Sistema de Asistencia y Núcleo Técnico Integral (SANTI) para Tecnimotos Santi, desarrollado utilizando **Next.js 14 (App Router)**, **TypeScript**, y **Tailwind CSS**.

---

## 📋 Arquitectura de Presentación

El sistema está dividido en dos superficies visuales vinculantes declaradas en el diseño del sistema (`03-diseno-sistema.md` §3.3.1):

1. **Interfaz Pública (Light Theme):**
   - **Estilo:** Fondo claro (`--color-surface-light` / `#F8FAFC`), texto oscuro (`slate-800`), acentos en `--color-teal` (`#0D9488`).
   - **Destinatarios:** Clientes conductores (`CLIENTE_CONDUCTOR` / S1), mecánicos de distrito (`CLIENTE_DISTRITO` / S2) y clientes rurales (`CLIENTE_RURAL` / S4).
   - **Grupo de Rutas:** `app/(public)/*`

2. **Interfaz Interna (Dark Theme / "Modo Taller"):**
   - **Estilo:** Fondo oscuro (`--color-surface-dark` / `#0F172A`), texto claro (`slate-50`), acentos en `--color-teal` y `--color-electric` (`#8B5CF6`).
   - **Destinatarios:** Operarios internos (`SUPERADMIN`, `ADMINISTRADOR`, `MECANICO_MASTER`, `MECANICO_JUNIOR`).
   - **Grupo de Rutas:** `app/(internal)/*`

---

## ⚖️ Decisión de Diseño: Contexto Visual del VENDEDOR

El rol de `VENDEDOR` es transversal y opera en ambas superficies:
- Consulta el catálogo de repuestos públicamente para asesorar a clientes de manera presencial.
- Gestiona y emite comprobantes en estado `PENDIENTE_VALIDACION` en la consola interna.

### Definición de Cambio de Contexto
Para evitar la complejidad de estados manuales, alternancia de clases en runtime y posibles desfases visuales, **el contexto visual del VENDEDOR depende estrictamente de la ruta navegada**:
- Al acceder al catálogo público (`/catalogo`), el sistema renderiza el layout del grupo `(public)`, aplicando el tema claro (interfaz pública).
- Al acceder al panel de facturación y comprobantes (`/facturacion`), el sistema renderiza el layout de `(internal)`, aplicando el tema oscuro (Modo Taller).

Esto mantiene el desacoplamiento de layouts a nivel de Next.js Route Groups y asegura que el lóbulo visual concuerde con el rol de uso del software en ese preciso instante.

---

## 🛠️ Tecnologías y Estructura

- **Next.js 14.2.x** (App Router)
- **Tailwind CSS 3.4.x**
- **TypeScript 5.4.x**
- **Fuentes (Google Fonts):**
  - Display: `Quicksand` (Títulos, logotipo, proformas)
  - Body: `Nunito Sans` (Párrafos, botones, alertas)
  - Mono: `Fira Code` (Códigos de repuestos, precios, placas)

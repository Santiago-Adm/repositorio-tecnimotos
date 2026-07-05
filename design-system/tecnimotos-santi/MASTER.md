# Design System Master File — Tecnimotos Santi

> **LOGIC:** When building a specific page, first check `design-system/tecnimotos-santi/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.
>
> **Origen:** generado con `ui-ux-pro-max` (`--design-system --variance 6 --motion 6 --density 7`,
> ver Pieza 0 de la sesión anterior para el mismo criterio de traducción) y adaptado a los
> tokens SANTI ya fijados y en uso real en `frontend/app/globals.css` y `frontend/tailwind.config.ts`.
> El Skill aportó profundidad/sombra/espaciado/motion — **no** su paleta ni tipografía crudas.

---

**Project:** Tecnimotos Santi
**Adaptado:** 2026-07-05
**Categoría real:** Marketplace B2B de repuestos + taller (11 roles), no "Automotive/Car Dealership" genérico
**Design Dials:** Variance 6/10 (Balanced/Modern) | Motion 6/10 (Standard) | Density 7/10 (Standard)

---

## Global Rules

### Color Palette — SANTI (restricción dura, no sustituible)

| Rol | Hex | Variable CSS real | Uso |
|---|---|---|---|
| Primary / CTA / Accent | `#0D9488` (Teal) | `--color-teal` | Botones primarios, focus ring, estado activo, glow |
| Secondary / Acento decorativo | `#8B5CF6` (Electric) | `--color-electric` | Logo, gráficos (serie 2), acentos puntuales — nunca CTA principal |
| Foreground oscuro / superficie dark | `#0F172A` (Cobalt Dark) | `--color-surface-dark` | Fondo de los 5 roles internos (Admin, Vendedor, Mecánico ×2, Superadmin) |
| Background claro / superficie light | `#F8FAFC` | `--color-surface-light` | Fondo de los 3 roles cliente (Conductor, Rural, Distrito) y landings públicas |
| Muted (dark) | `#1E293B` (slate-800) | — | Cards, sidebar, inputs sobre superficie oscura |
| Muted (light) | `#F1F5F9` (slate-100) | — | Cards, chips inactivos sobre superficie clara |
| Border (dark) | `#1E293B` (slate-800) | — | Divisores sobre superficie oscura |
| Border (light) | `#E2E8F0` (slate-200) | — | Divisores sobre superficie clara |
| Destructive | `#EF4444` (red-500), texto `#F87171` (red-400) | — | Errores, cancelar, dar de baja — **nunca** como CTA |
| Ring (focus) | `#0D9488` (Teal) | — | `focus:ring-teal`, ya usado en todos los inputs |

**Nota sobre las palabras clave crudas del Skill** ("indigo", "deep black", "action red"): se traducen así — *indigo* → Electric `#8B5CF6` (ya es un morado/índigo real, no hace falta cambiarlo); *deep black* → Cobalt Dark `#0F172A` (nunca `#000000` puro, coincide con la advertencia OLED del propio Skill); *action red* → Teal `#0D9488` (el CTA de este sistema siempre fue teal, confirmado en las 8 piezas de la sesión anterior — el rojo queda reservado a destructivo).

### Typography — SANTI (restricción dura, ya wireada en `globals.css`)

- **Heading/Display Font:** Quicksand (`--font-display`)
- **Body Font:** Nunito / Nunito Sans (`--font-body`)
- **Mono Font:** Fira Code (`--font-mono`) — coincide con la recomendación cruda del Skill, sin cambios
- **Mood aportado por el Skill (se conserva):** dashboard, data, analytics, técnico, preciso — es exactamente el tono que ya tienen los paneles construidos

### Spacing Variables (Skill, sin cambios — Density 7/10)

| Token | Value | Uso |
|---|---|---|
| `--space-xs` | `4px` | Gaps ajustados |
| `--space-sm` | `8px` | Gaps de íconos, espaciado inline |
| `--space-md` | `16px` | Padding estándar |
| `--space-lg` | `24px` | Padding de sección |
| `--space-xl` | `32px` | Gaps grandes |
| `--space-2xl` | `48px` | Márgenes de sección |
| `--space-3xl` | `64px` | Padding de hero |

### Shadow Depths (Skill, sin cambios de valor — ya aplicado en Pieza F de la sesión anterior)

| Level | Value | Uso |
|---|---|---|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Lift sutil (headers) |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, botones |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modales, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Cards destacadas |
| Glow de marca (ya en uso real) | `0 0 12-20px rgba(13,148,136,0.15-0.35)` | Estado activo/hover — mismo valor exacto que `RepuestoCard`, `PedidoCard`, `AppSidebarNav` |

---

## Component Specs (Skill + tokens SANTI)

### Buttons

```css
.btn-primary {
  background: #0D9488; /* Teal */
  color: #FFFFFF;
  padding: 12px 24px;
  border-radius: 8px;
  font-family: var(--font-body);
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}
.btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }

.btn-secondary {
  background: transparent;
  color: #0D9488;
  border: 2px solid #0D9488;
  padding: 12px 24px;
  border-radius: 8px;
  font-family: var(--font-body);
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-destructive {
  background: transparent;
  color: #F87171; /* red-400, ya en uso */
  border: 1px solid #EF4444;
}
```

### Cards (dark / light — ambas superficies del sistema)

```css
.card-dark {
  background: linear-gradient(to bottom right, #1E293B, #0F172A);
  border: 1px solid rgba(30,41,59,0.6);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
}
.card-dark:hover { box-shadow: 0 0 20px rgba(13,148,136,0.15); border-color: rgba(13,148,136,0.5); }

.card-light {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-sm);
  transition: all 200ms ease;
}
.card-light:hover { box-shadow: var(--shadow-lg); }
```

### Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0; /* light. Dark surface: #1E293B */
  border-radius: 8px;
  font-family: var(--font-body);
  font-size: 16px; /* nunca <16px en mobile — evita auto-zoom iOS */
  transition: border-color 200ms ease;
}
.input:focus {
  border-color: #0D9488;
  outline: none;
  box-shadow: 0 0 0 3px rgba(13,148,136,0.15);
}
```

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px); /* consistente con AppSidebarNav drawer, sesión anterior */
}
.modal {
  background: #0F172A; /* dark surface — o #FFFFFF en contexto claro */
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

### Gráficos Recharts (Pieza 1.D — ya parcialmente construido en `chartColors.ts`)

- Serie 1: Teal `#0D9488` · Serie 2: Electric `#8B5CF6` · Series adicionales: derivar con `CATEGORICAL` ya existente en `frontend/src/lib/chartColors.ts` — **no introducir una paleta categórica nueva**, ya cumple contraste.
- Tooltip dark: `background:#1E293B; border:1px solid #334155; color:#E2E8F0` (ya en `Primitives.tsx`, sin cambios).
- Tooltip light: `background:#FFFFFF; border:1px solid #E2E8F0; color:#1E293B` (ya en `PrimitivesLight.tsx`, sin cambios).
- Grid/ejes: `#1E293B` dark, `#E2E8F0` light — ya correcto, no tocar.

---

## Variantes por contexto (respuesta a observación de Sant — el Skill no se aplica parejo)

El sistema es único en **tokens** (color/tipografía/sombra/spacing), pero cada contexto usa
un patrón distinto de los 67 estilos / patrones de landing del Skill, consultado
específicamente por contexto (no un solo `--design-system` genérico estirado a todo):

### A) Landings públicas (Conductor/Rural/Distrito)

Consulté `--domain landing` con la query real del negocio. Descarté el patrón crudo inicial
("Marketplace/Directory", hero de búsqueda + "conviértete en vendedor" — no aplica, Tecnimotos
no es un marketplace multi-vendedor) y elegí **Trust & Authority + Conversion**, que además
coincide con la estructura que las 3 landings YA tienen construida (`app/(public)/*/page.tsx`:
hero con video/imagen de marca → secciones de features/beneficios → CTA) — confirmado por
grep real antes de recomendar, no asumido:
- Hero: credibilidad/misión (ya existe, hero con video de fondo)
- Prueba: beneficios concretos por segmento (ya existen las 3 secciones por landing)
- CTA claro y único por sección — revisar que cada landing tenga un solo CTA primario visible
  a la vez (Pieza 1.D debe auditar esto, no re-construir las landings desde cero)

### B) Dashboards internos (Administrador, Vendedor, Mecánico Máster/Junior, Superadmin)

Tres patrones del Skill combinados, cada uno para una parte distinta del dashboard —
consultados con `--domain style`:
- **Data-Dense Dashboard** — ya es lo que `AdministradorResumenTab`/`Primitives.tsx`
  construyeron (KPI cards, grid de charts, padding compacto). Confirma que el camino ya
  tomado es correcto, no requiere cambio de estructura.
- **Drill-Down Analytics** — aplica directo a `CatalogoNavegable` (universo → modelo →
  categoría ya es jerárquico). Pieza 1.D debe agregar un indicador de nivel/breadcrumb
  visible ("3R > Pulsar 200 NS > Motor") reutilizando el patrón, no solo tabs sueltos.
- **Real-Time Monitoring** (sin WebSocket real, solo el lenguaje visual) — aplica a las
  alertas de stock bajo umbral: el glow teal ya usado se extiende a un `pulse` sutil
  específicamente en el badge de "Bajo umbral"/"Crítico", para que se perciba como alerta
  viva, no un dato estático más.

### C) Dashboards cliente (Conductor, Rural, Distrito — tema claro)

Data-Dense pero con **menos densidad** que los internos (density 5/10, no 7/10) — son flujos
de una sola tarea ("¿qué necesitas?", "mi lista"), no paneles analíticos. No se les aplica
Drill-Down breadcrumb (ya tienen el banner "Mostrando repuestos para tu vehículo" de la
sesión anterior, que cumple el mismo propósito de orientación de forma más simple).

### D) Modales (EditarRepuestoModal y futuros)

Ver Component Specs → Modals arriba. Mismo blur + spring que el drawer de `AppSidebarNav`.

---

## Motion (Skill, adaptado — sin gsap nuevo, Framer Motion ya es la librería del proyecto)

**Regla de consistencia (ya validada en Pieza F de la sesión anterior):** un solo spring en todo el sistema — `{ type: 'spring', stiffness: 380, damping: 30 }` — es el que ya usa `AppSidebarNav`. Cualquier componente nuevo debe reutilizar esta constante, no inventar timings nuevos.

- Micro-interacciones (hover, tap): 150-300ms, `whileHover`/`whileTap` de Framer Motion.
- Transiciones de página completa: el Skill sugiere 400-600ms con overlay — **no aplicar** todavía (requeriría un overlay de layout nuevo, fuera de lo pedido en esta sesión; queda anotado como candidato futuro, no se construye sin pedido explícito).
- `prefers-reduced-motion`: obligatorio en todo componente animado — mismo patrón `useReducedMotion()` ya aplicado en `TiltCard` y `AppSidebarNav`.

---

## Anti-Patterns (Skill, sin cambios)

- ❌ Emojis como íconos — usar SVG (Heroicons/Lucide, ya es el criterio del proyecto)
- ❌ Elementos clicables sin `cursor-pointer`
- ❌ Hover que desplaza layout (usar `transform`, nunca `width`/`height`/`top`/`left`)
- ❌ Contraste de texto por debajo de 4.5:1
- ❌ Cambios de estado instantáneos sin transición (150-300ms mínimo)
- ❌ Focus states invisibles
- ❌ Scroll horizontal en mobile
- ❌ Contenido oculto detrás de navbars/sidebars fijos

## Fuera de alcance de este MASTER.md (no reabrir)

- Paleta y tipografía SANTI — fijas, este documento solo las cataloga
- Reglas de negocio, scoping por rol, estructura de datos — el Skill no opina sobre dominio
- El patrón de página "Marketplace/Directory" (hero de búsqueda + "conviértete en vendedor") que propuso el Skill crudo — **no aplica**, la estructura real de páginas ya está construida (dashboards por rol, catálogo universo→modelo→categoría) y no se reconstruye desde cero

---

## Pre-Delivery Checklist (Skill, aplicar antes de dar por cerrada cada pantalla en Pieza 1.D)

- [ ] Ningún emoji como ícono
- [ ] Un solo set de íconos (SVG inline ya usado en el proyecto)
- [ ] `cursor-pointer` en todo elemento clicable
- [ ] Transiciones 150-300ms en hover/estado
- [ ] Contraste ≥4.5:1 en ambos temas (claro y oscuro)
- [ ] Focus states visibles
- [ ] `prefers-reduced-motion` respetado
- [ ] Responsive real en 375px, 768px, 1440px (viewports de Pieza 4)
- [ ] Sin contenido oculto tras navbar/sidebar sticky
- [ ] Sin scroll horizontal en mobile

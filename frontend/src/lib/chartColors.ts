/**
 * Paleta de charts — validada con scripts/validate_palette.js del skill
 * dataviz (6 slots categóricos, PASS en claro y oscuro contra
 * surface-light #F8FAFC y surface-dark #0F172A). Orden fijo — nunca
 * ciclar ni reasignar por rango/filtro.
 */
export const CATEGORICAL = [
  '#0D9488', // teal — color de marca primario
  '#8B5CF6', // electric — color de marca secundario
  '#D97706', // ámbar
  '#E11D48', // rosa/rojo
  '#0284C7', // celeste
  '#4D7C0F', // verde oliva
] as const

// Reservados — nunca reutilizar para series categóricas.
export const STATUS = {
  good: '#16A34A',
  warning: '#D97706',
  critical: '#DC2626',
} as const

export const SEQUENTIAL_TEAL = ['#CCFBF1', '#5EEAD4', '#2DD4BF', '#0D9488', '#115E59'] as const

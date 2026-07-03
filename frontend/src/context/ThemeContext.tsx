'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { VarianteTema } from '@/src/lib/types'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'

interface ThemeContextValue {
  variante: VarianteTema
  setVariante: (v: VarianteTema) => Promise<void>
  themeError: string | null
}

// Caché local — se pobla desde el response de MFA y en cada PATCH exitoso.
// La fuente de verdad es siempre el backend (EP-USR-01). Esta clave
// solo persiste el último valor confirmado por el servidor para evitar
// flash en recargas. Se limpia en logout.
export const VARIANTE_TEMA_CACHE_KEY = 'tm_variante_tema'

const MENSAJES_ERROR: Record<string, string> = {
  VALIDACION_FALLIDA: 'Variante de tema no válida para tu perfil.',
  ACCESO_DENEGADO:    'No tienes permisos para cambiar el tema.',
  AUTENTICACION_REQUERIDA: 'Tu sesión expiró. Vuelve a iniciar sesión.',
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [variante, setVarianteState] = useState<VarianteTema>('OSCURO_ESTANDAR')
  const [themeError, setThemeError] = useState<string | null>(null)

  // Lee la caché tras hidratación — el valor fue puesto por MFA o por un PATCH previo
  useEffect(() => {
    const cached = localStorage.getItem(VARIANTE_TEMA_CACHE_KEY) as VarianteTema | null
    if (cached) setVarianteState(cached)
  }, [])

  async function setVariante(v: VarianteTema): Promise<void> {
    const anterior = variante
    setVarianteState(v)   // actualización optimista
    setThemeError(null)
    try {
      await apiClient.patch('/v1/usuarios/me/tema', { variante_tema: v })
      localStorage.setItem(VARIANTE_TEMA_CACHE_KEY, v)
    } catch (err) {
      setVarianteState(anterior)  // revertir si backend rechaza
      const code = (err as ApiCallError).code ?? 'ERROR_INTERNO'
      setThemeError(MENSAJES_ERROR[code] ?? 'No se pudo actualizar el tema. Intenta de nuevo.')
    }
  }

  return (
    <ThemeContext.Provider value={{ variante, setVariante, themeError }}>
      <div data-theme={variante} className="contents">
        {children}
      </div>
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}

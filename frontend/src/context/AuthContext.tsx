'use client'

import { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react'
import {
  AuthUser,
  Rol,
  rolToRoute,
  ApiCallError,
} from '@/src/lib/types'
import {
  apiClient,
  getStoredToken,
  setStoredToken,
  clearStoredToken,
  decodeJwtPayload,
  getDeviceToken,
  setDeviceToken,
} from '@/src/lib/api-client'
import { VARIANTE_TEMA_CACHE_KEY } from '@/src/context/ThemeContext'
import { useRouter } from 'next/navigation'

interface SesionInmediata {
  access_token: string
  variante_tema?: string
  device_token?: string
}

// Pieza 6-bis: login() ahora puede resolver de dos formas — si el
// dispositivo ya es confiable, el backend salta MFA y entrega la sesión de
// una vez (needsMfa: false); si no, sigue el flujo de siempre.
type LoginResultado =
  | { needsMfa: true; mfaSessionToken: string }
  | { needsMfa: false }

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<LoginResultado>
  verifyMfa: (mfaSessionToken: string, totpCode: string) => Promise<void>
  setAuthToken: (storedToken: string) => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

// Pieza 6-bis: sesión deslizante por rol — espejo de idle_window_para_rol en
// api/auth_stores.py. SUPERADMIN/ADMINISTRADOR trabajan sesiones largas de
// gestión activa (3h); el resto se cierra a los 15 min sin interacción real.
const IDLE_WINDOW_MINUTOS_MASTER = 180
const IDLE_WINDOW_MINUTOS_DEFAULT = 15
const ROLES_MASTER = new Set(['SUPERADMIN', 'ADMINISTRADOR'])
const REFRESH_INTERVALO_MS = 60_000

function idleWindowMs(rol: string): number {
  return (ROLES_MASTER.has(rol) ? IDLE_WINDOW_MINUTOS_MASTER : IDLE_WINDOW_MINUTOS_DEFAULT) * 60 * 1000
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const stored = getStoredToken()
    if (stored) {
      try {
        const payload = decodeJwtPayload(stored)
        if (payload.exp * 1000 > Date.now()) {
          setToken(stored)
          setUser({ id: payload.sub, rol: payload.rol as Rol })
          // Asegurar que la cookie esté sincronizada en el montaje de la app
          if (typeof document !== 'undefined') {
            document.cookie = `auth_token=${stored}; path=/; SameSite=Strict`
          }
        } else {
          clearStoredToken()
        }
      } catch {
        clearStoredToken()
      }
    }
    setLoading(false)
  }, [])

  // Pieza 6-bis: sesión deslizante — mientras haya interacción real en
  // pantalla (click/tecla/scroll/mouse), refresca el access_token cada
  // minuto para mantener la sesión viva. Si nadie interactúa durante la
  // ventana de inactividad del rol, cierra la sesión proactivamente en vez
  // de esperar a que una llamada cualquiera al API devuelva 401.
  const userIdRef = useRef<string | undefined>(undefined)
  const userRolRef = useRef<string | undefined>(undefined)
  userIdRef.current = user?.id
  userRolRef.current = user?.rol

  useEffect(() => {
    if (!user) return

    let ultimaActividad = Date.now()
    const marcarActividad = () => { ultimaActividad = Date.now() }
    const eventos: (keyof WindowEventMap)[] = ['mousemove', 'keydown', 'click', 'scroll']
    eventos.forEach(e => window.addEventListener(e, marcarActividad, { passive: true }))

    const intervalo = setInterval(async () => {
      const rol = userRolRef.current
      if (!rol) return
      if (Date.now() - ultimaActividad >= idleWindowMs(rol)) {
        clearInterval(intervalo)
        apiClient.post('/v1/auth/logout').catch(() => {})
        clearStoredToken()
        setToken(null)
        setUser(null)
        window.dispatchEvent(new CustomEvent('tm:session-expired'))
        return
      }
      try {
        const data = await apiClient.post<{ access_token: string }>('/v1/auth/refresh')
        setStoredToken(data.access_token)
        setToken(data.access_token)
      } catch {
        // El refresh falló porque la sesión ya murió en el backend (p.ej.
        // idle_window vencida entre ticks) — la próxima llamada al API
        // disparará tm:session-expired de forma reactiva (401), sin duplicar lógica aquí.
      }
    }, REFRESH_INTERVALO_MS)

    return () => {
      eventos.forEach(e => window.removeEventListener(e, marcarActividad))
      clearInterval(intervalo)
    }
  }, [user?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const aplicarSesion = useCallback((data: SesionInmediata) => {
    const payload = decodeJwtPayload(data.access_token)
    const authUser: AuthUser = { id: payload.sub, rol: payload.rol as Rol }
    setStoredToken(data.access_token)
    setToken(data.access_token)
    setUser(authUser)
    // Poblar caché de tema con el valor confirmado por el backend (EP-AUTH-02 / EP-USR-01)
    if (data.variante_tema) {
      localStorage.setItem(VARIANTE_TEMA_CACHE_KEY, data.variante_tema)
    }
    // Pieza 6-bis: guarda el nuevo token de dispositivo confiable — el
    // próximo login desde este mismo navegador saltará el paso de MFA.
    if (data.device_token) {
      setDeviceToken(data.device_token)
    }
    router.replace(rolToRoute(authUser.rol))
  }, [router])

  const login = useCallback(async (email: string, password: string): Promise<LoginResultado> => {
    const data = await apiClient.post<{
      mfa_session_token?: string
      access_token?: string
      variante_tema?: string
      device_token?: string
    }>('/v1/auth/login', { email, password, device_token: getDeviceToken() })

    // Pieza 6-bis: dispositivo ya confiable — el backend saltó MFA y entregó
    // la sesión completa directamente.
    if (data.access_token) {
      aplicarSesion({ access_token: data.access_token, variante_tema: data.variante_tema, device_token: data.device_token })
      return { needsMfa: false }
    }
    return { needsMfa: true, mfaSessionToken: data.mfa_session_token! }
  }, [aplicarSesion])

  const verifyMfa = useCallback(async (mfaSessionToken: string, totpCode: string): Promise<void> => {
    const data = await apiClient.post<{ access_token: string; token_type: string; variante_tema?: string; device_token?: string }>('/v1/auth/mfa', {
      mfa_session_token: mfaSessionToken,
      totp_code: totpCode,
    })
    aplicarSesion(data)
  }, [aplicarSesion])

  const setAuthToken = useCallback((storedToken: string): void => {
    const payload = decodeJwtPayload(storedToken)
    const authUser: AuthUser = { id: payload.sub, rol: payload.rol as Rol }
    setStoredToken(storedToken)
    setToken(storedToken)
    setUser(authUser)
  }, [])

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiClient.post('/v1/auth/logout')
    } catch {
      // token may already be invalid — proceed with local cleanup
    }
    clearStoredToken()
    localStorage.removeItem(VARIANTE_TEMA_CACHE_KEY)
    setToken(null)
    setUser(null)
    router.replace('/login')
  }, [router])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, verifyMfa, setAuthToken, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}

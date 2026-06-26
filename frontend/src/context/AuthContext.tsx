'use client'

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
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
} from '@/src/lib/api-client'
import { useRouter } from 'next/navigation'

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<string>
  verifyMfa: (mfaSessionToken: string, totpCode: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

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
        } else {
          clearStoredToken()
        }
      } catch {
        clearStoredToken()
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (email: string, password: string): Promise<string> => {
    const data = await apiClient.post<{ mfa_session_token: string }>('/v1/auth/login', { email, password })
    return data.mfa_session_token
  }, [])

  const verifyMfa = useCallback(async (mfaSessionToken: string, totpCode: string): Promise<void> => {
    const data = await apiClient.post<{ access_token: string; token_type: string }>('/v1/auth/mfa', {
      mfa_session_token: mfaSessionToken,
      totp_code: totpCode,
    })
    const accessToken = data.access_token
    const payload = decodeJwtPayload(accessToken)
    const authUser: AuthUser = { id: payload.sub, rol: payload.rol as Rol }
    setStoredToken(accessToken)
    setToken(accessToken)
    setUser(authUser)
    router.replace(rolToRoute(authUser.rol))
  }, [router])

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiClient.post('/v1/auth/logout')
    } catch {
      // token may already be invalid — proceed with local cleanup
    }
    clearStoredToken()
    setToken(null)
    setUser(null)
    router.replace('/login')
  }, [router])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, verifyMfa, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}

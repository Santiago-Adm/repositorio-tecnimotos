'use client'

import { ApiCallError } from './types'

// Rutas relativas — Next.js reescribe /v1/* → backend (ver next.config.mjs)
const API_BASE = ''
const TOKEN_KEY = 'tm_access_token'

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
  if (typeof document !== 'undefined') {
    document.cookie = `auth_token=${token}; path=/; SameSite=Strict`
  }
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  if (typeof document !== 'undefined') {
    document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict'
  }
}

export function decodeJwtPayload(token: string): { sub: string; rol: string; exp: number } {
  const [, payload] = token.split('.')
  const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
  return JSON.parse(atob(base64))
}

async function parseEnvelope<T>(res: Response): Promise<T> {
  const body = await res.json()

  if (!res.ok) {
    const err = body?.error ?? body?.detail?.error ?? body?.detail
    const code = err?.code ?? 'ERROR_INTERNO'
    const message = err?.message ?? res.statusText
    const detail = err?.detail

    if (res.status === 401) {
      typeof window !== 'undefined' &&
        window.dispatchEvent(new CustomEvent('tm:session-expired'))
    }

    throw new ApiCallError(code, message, detail)
  }

  return (body as { data: T }).data
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  extraHeaders?: Record<string, string>,
): Promise<T> {
  const token = getStoredToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extraHeaders,
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  })

  return parseEnvelope<T>(res)
}

async function requestForm<T>(method: string, path: string, form: FormData): Promise<T> {
  const token = getStoredToken()
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: form,
  })

  return parseEnvelope<T>(res)
}

export const apiClient = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  postForm: <T>(path: string, form: FormData) => requestForm<T>('POST', path, form),
  patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
  delete: <T>(path: string) => request<T>('DELETE', path),
}

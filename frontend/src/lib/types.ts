export type Rol =
  | 'SUPERADMIN'
  | 'ADMINISTRADOR'
  | 'VENDEDOR'
  | 'MECANICO_MASTER'
  | 'MECANICO_JUNIOR'
  | 'CLIENTE_CONDUCTOR'
  | 'CLIENTE_DISTRITO'
  | 'CLIENTE_RURAL'

export interface AuthUser {
  id: string
  rol: Rol
}

export interface ApiError {
  code: string
  message: string
  detail?: unknown
  request_id?: string
}

export class ApiCallError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly detail?: unknown,
  ) {
    super(message)
    this.name = 'ApiCallError'
  }
}

export type ApiResponse<T> = { data: T; meta: { request_id: string; timestamp: string; version: string } }

export function rolToRoute(rol: Rol): string {
  const map: Record<Rol, string> = {
    SUPERADMIN: '/app/superadmin',
    ADMINISTRADOR: '/app/administrador',
    VENDEDOR: '/app/vendedor',
    MECANICO_MASTER: '/app/mecanico-master',
    MECANICO_JUNIOR: '/app/mecanico-junior',
    CLIENTE_CONDUCTOR: '/app/conductor',
    CLIENTE_DISTRITO: '/app/distrito',
    CLIENTE_RURAL: '/app/rural',
  }
  return map[rol] ?? '/login'
}

export function rolToLanding(rol: Rol): string {
  const map: Partial<Record<Rol, string>> = {
    CLIENTE_CONDUCTOR: '/conductor',
    CLIENTE_DISTRITO: '/distrito',
    CLIENTE_RURAL: '/rural',
  }
  return map[rol] ?? '/login'
}

export function isClienteRol(rol: Rol): boolean {
  return rol.startsWith('CLIENTE_')
}

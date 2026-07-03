export type Rol =
  | 'SUPERADMIN'
  | 'ADMINISTRADOR'
  | 'VENDEDOR'
  | 'MECANICO_MASTER'
  | 'MECANICO_JUNIOR'
  | 'CLIENTE_CONDUCTOR'
  | 'CLIENTE_DISTRITO'
  | 'CLIENTE_RURAL'

export type VarianteTema =
  | 'OSCURO_ESTANDAR'
  | 'OSCURO_SUAVE'
  | 'OSCURO_ALTO_CONTRASTE'
  | 'CLARO_ESTANDAR'
  | 'CLARO_CALIDO'
  | 'CLARO_ALTO_CONTRASTE'

export const VARIANTES_OSCURAS: VarianteTema[] = [
  'OSCURO_ESTANDAR', 'OSCURO_SUAVE', 'OSCURO_ALTO_CONTRASTE',
]
export const VARIANTES_CLARAS: VarianteTema[] = [
  'CLARO_ESTANDAR', 'CLARO_CALIDO', 'CLARO_ALTO_CONTRASTE',
]

export const VARIANTE_LABEL: Record<VarianteTema, string> = {
  OSCURO_ESTANDAR:       'Estándar',
  OSCURO_SUAVE:          'Suavizado',
  OSCURO_ALTO_CONTRASTE: 'Alto contraste',
  CLARO_ESTANDAR:        'Estándar',
  CLARO_CALIDO:          'Cálido',
  CLARO_ALTO_CONTRASTE:  'Alto contraste',
}

export function variantesParaRol(rol: Rol): VarianteTema[] {
  return isClienteRol(rol) ? VARIANTES_CLARAS : VARIANTES_OSCURAS
}

export function defaultVarianteTema(rol: Rol): VarianteTema {
  return isClienteRol(rol) ? 'CLARO_ESTANDAR' : 'OSCURO_ESTANDAR'
}

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

// Espejo de api/routes/catalogo.py::RepuestoListItem/RepuestoDetalle/ImagenResumen
// (introspección real de los modelos Pydantic — openapi.json no los tipa: EP-CAT-01/02
// devuelven dict[str, Any] sin response_model, ver .doc3/05-trazabilidad-ligera.md).
export interface RepuestoListItem {
  id: string
  codigo: string
  nombre: string
  universo: string
  modelo: string
  año: number | null
  categoria: string
  activo: boolean
  advertencia_instalacion: boolean
  imagen_principal_url: string | null
  imagen_url: string | null
}

export interface ImagenResumen {
  imagen_id: string
  url: string
  orden: number
}

export interface RepuestoDetalle {
  id: string
  codigo: string
  nombre: string
  descripcion: string
  universo: string
  modelo: string
  año: number | null
  categoria: string
  activo: boolean
  advertencia_instalacion: boolean
  disponible: boolean
  opcion_notificacion: boolean
  imagenes: ImagenResumen[]
  imagen_url: string | null
}

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export const config = {
  matcher: ['/app/:path*'],
}

interface JwtPayload {
  sub: string
  rol: string
  exp: number
}

// Decodificador seguro y Edge-compatible
function decodeJwt(token: string): JwtPayload | null {
  try {
    const [, payload] = token.split('.')
    if (!payload) return null
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const decoded = atob(base64)
    return JSON.parse(decoded)
  } catch {
    return null
  }
}

// Matriz de capacidades/roles para rutas de /app/
function isAuthorized(rol: string, pathname: string): boolean {
  if (pathname.startsWith('/app/superadmin')) {
    return rol === 'SUPERADMIN'
  }
  if (pathname.startsWith('/app/administrador')) {
    return rol === 'SUPERADMIN' || rol === 'ADMINISTRADOR'
  }
  if (pathname.startsWith('/app/vendedor')) {
    return rol === 'VENDEDOR'
  }
  if (pathname.startsWith('/app/mecanico-master')) {
    return rol === 'MECANICO_MASTER'
  }
  if (pathname.startsWith('/app/mecanico-junior')) {
    return rol === 'MECANICO_JUNIOR'
  }
  if (pathname.startsWith('/app/conductor')) {
    return rol === 'CLIENTE_CONDUCTOR'
  }
  if (pathname.startsWith('/app/distrito')) {
    return rol === 'CLIENTE_DISTRITO'
  }
  if (pathname.startsWith('/app/rural')) {
    return rol === 'CLIENTE_RURAL'
  }
  return false
}

function getRaizOperativa(rol: string): string {
  const map: Record<string, string> = {
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

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname
  const token = request.cookies.get('auth_token')?.value

  // 1. Si no hay token, capturar URL y redirigir a /login?callbackUrl=...
  if (!token) {
    const callbackUrl = request.nextUrl.pathname + request.nextUrl.search
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('callbackUrl', callbackUrl)
    return NextResponse.redirect(loginUrl)
  }

  // 2. Interpretar el token JWT de forma segura
  const payload = decodeJwt(token)
  if (!payload) {
    // Token malformado o inválido: redirigir a login
    const loginUrl = new URL('/login', request.url)
    const response = NextResponse.redirect(loginUrl)
    response.cookies.delete('auth_token')
    return response
  }

  // Verificar expiración
  const nowSeconds = Math.floor(Date.now() / 1000)
  if (payload.exp && payload.exp < nowSeconds) {
    const loginUrl = new URL('/login', request.url)
    const response = NextResponse.redirect(loginUrl)
    response.cookies.delete('auth_token')
    return response
  }

  // 3. Verificar capacidades por rol (RBAC) y aplicar Graceful Recovery si es necesario
  if (!isAuthorized(payload.rol, pathname)) {
    const fallbackPath = getRaizOperativa(payload.rol)
    const fallbackUrl = new URL(fallbackPath, request.url)
    return NextResponse.redirect(fallbackUrl)
  }

  return NextResponse.next()
}

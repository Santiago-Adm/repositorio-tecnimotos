import type { Metadata, Viewport } from 'next'
import './globals.css'
import { AuthProvider } from '@/src/context/AuthContext'

export const metadata: Metadata = {
  title: 'Tecnimotos',
  description: 'Sistema de gestión Tecnimotos',
}

// Sin esto Next.js no emite <meta name="viewport">, así que los navegadores
// móviles renderizan a ~980px de ancho asumido y reducen/desbordan todo el
// layout (bug real reportado por Sant: landing raíz rota en Android).
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}

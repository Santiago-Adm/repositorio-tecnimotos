import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/src/context/AuthContext'

export const metadata: Metadata = {
  title: 'Tecnimotos',
  description: 'Sistema de gestión Tecnimotos',
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

import type { Metadata } from 'next'
import { Quicksand, Nunito_Sans, Fira_Code } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/src/context/AuthContext'

const quicksand = Quicksand({
  subsets: ['latin'],
  variable: '--font-display',
  display: 'swap',
})

const nunitoSans = Nunito_Sans({
  subsets: ['latin'],
  variable: '--font-body',
  weight: ['400', '600', '700'],
  display: 'swap',
})

const firaCode = Fira_Code({
  subsets: ['latin'],
  variable: '--font-mono',
  weight: ['400', '500'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Tecnimotos',
  description: 'Sistema de gestión Tecnimotos',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className={`${quicksand.variable} ${nunitoSans.variable} ${firaCode.variable} font-body antialiased`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}

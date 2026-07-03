'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { LogoSanti } from '@/src/components/ui/LogoSanti'
import { usePathname } from 'next/navigation'

const NAV_LINKS = [
  { href: '/catalogo', label: 'Catálogo' },
  { href: '/conductor', label: 'Conductor' },
  { href: '/distrito', label: 'Distrito' },
  { href: '/rural', label: 'Rural' },
]

const SEGMENTOS = ['conductor', 'distrito', 'rural'] as const

function registroHref(pathname: string): string {
  const segmento = SEGMENTOS.find(s => pathname.startsWith(`/${s}`))
  return `/${segmento ?? 'conductor'}/registro`
}

export default function PublicNavbar() {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)
  const [logoError, setLogoError] = useState(false)
  const logoRef = useRef<HTMLImageElement>(null)

  // El <img> se renderiza en el HTML servido por SSR y el navegador puede empezar
  // (y fallar) la carga antes de que React hidrate y conecte onError — se verifica
  // también tras montar, igual que recomienda la documentación de React para este caso.
  useEffect(() => {
    if (logoRef.current?.complete && logoRef.current.naturalWidth === 0) {
      setLogoError(true)
    }
  }, [])

  const esVariantMinima = pathname === '/login' || pathname.endsWith('/registro')

  return (
    <header className="sticky top-0 z-50 w-full bg-surface-dark/95 backdrop-blur-md border-b border-slate-800/60 px-4 lg:px-8 py-3 flex items-center justify-between">
      {/* Bloque de Identidad de Marca Unificado */}
      <Link href="/" className="flex items-center space-x-3 group select-none focus:outline-none" onClick={() => setIsOpen(false)}>
        <LogoSanti sizeClassName="w-12 h-12 lg:w-14 lg:h-14" />

        {/* Texto Nominal de la Empresa (Quicksand) */}
        <span className="text-2xl lg:text-3xl font-extrabold tracking-tight font-display bg-gradient-to-r from-[#0D9488] to-[#8B5CF6] bg-clip-text text-transparent group-hover:opacity-90 transition-opacity">
          SANTI
        </span>
      </Link>

      <nav className="hidden lg:flex items-center gap-1 font-body">
        {NAV_LINKS.map(link => {
          const activo = pathname === link.href
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`px-4 py-2 rounded-full font-semibold text-sm transition-all duration-200 ${
                activo ? 'text-teal bg-teal/15' : 'text-slate-300 hover:bg-teal/15 hover:text-teal'
              }`}
            >
              {link.label}
            </Link>
          )
        })}
      </nav>

      <div className="hidden lg:flex items-center gap-4">
        {esVariantMinima ? (
          <Link href="/" className="text-slate-300 hover:text-white text-sm font-semibold font-body transition-colors">
            ← Inicio
          </Link>
        ) : (
          <>
            <Link href="/login" className="text-slate-300 hover:text-white text-sm font-semibold font-body transition-colors">
              Iniciar Sesión
            </Link>
            <Link
              href={registroHref(pathname)}
              className="bg-teal hover:bg-teal/90 text-white font-semibold font-body text-sm px-5 py-2 rounded-full shadow-sm active:scale-95 transition-all"
            >
              Registrarse
            </Link>
          </>
        )}
      </div>

      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex lg:hidden text-slate-300 hover:text-white p-2 transition-colors"
        aria-label="Abrir menú"
      >
        {isOpen ? (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 w-full bg-surface-dark border-b border-slate-800 flex flex-col px-6 py-6 gap-4 z-40 lg:hidden shadow-xl">
          {NAV_LINKS.map(link => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setIsOpen(false)}
              className={`py-2 font-semibold text-base font-body transition-colors ${
                pathname === link.href ? 'text-teal' : 'text-slate-300 hover:text-white'
              }`}
            >
              {link.label}
            </Link>
          ))}

          <div className="h-px bg-slate-800/80 my-2" />

          {esVariantMinima ? (
            <Link href="/" onClick={() => setIsOpen(false)} className="text-center py-2.5 text-slate-300 font-semibold text-base font-body hover:text-white transition-colors">
              ← Inicio
            </Link>
          ) : (
            <>
              <Link href="/login" onClick={() => setIsOpen(false)} className="text-center py-2.5 text-slate-300 font-semibold text-base font-body hover:text-white transition-colors">
                Iniciar Sesión
              </Link>
              <Link
                href={registroHref(pathname)}
                onClick={() => setIsOpen(false)}
                className="w-full bg-teal hover:bg-teal/90 text-white font-semibold font-body text-base py-3 rounded-full shadow-md active:scale-[0.98] transition-all text-center"
              >
                Registrarse
              </Link>
            </>
          )}
        </div>
      )}
    </header>
  )
}

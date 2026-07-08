'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { LogoSanti } from '@/src/components/ui/LogoSanti'
import HamburgerIcon from '@/src/components/ui/HamburgerIcon'
import { useScrollSticky } from '@/src/lib/useScrollSticky'
import { usePathname } from 'next/navigation'

const NAV_LINKS = [
  { href: '/catalogo', label: 'Catálogo' },
  { href: '/conductor', label: 'Conductor' },
  { href: '/distrito', label: 'Distrito' },
  { href: '/rural', label: 'Rural' },
]

const SEGMENTOS = ['conductor', 'distrito', 'rural'] as const
const SPRING = { type: 'spring' as const, stiffness: 380, damping: 30 }

function registroHref(pathname: string): string {
  const segmento = SEGMENTOS.find(s => pathname.startsWith(`/${s}`))
  return `/${segmento ?? 'conductor'}/registro`
}

/** Ripple de un solo uso — expande desde el punto de click y se desvanece (CTA primario). */
function Ripple({ x, y }: { x: number; y: number }) {
  return (
    <motion.span
      initial={{ opacity: 0.5, scale: 0 }}
      animate={{ opacity: 0, scale: 4 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="absolute w-8 h-8 rounded-full bg-teal/30 pointer-events-none"
      style={{ left: x - 16, top: y - 16 }}
    />
  )
}

export default function PublicNavbar() {
  const pathname = usePathname()
  const reduceMotion = useReducedMotion()
  const { compacto, progreso } = useScrollSticky()
  const [isOpen, setIsOpen] = useState(false)
  const [logoError, setLogoError] = useState(false)
  const [ripples, setRipples] = useState<{ id: number; x: number; y: number }[]>([])
  const logoRef = useRef<HTMLImageElement>(null)

  useEffect(() => {
    if (logoRef.current?.complete && logoRef.current.naturalWidth === 0) {
      setLogoError(true)
    }
  }, [])

  // Escape cierra el menú móvil + bloquea el scroll del body mientras está abierto
  useEffect(() => {
    if (!isOpen) return
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setIsOpen(false)
    }
    document.addEventListener('keydown', onKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [isOpen])

  function lanzarRipple(e: React.MouseEvent<HTMLElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    const id = Date.now()
    setRipples(r => [...r, { id, x: e.clientX - rect.left, y: e.clientY - rect.top }])
    setTimeout(() => setRipples(r => r.filter(r2 => r2.id !== id)), 650)
  }

  const esVariantMinima = pathname === '/login' || pathname.endsWith('/registro')

  // Navbar flotante (Sant: "que se sienta más flotante, ahora está más estático"):
  // al inicio de la página va a bordes completos; al bajar (compacto) se despega
  // en una tarjeta redondeada con margen y sombra propia — deja de ser una barra
  // pegada al viewport y pasa a sentirse suspendida sobre el contenido.
  // Color (corrección Sant, ronda 2): bg-teal/80 con backdrop-saturate-150 se
  // veía demasiado saturado y el isotipo (paleta clara #a4cfda, ver logo-santi.svg)
  // se perdía contra el teal brillante. Ahora predomina Cobalt Dark (mismo token
  // que el resto del sistema) con un degradado de teal como "toque" sutil en la
  // esquina opuesta al logo — logo siempre sobre la zona más oscura. Sin
  // backdrop-saturate (amplificaba el brillo) y sin hex nuevo (10 §3.1/§3.6).
  return (
    <header
      className={`sticky z-50 flex items-center justify-between bg-gradient-to-br from-surface-dark via-surface-dark to-teal/30 backdrop-blur-xl transition-all duration-300 ${
        compacto
          ? 'top-3 mx-3 sm:mx-6 px-4 lg:px-8 py-2 rounded-2xl border border-teal/20 shadow-[0_20px_50px_-15px_rgba(13,148,136,0.35)]'
          : 'top-0 mx-0 px-4 lg:px-8 py-3 rounded-none border-b border-teal/15 shadow-none'
      }`}
    >
      {/* Barra de progreso de scroll */}
      <div
        className="absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-teal to-electric transition-[width] duration-150"
        style={{ width: `${progreso}%` }}
        aria-hidden="true"
      />

      {/* Identidad de marca — contenedor con shimmer al hover */}
      <Link href="/" className="relative flex items-center space-x-3 group select-none focus:outline-none overflow-visible" onClick={() => setIsOpen(false)}>
        <motion.div
          className="relative"
          whileHover={reduceMotion ? undefined : { scale: 1.06, rotate: -3 }}
          transition={SPRING}
        >
          <LogoSanti sizeClassName={compacto ? 'w-10 h-10 lg:w-11 lg:h-11' : 'w-12 h-12 lg:w-14 lg:h-14'} />
          {!reduceMotion && (
            <span className="absolute inset-0 overflow-hidden rounded-full pointer-events-none">
              <span className="absolute -inset-y-full -left-1/2 w-1/3 bg-gradient-to-r from-transparent via-white/40 to-transparent -skew-x-12 opacity-0 group-hover:opacity-100 group-hover:translate-x-[250%] transition-all duration-700 ease-out" />
            </span>
          )}
        </motion.div>

        {/* Gradiente blanco→electric (antes teal→electric): sobre el navbar teal
            nuevo, el extremo teal del degradado se perdía contra el propio fondo. */}
        <span className="text-2xl lg:text-3xl font-extrabold tracking-tight font-display bg-gradient-to-r from-white to-[#8B5CF6] bg-clip-text text-transparent group-hover:opacity-90 transition-opacity">
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
              className={`relative px-4 py-2 rounded-full font-semibold text-sm transition-colors duration-200 group/link ${
                activo ? 'text-white' : 'text-white/70 hover:text-white'
              }`}
            >
              {link.label}
              {/* Indicador en electric, no teal — teal se pierde sobre el fondo teal del navbar */}
              <span
                className={`absolute left-1/2 -translate-x-1/2 bottom-0.5 h-[2px] bg-electric rounded-full transition-transform duration-300 ease-out ${
                  activo ? 'w-2/3 scale-x-100' : 'w-2/3 scale-x-0 group-hover/link:scale-x-100'
                }`}
                aria-hidden="true"
              />
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
            {/* Botón invertido (blanco sobre teal) — bg-teal sólido se perdía
                contra el navbar teal nuevo; blanco da el contraste máximo. */}
            <Link
              href={registroHref(pathname)}
              onClick={lanzarRipple}
              className="relative overflow-hidden bg-white hover:bg-slate-50 text-teal font-semibold font-body text-sm px-5 py-2 rounded-full shadow-sm active:scale-95 transition-all"
            >
              Registrarse
              {ripples.map(r => <Ripple key={r.id} x={r.x} y={r.y} />)}
            </Link>
          </>
        )}
      </div>

      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex lg:hidden items-center justify-center w-10 h-10 text-slate-300 hover:text-white hover:bg-slate-800/60 rounded-lg transition-colors"
        aria-label={isOpen ? 'Cerrar menú' : 'Abrir menú'}
      >
        <HamburgerIcon abierto={isOpen} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 top-[57px] bg-black/40 backdrop-blur-sm z-30 lg:hidden"
              onClick={() => setIsOpen(false)}
              aria-hidden="true"
            />
            <motion.div
              initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
              animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
              exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
              transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
              className="absolute top-full left-0 w-full bg-surface-dark border-b border-slate-800 flex flex-col px-6 py-6 gap-1 z-40 lg:hidden shadow-2xl"
            >
              {NAV_LINKS.map((link, i) => (
                <motion.div
                  key={link.href}
                  initial={reduceMotion ? undefined : { opacity: 0, x: -12 }}
                  animate={reduceMotion ? undefined : { opacity: 1, x: 0 }}
                  transition={reduceMotion ? { duration: 0 } : { ...SPRING, delay: i * 0.04 }}
                >
                  <Link
                    href={link.href}
                    onClick={() => setIsOpen(false)}
                    className={`block py-2.5 px-2 rounded-lg font-semibold text-base font-body transition-colors ${
                      pathname === link.href ? 'text-teal bg-teal/10' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                    }`}
                  >
                    {link.label}
                  </Link>
                </motion.div>
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
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </header>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import HamburgerIcon from '@/src/components/ui/HamburgerIcon'

interface AppSidebarNavProps {
  secciones: readonly string[]
  activa: string
  onSeleccionar: (seccion: string) => void
  surface?: 'light' | 'dark'
}

const SPRING = { type: 'spring' as const, stiffness: 380, damping: 30 }

/**
 * Navegación compartida por los 8 roles (Pieza F) — antes cada dashboard
 * duplicaba su propio `<nav className="hidden md:flex ...">`, que
 * desaparecía por completo bajo 768px sin ningún reemplazo (FASE 0.4,
 * confirmado con grep real en los 8 `page.tsx`). Sidebar sticky + colapsable
 * en desktop, drawer animado en mobile — mismo spring que TiltCard
 * (Primitives.tsx, stiffness 300-400/damping 22-30) para mantener un solo
 * lenguaje de movimiento en todo el dashboard (motion-consistency).
 */
export default function AppSidebarNav({ secciones, activa, onSeleccionar, surface = 'dark' }: AppSidebarNavProps) {
  const isDark = surface === 'dark'
  const reduceMotion = useReducedMotion()
  const [colapsado, setColapsado] = useState(false)
  const [abierto, setAbierto] = useState(false)

  useEffect(() => {
    if (!abierto) return
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setAbierto(false)
    }
    document.addEventListener('keydown', onKeyDown)
    // Body-scroll-lock — evita que el fondo se desplace detrás del drawer en mobile.
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [abierto])

  function seleccionar(s: string) {
    onSeleccionar(s)
    setAbierto(false)
  }

  const textoActivo = isDark ? 'text-teal font-semibold' : 'text-teal font-semibold'
  const textoInactivo = isDark ? 'text-slate-300' : 'text-slate-600'
  const hoverInactivo = isDark ? 'hover:bg-slate-800/60' : 'hover:bg-slate-100'

  return (
    <>
      {/* Barra móvil sticky — reemplaza el sidebar oculto bajo 768px. Profundidad
          real (Skill: Dimensional Layering) en vez de una línea divisoria plana. */}
      <div className={`md:hidden sticky top-[57px] z-30 flex items-center justify-between px-4 py-2.5 backdrop-blur-md ${
        isDark
          ? 'bg-slate-900/80 shadow-[0_4px_16px_-4px_rgba(0,0,0,0.4)]'
          : 'bg-white/90 shadow-[0_4px_16px_-4px_rgba(15,23,42,0.08)]'
      }`}>
        <motion.button
          type="button"
          onClick={() => setAbierto(a => !a)}
          aria-label={abierto ? 'Cerrar menú de navegación' : 'Abrir menú de navegación'}
          whileTap={reduceMotion ? undefined : { scale: 0.9 }}
          className={`flex items-center justify-center w-11 h-11 -ml-2 rounded-lg ${isDark ? 'text-slate-300 hover:bg-slate-800' : 'text-slate-600 hover:bg-slate-100'}`}
        >
          <HamburgerIcon abierto={abierto} />
        </motion.button>
        <span className={`text-sm font-semibold font-body ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{activa}</span>
        <span className="w-11" aria-hidden="true" />
      </div>

      {/* Sidebar desktop — sticky bajo el header, colapsable. Elevación real
          (gradiente + sombra, mismo lenguaje que TiltCard en Primitives.tsx)
          en vez de una columna con borde plano. */}
      <nav
        className={`hidden md:flex flex-col shrink-0 self-start sticky top-[57px] p-3 gap-1 transition-[width] duration-200 overflow-y-auto ${
          colapsado ? 'w-16' : 'w-48'
        } ${
          isDark
            ? 'bg-gradient-to-b from-slate-900 to-slate-950 shadow-[4px_0_24px_-8px_rgba(0,0,0,0.35)]'
            : 'bg-white shadow-[4px_0_24px_-8px_rgba(15,23,42,0.06)]'
        }`}
        style={{ maxHeight: 'calc(100vh - 57px)' }}
      >
        <motion.button
          type="button"
          onClick={() => setColapsado(c => !c)}
          aria-label={colapsado ? 'Expandir menú' : 'Colapsar menú'}
          whileTap={reduceMotion ? undefined : { scale: 0.9 }}
          className={`self-end flex items-center justify-center w-8 h-8 mb-2 rounded-lg ${isDark ? 'text-slate-500 hover:bg-slate-800 hover:text-slate-300' : 'text-slate-400 hover:bg-slate-100 hover:text-slate-600'}`}
        >
          <motion.svg
            width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"
            animate={{ rotate: colapsado ? 180 : 0 }}
            transition={reduceMotion ? { duration: 0 } : SPRING}
          >
            <path d="M15 18l-6-6 6-6" />
          </motion.svg>
        </motion.button>
        {secciones.map(s => {
          const esActiva = activa === s
          return (
            <motion.button
              key={s}
              type="button"
              onClick={() => seleccionar(s)}
              title={colapsado ? s : undefined}
              whileHover={reduceMotion || esActiva ? undefined : { x: 3 }}
              whileTap={reduceMotion ? undefined : { scale: 0.97 }}
              transition={reduceMotion ? { duration: 0 } : SPRING}
              className={`relative text-left px-3 py-2 rounded-lg text-sm font-body ${esActiva ? textoActivo : `${textoInactivo} ${hoverInactivo}`} ${colapsado ? 'text-center' : ''}`}
            >
              {esActiva && (
                <motion.span
                  layoutId={`sidebar-activo-${surface}`}
                  className="absolute inset-0 rounded-lg bg-teal/10 border-l-4 border-teal shadow-[0_0_12px_rgba(13,148,136,0.15)]"
                  transition={reduceMotion ? { duration: 0 } : SPRING}
                />
              )}
              <span className="relative z-10">{colapsado ? s.slice(0, 2).toUpperCase() : s}</span>
            </motion.button>
          )
        })}
      </nav>

      {/* Drawer mobile — slide-in con backdrop, respeta prefers-reduced-motion */}
      <AnimatePresence>
        {abierto && (
          <div className="fixed inset-0 z-50 md:hidden">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="absolute inset-0 bg-black/50 backdrop-blur-sm"
              onClick={() => setAbierto(false)}
              aria-hidden="true"
            />
            <motion.div
              initial={reduceMotion ? { opacity: 0 } : { x: '-100%' }}
              animate={reduceMotion ? { opacity: 1 } : { x: 0 }}
              exit={reduceMotion ? { opacity: 0 } : { x: '-100%' }}
              transition={reduceMotion ? { duration: 0.15 } : SPRING}
              className={`absolute left-0 top-0 bottom-0 w-72 max-w-[80vw] overflow-y-auto p-4 shadow-xl ${
                isDark ? 'bg-slate-900 border-r border-slate-800' : 'bg-white border-r border-slate-200'
              }`}
            >
              <div className="flex items-center justify-between mb-4">
                <span className={`text-xs font-bold uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Navegación</span>
                <motion.button
                  type="button"
                  onClick={() => setAbierto(false)}
                  aria-label="Cerrar menú"
                  whileTap={reduceMotion ? undefined : { scale: 0.9 }}
                  className={`flex items-center justify-center w-11 h-11 -mr-2 rounded-lg ${isDark ? 'text-slate-400 hover:bg-slate-800' : 'text-slate-500 hover:bg-slate-100'}`}
                >
                  ✕
                </motion.button>
              </div>
              <div className="flex flex-col gap-1">
                {secciones.map((s, i) => {
                  const esActiva = activa === s
                  return (
                    <motion.button
                      key={s}
                      type="button"
                      onClick={() => seleccionar(s)}
                      initial={reduceMotion ? undefined : { opacity: 0, x: -12 }}
                      animate={reduceMotion ? undefined : { opacity: 1, x: 0 }}
                      transition={reduceMotion ? { duration: 0 } : { ...SPRING, delay: i * 0.03 }}
                      whileTap={reduceMotion ? undefined : { scale: 0.97 }}
                      className={`relative text-left px-3 py-3 rounded-lg text-sm font-body ${esActiva ? textoActivo : `${textoInactivo} ${hoverInactivo}`}`}
                    >
                      {esActiva && (
                        <motion.span
                          layoutId={`drawer-activo-${surface}`}
                          className="absolute inset-0 rounded-lg bg-teal/10 border-l-4 border-teal shadow-[0_0_12px_rgba(13,148,136,0.15)]"
                          transition={reduceMotion ? { duration: 0 } : SPRING}
                        />
                      )}
                      <span className="relative z-10">{s}</span>
                    </motion.button>
                  )
                })}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  )
}

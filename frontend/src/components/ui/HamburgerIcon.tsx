'use client'

import { motion, useReducedMotion } from 'framer-motion'

interface Props {
  abierto: boolean
  className?: string
}

/**
 * Rediseño de navegación (sesión 2026-07-05) — reemplaza el swap estático de
 * dos <svg> distintos (PublicNavbar) / ícono fijo (AppSidebarNav) por un
 * morph real a X. Barras <span> apiladas en vez de líneas SVG: una línea SVG
 * horizontal tiene bounding box de altura cero, lo que rompe originX/originY
 * en píxeles (primer intento produjo un chevron roto, no una X limpia).
 * Compartido entre navbar público y drawer de rol — un solo lenguaje visual.
 */
export default function HamburgerIcon({ abierto, className = '' }: Props) {
  const reduceMotion = useReducedMotion()
  const transition = reduceMotion ? { duration: 0 } : { duration: 0.25, ease: [0.4, 0, 0.2, 1] as const }

  const barra = 'absolute left-0 h-[2px] w-[22px] rounded-full bg-current'

  return (
    <span className={`relative inline-block w-[22px] h-[22px] ${className}`} aria-hidden="true">
      <motion.span
        className={barra}
        style={{ top: '5px' }}
        animate={abierto ? { top: '10px', rotate: 45 } : { top: '5px', rotate: 0 }}
        transition={transition}
      />
      <motion.span
        className={barra}
        style={{ top: '10px' }}
        animate={abierto ? { opacity: 0, x: -8 } : { opacity: 1, x: 0 }}
        transition={transition}
      />
      <motion.span
        className={barra}
        style={{ top: '15px' }}
        animate={abierto ? { top: '10px', rotate: -45 } : { top: '15px', rotate: 0 }}
        transition={transition}
      />
    </span>
  )
}

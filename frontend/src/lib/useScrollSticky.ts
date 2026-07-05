'use client'

import { useEffect, useState } from 'react'

interface ScrollSticky {
  /** true tras superar el umbral — dispara el modo compacto/glow del header */
  compacto: boolean
  /** 0-100, progreso de scroll de toda la página (barra superior) */
  progreso: number
}

/**
 * Rediseño de navegación (barra pública + dashboards de rol, sesión
 * 2026-07-05): ambos, PublicNavbar y DashboardHeader, necesitan la misma
 * reactividad de scroll (padding compacto + barra de progreso) — un solo
 * listener compartido en vez de duplicar la lógica en cada componente.
 */
export function useScrollSticky(umbralPx = 24): ScrollSticky {
  const [compacto, setCompacto] = useState(false)
  const [progreso, setProgreso] = useState(0)

  useEffect(() => {
    function onScroll() {
      const y = window.scrollY
      setCompacto(y > umbralPx)
      const alturaTotal = document.documentElement.scrollHeight - window.innerHeight
      setProgreso(alturaTotal > 0 ? Math.min(100, (y / alturaTotal) * 100) : 0)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [umbralPx])

  return { compacto, progreso }
}

'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Rol } from '@/src/lib/types'
import ThemeToggle from '@/src/components/ThemeToggle'
import Image from 'next/image'
import { useScrollSticky } from '@/src/lib/useScrollSticky'

const ROL_LABEL: Record<Rol, string> = {
  SUPERADMIN: 'Superadministrador',
  ADMINISTRADOR: 'Administrador',
  VENDEDOR: 'Vendedor',
  MECANICO_MASTER: 'Mecánico Master',
  MECANICO_JUNIOR: 'Mecánico Junior',
  CLIENTE_CONDUCTOR: 'Conductor',
  CLIENTE_DISTRITO: 'Distribuidor',
  CLIENTE_RURAL: 'Rural',
}

// Roles con dashboard de tema claro (mismo set que AppSidebarNav surface="light")
// — el mensaje central usa Cobalt Dark aquí en vez de Teal (Sant: el teal se
// perdía de contraste sobre el header claro, pidió usar cobalto oscuro).
const ROLES_CLARO = new Set<Rol>(['CLIENTE_CONDUCTOR', 'CLIENTE_DISTRITO', 'CLIENTE_RURAL'])

// Mensaje contextual junto al logo (sesión 2026-07-05, aprobado por Sant) —
// un mensaje por rol o compartido entre roles afines, nunca genérico.
const MENSAJE_ROL: Record<Rol, string> = {
  SUPERADMIN: 'Proyectando 15 años de confianza física hacia un sistema tecnológico líder en la región.',
  ADMINISTRADOR: 'Proyectando 15 años de confianza física hacia un sistema tecnológico líder en la región.',
  MECANICO_MASTER: 'El vehículo no está en un taller improvisado, sino en manos de ingeniería confiable.',
  MECANICO_JUNIOR: 'El vehículo no está en un taller improvisado, sino en manos de ingeniería confiable.',
  VENDEDOR: 'El vehículo y las herramientas de nuestros clientes son nuestra prioridad — su confianza está en nuestras manos.',
  CLIENTE_DISTRITO: 'El vehículo y las herramientas de nuestros clientes son nuestra prioridad — su confianza está en nuestras manos.',
  CLIENTE_CONDUCTOR: 'Entendemos tu urgencia y vamos a devolverte a la ruta.',
  CLIENTE_RURAL: 'Entendemos tu urgencia y vamos a devolverte a la ruta.',
}

interface Props {
  userId: string
  rol: Rol
  onLogout: () => void
  extraAction?: React.ReactNode
}

const SPRING = { type: 'spring' as const, stiffness: 380, damping: 30 }

/**
 * Rediseño de navegación (sesión 2026-07-05) — antes era una barra estática
 * sin ninguna reactividad de scroll ("se ve como un recuadro", feedback de
 * Sant); ahora comparte useScrollSticky con PublicNavbar (mismo lenguaje de
 * scroll compacto + barra de progreso en todo el sistema, no solo landings).
 */
export default function DashboardHeader({ userId, rol, onLogout, extraAction }: Props) {
  const [logoError, setLogoError] = useState(false)
  const logoRef = useRef<HTMLImageElement>(null)
  const reduceMotion = useReducedMotion()
  const { compacto, progreso } = useScrollSticky(16)
  const esClaro = ROLES_CLARO.has(rol)

  useEffect(() => {
    if (logoRef.current?.complete && logoRef.current.naturalWidth === 0) {
      setLogoError(true)
    }
  }, [])

  return (
    <header
      className={`sticky top-0 z-40 flex items-center justify-between bg-slate-900/90 backdrop-blur-xl backdrop-saturate-150 transition-[padding,box-shadow] duration-300 ${
        compacto
          ? 'px-4 md:px-6 py-2 border-b border-teal/20 shadow-[0_8px_30px_-14px_rgba(13,148,136,0.3)]'
          : 'px-4 md:px-6 py-3 border-b border-slate-800 shadow-sm'
      }`}
    >
      <div
        className="absolute bottom-0 left-0 h-[2px] bg-gradient-to-r from-teal to-electric transition-[width] duration-150"
        style={{ width: `${progreso}%` }}
        aria-hidden="true"
      />

      <div className="relative flex items-center gap-3 group select-none min-w-0">
        {!logoError ? (
          <motion.div
            className="relative w-10 h-10 shrink-0 flex items-center justify-center p-0.5 overflow-visible"
            whileHover={reduceMotion ? undefined : { scale: 1.08, rotate: -3 }}
            transition={SPRING}
          >
            <Image
              src="/brand/logo-santi.svg"
              alt="Tecnimotos"
              width={40}
              height={40}
              priority
              className="w-full h-full object-contain drop-shadow-[0_2px_10px_rgba(13,148,136,0.25)]"
              onError={() => {
                console.warn("Asset logo-santi.svg no detectado. Activando fallback de texto.");
                setLogoError(true);
              }}
            />
            {!reduceMotion && (
              <span className="absolute inset-0 overflow-hidden rounded-full pointer-events-none">
                <span className="absolute -inset-y-full -left-1/2 w-1/3 bg-gradient-to-r from-transparent via-white/40 to-transparent -skew-x-12 opacity-0 group-hover:opacity-100 group-hover:translate-x-[250%] transition-all duration-700 ease-out" />
              </span>
            )}
          </motion.div>
        ) : (
          <span className="text-lg font-display font-extrabold tracking-tight bg-gradient-to-r from-teal to-electric bg-clip-text text-transparent shrink-0">
            TECNIMOTOS SANTI
          </span>
        )}

        <span
          className="hidden sm:block text-base font-display font-extrabold tracking-tight bg-gradient-to-r from-teal to-electric bg-clip-text text-transparent"
          title="Sistema de Asistencia y Núcleo Técnico Integral"
        >
          SANTI
        </span>
      </div>

      {/* Mensaje contextual centrado — brillo real, no depende de background-clip
          (Sant reportó texto invisible con el gradiente+clip anterior en algún
          contexto suyo; color sólido + text-shadow es más robusto entre navegadores). */}
      <p
        className={`hidden xl:block absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center text-[13px] font-body font-semibold max-w-md leading-snug line-clamp-2 px-4 pointer-events-none ${
          esClaro ? 'text-[#0F172A]' : 'text-teal'
        }`}
        style={{ textShadow: esClaro ? '0 0 14px rgba(15,23,42,0.25)' : '0 0 18px rgba(13,148,136,0.55)' }}
      >
        {MENSAJE_ROL[rol]}
      </p>

      <div className="flex items-center gap-3">
        <div className="hidden sm:block text-right">
          <p className="text-xs text-slate-400 font-body">{ROL_LABEL[rol]}</p>
          <p className="text-xs font-mono text-slate-500 truncate max-w-[120px]">{userId}</p>
        </div>
        <ThemeToggle />
        {extraAction}
        <button
          onClick={onLogout}
          className="px-3 py-1.5 rounded-lg text-xs font-body text-slate-300 border border-slate-700 hover:bg-slate-800 hover:border-slate-600 active:scale-95 transition-all"
        >
          Cerrar sesión
        </button>
      </div>
    </header>
  )
}

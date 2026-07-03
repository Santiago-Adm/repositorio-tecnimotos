'use client'

import { useState, useEffect, useRef } from 'react'
import { Rol } from '@/src/lib/types'
import ThemeToggle from '@/src/components/ThemeToggle'
import Image from 'next/image'

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

interface Props {
  userId: string
  rol: Rol
  onLogout: () => void
  extraAction?: React.ReactNode
}

export default function DashboardHeader({ userId, rol, onLogout, extraAction }: Props) {
  const [logoError, setLogoError] = useState(false)
  const logoRef = useRef<HTMLImageElement>(null)

  useEffect(() => {
    if (logoRef.current?.complete && logoRef.current.naturalWidth === 0) {
      setLogoError(true)
    }
  }, [])

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between px-4 md:px-6 py-3 bg-slate-900/90 backdrop-blur border-b border-slate-800">
      <div className="flex items-center gap-3 group select-none">
        {!logoError ? (
          <div className="relative w-10 h-10 flex items-center justify-center p-0.5 overflow-visible">
            <Image
              src="/brand/logo-negativo.svg"
              alt="Tecnimotos"
              width={40}
              height={40}
              priority
              className="w-full h-full object-contain transform scale-110 transition-transform duration-300 group-hover:scale-115 drop-shadow-[0_2px_10px_rgba(13,148,136,0.25)]"
              onError={() => {
                console.warn("Asset logo-negativo.svg no detectado. Activando fallback de texto.");
                setLogoError(true);
              }}
            />
          </div>
        ) : (
          <span className="text-lg font-display font-extrabold tracking-tight bg-gradient-to-r from-teal to-electric bg-clip-text text-transparent">
            TECNIMOTOS SANTI
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden sm:block text-right">
          <p className="text-xs text-slate-400 font-body">{ROL_LABEL[rol]}</p>
          <p className="text-xs font-mono text-slate-500 truncate max-w-[120px]">{userId}</p>
        </div>
        <ThemeToggle />
        {extraAction}
        <button
          onClick={onLogout}
          className="px-3 py-1.5 rounded-lg text-xs font-body text-slate-300 border border-slate-700 hover:bg-slate-800 transition-colors"
        >
          Cerrar sesión
        </button>
      </div>
    </header>
  )
}


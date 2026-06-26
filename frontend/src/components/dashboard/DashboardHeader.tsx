'use client'

import { Rol } from '@/src/lib/types'

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
  return (
    <header className="sticky top-0 z-40 flex items-center justify-between px-4 md:px-6 py-3 bg-slate-900/90 backdrop-blur border-b border-slate-800">
      <div className="flex items-center gap-3">
        {/* Referencia al logo negativo — requiere /brand/logo-negativo.svg (10 §3.5) */}
        <img src="/brand/logo-negativo.svg" alt="Tecnimotos" className="h-7" />
      </div>
      <div className="flex items-center gap-4">
        <div className="hidden sm:block text-right">
          <p className="text-xs text-slate-400 font-body">{ROL_LABEL[rol]}</p>
          <p className="text-xs font-mono text-slate-500 truncate max-w-[120px]">{userId}</p>
        </div>
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

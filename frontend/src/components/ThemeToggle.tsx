'use client'

import { useState } from 'react'
import { useTheme } from '@/src/context/ThemeContext'
import { useAuth } from '@/src/context/AuthContext'
import { variantesParaRol, VARIANTE_LABEL, VarianteTema } from '@/src/lib/types'

export default function ThemeToggle() {
  const { variante, setVariante, themeError } = useTheme()
  const { user } = useAuth()
  const [open, setOpen] = useState(false)

  if (!user) return null

  const opciones = variantesParaRol(user.rol)

  async function elegir(v: VarianteTema) {
    setOpen(false)
    await setVariante(v)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(prev => !prev)}
        aria-label="Cambiar tema visual"
        title={`Tema: ${VARIANTE_LABEL[variante]}`}
        className="p-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="3" />
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
        </svg>
      </button>

      {open && (
        <>
          {/* overlay para cerrar al hacer clic fuera */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute right-0 top-full mt-1 z-50 min-w-[140px] rounded-xl border border-slate-700 bg-slate-900 shadow-lg py-1">
            {opciones.map(v => (
              <button
                key={v}
                onClick={() => elegir(v)}
                className={`w-full text-left px-3 py-2 text-xs font-body transition-colors ${
                  v === variante
                    ? 'text-teal bg-teal/10'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
                }`}
              >
                {v === variante && <span className="mr-1.5">✓</span>}
                {VARIANTE_LABEL[v]}
              </button>
            ))}
          </div>
        </>
      )}

      {themeError && (
        <p className="absolute right-0 top-full mt-2 z-50 text-xs font-body text-red-400 bg-slate-900 border border-red-900 rounded-lg px-3 py-2 min-w-[200px]">
          {themeError}
        </p>
      )}
    </div>
  )
}

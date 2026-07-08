'use client'

import { useEffect, useMemo, useRef, useState } from 'react'

interface ModeloDropdownProps {
  value: string
  onChange: (modelo: string) => void
  opciones: string[]
  surface?: 'light' | 'dark'
  label?: string
  placeholder?: string
}

/**
 * Selector de modelo con botón de despliegue manual — reemplaza el patrón
 * <input list> + <datalist> nativo, que en la mayoría de navegadores móviles
 * no muestra ningún affordance visible de "hay una lista para abrir"
 * (reportado por Sant sobre /catalogo). Un solo componente compartido por
 * el catálogo público y CatalogoNavegable.tsx (todos los roles internos).
 */
export default function ModeloDropdown({
  value, onChange, opciones, surface = 'dark', label = 'Modelo', placeholder = 'Todos los modelos',
}: ModeloDropdownProps) {
  const isDark = surface === 'dark'
  const [abierto, setAbierto] = useState(false)
  const [filtro, setFiltro] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!abierto) return
    function onClickFuera(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setAbierto(false)
      }
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setAbierto(false)
    }
    document.addEventListener('mousedown', onClickFuera)
    document.addEventListener('keydown', onKeyDown)
    inputRef.current?.focus()
    return () => {
      document.removeEventListener('mousedown', onClickFuera)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [abierto])

  useEffect(() => {
    if (!abierto) setFiltro('')
  }, [abierto])

  const opcionesFiltradas = useMemo(() => {
    const q = filtro.trim().toLowerCase()
    if (!q) return opciones
    return opciones.filter(o => o.toLowerCase().includes(q))
  }, [opciones, filtro])

  function seleccionar(modelo: string) {
    onChange(modelo)
    setAbierto(false)
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setAbierto(o => !o)}
        aria-haspopup="listbox"
        aria-expanded={abierto}
        className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg border transition-colors ${
          isDark
            ? 'text-slate-400 bg-slate-800/70 border-slate-700 hover:border-slate-600'
            : 'text-slate-500 bg-slate-100 border-slate-200 hover:border-slate-300'
        }`}
      >
        <span className="font-semibold uppercase tracking-wider text-[10px]">{label}:</span>
        <span className={`font-medium truncate max-w-[9rem] ${
          value ? (isDark ? 'text-slate-200' : 'text-slate-700') : isDark ? 'text-slate-600' : 'text-slate-400'
        }`}>
          {value || placeholder}
        </span>
        <svg
          className={`w-3.5 h-3.5 shrink-0 transition-transform duration-200 ${abierto ? 'rotate-180' : ''} ${isDark ? 'text-slate-500' : 'text-slate-400'}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {abierto && (
        <div
          role="listbox"
          className={`absolute z-50 mt-2 w-64 max-w-[80vw] rounded-xl border shadow-2xl overflow-hidden ${
            isDark ? 'bg-slate-900 border-slate-700' : 'bg-white border-slate-200'
          }`}
        >
          <div className={`p-2 border-b ${isDark ? 'border-slate-800' : 'border-slate-100'}`}>
            <input
              ref={inputRef}
              type="text"
              value={filtro}
              onChange={e => setFiltro(e.target.value)}
              placeholder="Filtrar modelos..."
              className={`w-full px-2.5 py-1.5 rounded-lg text-xs font-medium focus:outline-none focus:ring-1 focus:ring-teal/60 ${
                isDark ? 'bg-slate-800 text-slate-200 placeholder-slate-600' : 'bg-slate-50 text-slate-700 placeholder-slate-400'
              }`}
            />
          </div>
          <div className="max-h-64 overflow-y-auto py-1">
            <button
              type="button"
              role="option"
              aria-selected={!value}
              onClick={() => seleccionar('')}
              className={`w-full text-left px-3 py-2 text-xs font-semibold transition-colors ${
                !value
                  ? 'text-teal bg-teal/10'
                  : isDark ? 'text-slate-300 hover:bg-slate-800' : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              {placeholder}
            </button>
            {opcionesFiltradas.length === 0 ? (
              <p className={`px-3 py-2 text-xs italic ${isDark ? 'text-slate-600' : 'text-slate-400'}`}>
                Sin modelos que coincidan.
              </p>
            ) : (
              opcionesFiltradas.map(modelo => (
                <button
                  key={modelo}
                  type="button"
                  role="option"
                  aria-selected={modelo === value}
                  onClick={() => seleccionar(modelo)}
                  className={`w-full text-left px-3 py-2 text-xs font-medium truncate transition-colors ${
                    modelo === value
                      ? 'text-teal bg-teal/10'
                      : isDark ? 'text-slate-300 hover:bg-slate-800' : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {modelo}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

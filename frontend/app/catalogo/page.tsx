'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import PublicNavbar from '@/src/components/layout/PublicNavbar'
import PublicFooter from '@/src/components/ui/PublicFooter'
import RepuestoCard from '@/src/components/RepuestoCard'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError, RepuestoDetalle, RepuestoListItem } from '@/src/lib/types'

type Repuesto = RepuestoListItem

const CATEGORIAS = [
  { value: '', label: 'Todos' },
  { value: 'motor', label: 'Motor' },
  { value: 'transmision', label: 'Transmisión' },
  { value: 'frenos', label: 'Frenos' },
  { value: 'electrico', label: 'Eléctrico' },
  { value: 'carroceria', label: 'Carrocería' },
  { value: 'suspension', label: 'Suspensión' },
]

const PAGE_SIZE = 12

type Universo = 'mototaxi_3r' | 'mototaxi_4r' | 'motolineal'

const UNIVERSOS_VALIDOS: Universo[] = ['mototaxi_3r', 'mototaxi_4r', 'motolineal']

function esUniversoValido(v: string | null): v is Universo {
  return !!v && (UNIVERSOS_VALIDOS as string[]).includes(v)
}

function CatalogoContent() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const universoInicial = searchParams.get('universo')
  const [universo, setUniverso] = useState<Universo>(
    esUniversoValido(universoInicial) ? universoInicial : 'mototaxi_3r'
  )
  const [categoria, setCategoria] = useState<string>(searchParams.get('categoria') ?? '')
  const [modelo, setModelo] = useState<string>(searchParams.get('modelo') ?? '')
  const [modeloInput, setModeloInput] = useState<string>(searchParams.get('modelo') ?? '')
  const [page, setPage] = useState<number>(Number(searchParams.get('page')) || 1)
  const [busqueda, setBusqueda] = useState<string>(searchParams.get('q') ?? '')

  const [repuestos, setRepuestos] = useState<Repuesto[] | null>(null)
  const [total, setTotal] = useState(0)
  const [totalPaginas, setTotalPaginas] = useState(1)
  const [error, setError] = useState<string | null>(null)

  const [resultadoCodigo, setResultadoCodigo] = useState<RepuestoDetalle | null | 'no_encontrado'>(null)
  const [buscandoCodigo, setBuscandoCodigo] = useState(false)

  // Debounce del filtro de modelo (texto libre → server-side, EP-CAT-01 param real)
  useEffect(() => {
    const t = setTimeout(() => setModelo(modeloInput.trim()), 400)
    return () => clearTimeout(t)
  }, [modeloInput])

  // Sincronizar filtros a la URL
  useEffect(() => {
    const params = new URLSearchParams()
    params.set('universo', universo)
    if (categoria) params.set('categoria', categoria)
    if (modelo) params.set('modelo', modelo)
    if (busqueda) params.set('q', busqueda)
    if (page > 1) params.set('page', String(page))
    router.replace(`${pathname}?${params.toString()}`, { scroll: false })
  }, [universo, categoria, modelo, busqueda, page, router, pathname])

  async function cargar() {
    setError(null)
    setRepuestos(null)
    try {
      const params = new URLSearchParams({
        universo, page: String(page), limit: String(PAGE_SIZE),
      })
      if (modelo) params.set('modelo', modelo)
      if (categoria) params.set('categoria', categoria)
      const data = await apiClient.get<{ repuestos: Repuesto[]; total: number; total_paginas: number }>(
        `/v1/repuestos?${params.toString()}`
      )
      setRepuestos(data.repuestos)
      setTotal(data.total)
      setTotalPaginas(Math.max(1, data.total_paginas))
    } catch (err) {
      setError(err instanceof ApiCallError ? err.code : 'ERROR_INTERNO')
    }
  }

  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [universo, modelo, categoria, page])

  useEffect(() => {
    setPage(1)
  }, [universo, modelo, categoria])

  // Búsqueda por código directa (EP-CAT-02) — única forma de búsqueda por texto:
  // EP-CAT-01 no tiene parámetro de texto libre, así que el catálogo pagina
  // server-side (universo/categoria/modelo) y la búsqueda exacta por código
  // resuelve aparte contra GET /v1/repuestos/{codigo}.
  useEffect(() => {
    const term = busqueda.trim()
    if (!term.includes('-')) {
      setResultadoCodigo(null)
      return
    }
    let cancelado = false
    setBuscandoCodigo(true)
    apiClient
      .get<RepuestoDetalle>(`/v1/repuestos/${encodeURIComponent(term)}`)
      .then(r => { if (!cancelado) setResultadoCodigo(r) })
      .catch(() => { if (!cancelado) setResultadoCodigo('no_encontrado') })
      .finally(() => { if (!cancelado) setBuscandoCodigo(false) })
    return () => { cancelado = true }
  }, [busqueda])

  const mostrandoResultadoCodigo = busqueda.trim().includes('-')
  const paginaActual = Math.min(page, totalPaginas)

  return (
    <div className="min-h-screen bg-surface-dark flex flex-col text-slate-100 selection:bg-teal/30">
      <PublicNavbar />

      {/* A. HERO DE TRANSICIÓN PREMIUM CON VIDEO */}
      <section className="relative w-full h-[45vh] bg-[#0F172A] overflow-hidden flex items-center justify-center border-b border-slate-800/50">
        {/* Video en loop de fondo */}
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover opacity-40 select-none pointer-events-none"
        >
          <source src="/videos/transicion-catalogo.webm" type="video/webm" />
        </video>

        {/* Gradiente Overlay de cine */}
        <div className="absolute inset-0 bg-gradient-to-t from-surface-dark via-surface-dark/40 to-surface-dark/80" />

        {/* Contenido flotante */}
        <div className="relative z-10 flex flex-col items-center text-center px-4 max-w-3xl">
          <h1 className="font-display text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight drop-shadow-md">
            Ingeniería y Repuestos con Máxima Precisión
          </h1>
          <p className="mt-4 text-slate-300 text-sm sm:text-base font-semibold tracking-wide drop-shadow-sm font-sans">
            {total} repuestos físicos en Ayacucho
          </p>

          {/* Caja de Búsqueda Integrada — código exacto (ej. BAJ-4592) */}
          <div className="mt-8 w-full max-w-md relative">
            <input
              type="text"
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              placeholder="Busca por código exacto (ej. BAJ-4592)..."
              className="w-full px-5 py-3 rounded-full bg-slate-900/90 border border-slate-800/80 font-mono text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal/70 focus:border-transparent transition-all shadow-lg"
            />
          </div>
        </div>
      </section>

      {/* B. PESTAÑAS CENTRALES Y FILTROS DE MARCA */}
      <section className="w-full py-8 flex flex-col items-center justify-center space-y-6 bg-surface-dark/30 border-y border-slate-800/10">
        {/* Selectores de Marca Destacados (Bajaj 3R/4R / TVS) */}
        <div className="flex items-center space-x-3 bg-[#0b0f19]/70 p-1.5 rounded-full border border-slate-800/80 backdrop-blur-md">
          <button
            onClick={() => setUniverso('mototaxi_3r')}
            className={`px-6 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all duration-300 ${
              universo === 'mototaxi_3r'
                ? 'bg-teal text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
            }`}
          >
            Bajaj 3R
          </button>
          <button
            onClick={() => setUniverso('mototaxi_4r')}
            className={`px-6 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all duration-300 ${
              universo === 'mototaxi_4r'
                ? 'bg-teal text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
            }`}
          >
            Bajaj 4R
          </button>
          <button
            onClick={() => setUniverso('motolineal')}
            className={`px-6 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all duration-300 ${
              universo === 'motolineal'
                ? 'bg-teal text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
            }`}
          >
            TVS
          </button>
        </div>

        {/* Pestañas Centrales de Categorías */}
        <div className="w-full max-w-5xl px-4 overflow-visible flex items-center justify-center">
          <div className="flex items-center space-x-3 overflow-x-auto max-w-full px-4 scrollbar-none py-1.5 bg-[#0b0f19]/60 backdrop-blur-md rounded-full border border-slate-800/80 shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
            {CATEGORIAS.map(cat => {
              const active = cat.value === categoria
              return (
                <button
                  key={cat.value}
                  onClick={() => setCategoria(cat.value)}
                  className={`relative px-4 py-2 rounded-full text-xs font-semibold tracking-wider uppercase transition-all duration-300 shrink-0 ${
                    active
                      ? 'bg-teal text-white shadow-md'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                  }`}
                >
                  {cat.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Filtro de Modelo (texto libre — EP-CAT-01 param real, server-side) */}
        <div className="flex items-center space-x-2 text-xs text-slate-400 bg-[#0b0f19]/50 px-3 py-1.5 rounded-lg border border-slate-800/70 backdrop-blur-md">
          <span className="font-semibold uppercase tracking-wider text-[10px]">Modelo:</span>
          <input
            type="text"
            value={modeloInput}
            onChange={e => setModeloInput(e.target.value)}
            placeholder="Ej. King Deluxe"
            className="bg-transparent border-none text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-0 font-medium text-xs w-40"
          />
        </div>
      </section>

      {/* C. GRILLA DE PRODUCTOS */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 lg:px-8 py-10">
        {mostrandoResultadoCodigo ? (
          buscandoCodigo ? (
            <div className="py-20 flex justify-center"><LoadingIndicator message="Buscando código..." /></div>
          ) : resultadoCodigo === 'no_encontrado' ? (
            <div className="py-20 max-w-md mx-auto"><ErrorDisplay code="REPUECHO_NO_ENCONTRADO" context="búsqueda por código" /></div>
          ) : resultadoCodigo ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
              <RepuestoCard
                variant="grid"
                repuestoId={resultadoCodigo.id}
                codigo={resultadoCodigo.codigo}
                nombre={resultadoCodigo.nombre}
                modelo={resultadoCodigo.modelo}
                universo={resultadoCodigo.universo}
                disponible={resultadoCodigo.activo}
                imagenUrl={resultadoCodigo.imagen_url}
                imagenes={resultadoCodigo.imagenes}
                surface="dark"
              />
            </div>
          ) : null
        ) : error ? (
          <div className="py-20 max-w-md mx-auto"><ErrorDisplay code={error} onRetry={cargar} context="catálogo" /></div>
        ) : repuestos === null ? (
          <div className="py-20 flex justify-center"><LoadingIndicator message="Cargando catálogo..." /></div>
        ) : repuestos.length === 0 ? (
          <div className="py-20 text-center">
            <p className="text-sm text-slate-400 font-body">
              Sin resultados para los filtros seleccionados.
            </p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-6 text-xs text-slate-500 font-mono">
              <span>{total} repuestos encontrados</span>
              <span>Página {paginaActual} de {totalPaginas}</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
              {repuestos.map(r => (
                <RepuestoCard
                  key={r.codigo}
                  variant="grid"
                  repuestoId={r.id}
                  codigo={r.codigo}
                  nombre={r.nombre}
                  modelo={r.modelo}
                  universo={r.universo}
                  disponible={r.activo}
                  imagenUrl={r.imagen_principal_url}
                  surface="dark"
                />
              ))}
            </div>

            {/* D. PAGINACIÓN ASÍNCRONA */}
            {totalPaginas > 1 && (
              <div className="flex items-center justify-center gap-2 mt-16 pb-8">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={paginaActual === 1}
                  className="px-4 py-2 rounded-xl bg-[#0b0f19]/60 border border-slate-800/70 text-xs font-semibold hover:bg-slate-800/80 transition-colors disabled:opacity-40 disabled:hover:bg-[#0b0f19]/60 select-none text-slate-300"
                >
                  ← Anterior
                </button>
                <div className="flex items-center space-x-1">
                  {(() => {
                    const ventana = 2
                    const inicio = Math.max(1, paginaActual - ventana)
                    const fin = Math.min(totalPaginas, paginaActual + ventana)
                    const pags = []
                    for (let p = inicio; p <= fin; p++) pags.push(p)
                    return pags.map(pNum => {
                      const active = pNum === paginaActual
                      return (
                        <button
                          key={pNum}
                          onClick={() => setPage(pNum)}
                          className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
                            active
                              ? 'bg-teal text-white shadow-md'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-[#0b0f19]/60'
                          }`}
                        >
                          {pNum}
                        </button>
                      )
                    })
                  })()}
                </div>
                <button
                  onClick={() => setPage(p => Math.min(totalPaginas, p + 1))}
                  disabled={paginaActual === totalPaginas}
                  className="px-4 py-2 rounded-xl bg-[#0b0f19]/60 border border-slate-800/70 text-xs font-semibold hover:bg-slate-800/80 transition-colors disabled:opacity-40 disabled:hover:bg-[#0b0f19]/60 select-none text-slate-300"
                >
                  Siguiente →
                </button>
              </div>
            )}
          </>
        )}
      </main>

      <PublicFooter />
    </div>
  )
}

export default function CatalogoPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface-dark flex flex-col"><PublicNavbar /><div className="flex-1 flex items-center justify-center"><LoadingIndicator message="Cargando sistema..." /></div></div>}>
      <CatalogoContent />
    </Suspense>
  )
}

'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import PublicNavbar from '@/src/components/layout/PublicNavbar'
import PublicFooter from '@/src/components/ui/PublicFooter'
import RepuestoCard from '@/src/components/RepuestoCard'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'

interface Repuesto {
  id: string
  codigo: string
  nombre: string
  universo: string
  modelo: string
  categoria: string
  activo: boolean
  imagen_principal_url?: string | null
}

type Universo = 'mototaxi_3r' | 'mototaxi_4r' | 'motolineal'

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('')
  const [universo, setUniverso] = useState<Universo>('mototaxi_3r')

  const [repuestos, setRepuestos] = useState<Repuesto[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [videoError, setVideoError] = useState(false)

  async function cargar() {
    setError(null)
    setRepuestos(null)
    try {
      // EP-CAT-01 — sin auth, universo obligatorio (api/routes/catalogo.py). Nunca trae precio_venta.
      const data = await apiClient.get<{ repuestos: Repuesto[] }>(`/v1/repuestos?universo=${universo}`)
      setRepuestos(data.repuestos)
    } catch (err) {
      setError(err instanceof ApiCallError ? err.code : 'ERROR_INTERNO')
    }
  }

  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [universo])

  const filteredRepuestos = useMemo(() => {
    if (!repuestos) return []
    const query = searchQuery.toLowerCase().trim()
    if (query === '') return repuestos
    return repuestos.filter(r =>
      r.nombre.toLowerCase().includes(query) ||
      r.codigo.toLowerCase().includes(query) ||
      r.modelo.toLowerCase().includes(query),
    )
  }, [repuestos, searchQuery])

  return (
    <>
      <title>SANTI — Repuestos de Alta Fidelidad Comercial</title>

      <div className="min-h-screen font-body text-slate-800 bg-white">
        <PublicNavbar />

        {/* B. BLOQUE HERO DE BIENVENIDA */}
        <section className="relative w-full min-h-[85vh] flex flex-col items-center justify-center overflow-hidden bg-surface-dark pt-6 text-center">
          <div className="absolute top-0 left-0 w-full h-full z-0 bg-surface-dark">
            {!videoError ? (
              <video
                autoPlay
                loop
                muted
                playsInline
                controls={false}
                preload="auto"
                className="w-full h-full object-cover opacity-45 select-none pointer-events-none"
                onError={() => setVideoError(true)}
              >
                <source src="/transicion-santi.webm" type="video/webm" />
              </video>
            ) : (
              <div className="absolute inset-0 bg-gradient-to-br from-teal/20 to-electric/20" />
            )}
            <div className="absolute inset-0 bg-gradient-to-b from-surface-dark/80 via-transparent to-surface-dark/20" />
          </div>

          <div className="relative z-10 max-w-4xl mx-auto text-center flex flex-col items-center space-y-6 py-16 px-4 text-white">
            <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-semibold bg-teal/20 text-teal border border-teal/30 select-none">
              🛡️ 15 años de confianza garantizada en taller
            </span>

            <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight max-w-3xl">
              Encuentra el Repuesto <span className="bg-gradient-to-r from-teal to-electric bg-clip-text text-transparent">Exacto</span> para tu Moto
            </h1>

            <p className="text-slate-200 text-base md:text-lg max-w-2xl font-medium leading-relaxed">
              Consulta disponibilidad física instantánea, separa tus repuestos de forma remota y optimiza tus recorridos de compra en Ayacucho.
            </p>

            <div className="relative w-full max-w-2xl bg-white rounded-full shadow-2xl px-6 py-4 flex items-center mt-4 group">
              <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none text-slate-400">
                <svg className="w-5 h-5 group-focus-within:text-teal transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Busca repuestos por nombre o código de fábrica..."
                className="w-full font-body text-sm sm:text-base bg-transparent pl-7 pr-6 py-1 text-slate-800 focus:outline-none placeholder-slate-400"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="text-slate-400 hover:text-slate-600 text-xs font-semibold whitespace-nowrap"
                >
                  Limpiar
                </button>
              )}
            </div>

            <div className="flex items-center justify-center gap-3 mt-2">
              <span className="text-[11px] text-slate-300 font-bold uppercase tracking-wider">
                Universo:
              </span>
              <button
                onClick={() => setUniverso('mototaxi_3r')}
                className={`rounded-full px-5 py-2 text-xs font-bold transition-all duration-200 ${
                  universo === 'mototaxi_3r'
                    ? 'bg-electric text-white shadow-md shadow-electric/30'
                    : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
                }`}
              >
                Mototaxi 3R
              </button>
              <button
                onClick={() => setUniverso('mototaxi_4r')}
                className={`rounded-full px-5 py-2 text-xs font-bold transition-all duration-200 ${
                  universo === 'mototaxi_4r'
                    ? 'bg-electric text-white shadow-md shadow-electric/30'
                    : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
                }`}
              >
                Mototaxi 4R
              </button>
              <button
                onClick={() => setUniverso('motolineal')}
                className={`rounded-full px-5 py-2 text-xs font-bold transition-all duration-200 ${
                  universo === 'motolineal'
                    ? 'bg-electric text-white shadow-md shadow-electric/30'
                    : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
                }`}
              >
                Motolineal
              </button>
            </div>
          </div>

          <div className="absolute bottom-0 left-0 w-full overflow-hidden leading-[0] z-30">
            <svg
              viewBox="0 0 1200 120"
              preserveAspectRatio="none"
              className="relative block w-full h-[60px] text-surface-dark fill-current"
            >
              <path d="M0,32L120,42.7C240,53,480,75,720,74.7C960,75,1200,53,1320,42.7L1440,32L1440,120L1320,120C1200,120,960,120,720,120C480,120,240,120,120,120L0,120Z"></path>
            </svg>
          </div>
        </section>

        {/* D. SECCIÓN DEL ESCAPARATE PÚBLICO */}
        <section id="catalog-section" className="bg-surface-dark text-white py-16 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-white inline-block relative pb-3">
                Catálogo de Piezas Disponibles
                <span className="absolute bottom-0 left-1/4 right-1/4 h-[3px] bg-teal rounded-full"></span>
              </h2>
              {repuestos && (
                <p className="text-xs text-slate-400 font-mono mt-3 uppercase tracking-wider">
                  {filteredRepuestos.length === repuestos.length
                    ? `Mostrando ${filteredRepuestos.length} repuestos físicos en Ayacucho`
                    : `Filtrados ${filteredRepuestos.length} repuestos en catálogo`}
                </p>
              )}
            </div>

            {error ? (
              <ErrorDisplay code={error} onRetry={cargar} context="catálogo público" />
            ) : repuestos === null ? (
              <LoadingIndicator message="Cargando catálogo..." />
            ) : filteredRepuestos.length === 0 ? (
              <div className="text-center py-16 bg-slate-800 rounded-3xl border border-slate-800 max-w-md mx-auto px-6">
                <svg className="w-12 h-12 text-slate-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="font-display font-bold text-slate-200 text-lg mb-1">Sin resultados</h3>
                <p className="text-xs text-slate-400">Intenta buscar por otro término o limpia los filtros.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredRepuestos.map(r => (
                  <RepuestoCard
                    key={r.codigo}
                    variant="grid"
                    surface="dark"
                    repuestoId={r.id}
                    codigo={r.codigo}
                    nombre={r.nombre}
                    modelo={r.modelo}
                    universo={r.universo}
                    disponible={r.activo}
                    imagenUrl={r.imagen_principal_url}
                  />
                ))}
              </div>
            )}

            <div className="text-center mt-12">
              <Link
                href="/catalogo"
                className="inline-block text-sm font-body font-semibold text-teal hover:underline"
              >
                Ver catálogo completo con filtros →
              </Link>
            </div>

            {/* E. FOOTER CORPORATIVO */}
            <PublicFooter />
          </div>
        </section>
      </div>
    </>
  )
}

'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import PublicNavbar from '@/src/components/layout/PublicNavbar'
import PublicFooter from '@/src/components/ui/PublicFooter'
import ModeloDropdown from '@/src/components/ui/ModeloDropdown'
import RepuestoCard from '@/src/components/RepuestoCard'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError, RepuestoDetalle, RepuestoListItem } from '@/src/lib/types'

type Repuesto = RepuestoListItem

interface Categoria {
  id: string
  nombre: string
  orden: number
}

const PAGE_SIZE = 12

type Universo = 'mototaxi_3r' | 'mototaxi_4r' | 'motolineal'

const UNIVERSOS_VALIDOS: Universo[] = ['mototaxi_3r', 'mototaxi_4r', 'motolineal']

// Jerarquía real confirmada por Sant/Elena (PIEZA B, sesión 2026-07-03):
// 2R=motolineal, 3R=mototaxi_3r, 4R=mototaxi_4r.
const UNIVERSO_LABEL: Record<Universo, string> = {
  mototaxi_3r: '3R',
  mototaxi_4r: '4R',
  motolineal: '2R',
}

function esUniversoValido(v: string | null): v is Universo {
  return !!v && (UNIVERSOS_VALIDOS as string[]).includes(v)
}

// Códigos reales de la migración Bajaj: sin espacios, 7-18 caracteres
// alfanuméricos (confirmado: 16 192/16 195 sin guion). Un nombre de
// búsqueda ("filtro de aceite") sí tiene espacios — ver page.tsx (landing).
function esPosibleCodigo(termino: string): boolean {
  const t = termino.trim()
  return t.length >= 6 && !t.includes(' ')
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

  // Categorías dinámicas (EP-CAT-13) — nunca hardcodeadas. Si Elena agrega/quita
  // una categoría desde el dashboard de ADMIN, este catálogo se actualiza solo.
  const [categorias, setCategorias] = useState<Categoria[]>([])
  useEffect(() => {
    apiClient.get<{ categorias: Categoria[] }>('/v1/categorias')
      .then(data => setCategorias(data.categorias))
      .catch(() => setCategorias([]))
  }, [])

  // Modelos reales por universo (EP-CAT-17) — 107 valores confirmados en FASE 0.3,
  // pocos y reutilizables → autocomplete real, no texto libre disperso.
  const [modelosDisponibles, setModelosDisponibles] = useState<string[]>([])
  useEffect(() => {
    apiClient.get<{ modelos: string[] }>(`/v1/repuestos/modelos?universo=${universo}`)
      .then(data => setModelosDisponibles(data.modelos))
      .catch(() => setModelosDisponibles([]))
  }, [universo])

  // Debounce del filtro de modelo (texto libre → server-side, EP-CAT-01 param real)
  useEffect(() => {
    const t = setTimeout(() => setModelo(modeloInput.trim()), 400)
    return () => clearTimeout(t)
  }, [modeloInput])

  // Debounce de la caja de búsqueda del hero (código o nombre → EP-CAT-01 `q`, server-side
  // real sobre las 16 195 piezas). Antes `busqueda` solo alimentaba la búsqueda exacta por
  // código (EP-CAT-02); un término que no parecía código quedaba sin efecto (bug real
  // encontrado al conectar el filtro avanzado de código/nombre para todos los roles).
  const [q, setQ] = useState(busqueda.trim())
  useEffect(() => {
    const t = setTimeout(() => setQ(busqueda.trim()), 400)
    return () => clearTimeout(t)
  }, [busqueda])

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
      if (q) params.set('q', q)
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
  }, [universo, modelo, categoria, q, page])

  useEffect(() => {
    setPage(1)
  }, [universo, modelo, categoria, q])

  // Búsqueda por código directa (EP-CAT-02) — única forma de búsqueda por texto:
  // EP-CAT-01 no tiene parámetro de texto libre, así que el catálogo pagina
  // server-side (universo/categoria/modelo) y la búsqueda exacta por código
  // resuelve aparte contra GET /v1/repuestos/{codigo}.
  // Heurística de detección corregida (sesión 2026-07-04): antes exigía un
  // guion ("-"), asumiendo el formato mockeado "BAJ-4592". Confirmado real
  // contra los 16 195 repuestos de la migración: solo 3 códigos tienen guion,
  // el resto es alfanumérico plano de 7-18 caracteres sin espacios
  // (ej. "39050302", "01100317"). "Sin espacios y largo >= 6" es el criterio
  // real que distingue un código de una búsqueda por nombre.
  const mostrandoResultadoCodigo = esPosibleCodigo(busqueda)

  useEffect(() => {
    if (!mostrandoResultadoCodigo) {
      setResultadoCodigo(null)
      return
    }
    const term = busqueda.trim()
    let cancelado = false
    setBuscandoCodigo(true)
    apiClient
      .get<RepuestoDetalle>(`/v1/repuestos/${encodeURIComponent(term)}`)
      .then(r => { if (!cancelado) setResultadoCodigo(r) })
      .catch(() => { if (!cancelado) setResultadoCodigo('no_encontrado') })
      .finally(() => { if (!cancelado) setBuscandoCodigo(false) })
    return () => { cancelado = true }
  }, [busqueda, mostrandoResultadoCodigo])
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

          {/* Caja de Búsqueda Integrada — código exacto (ej. 39050302) muestra la
              ficha ampliada (EP-CAT-02); cualquier otro texto busca por código o
              nombre en todo el catálogo (EP-CAT-01 `q`, server-side real). */}
          <div className="mt-8 w-full max-w-md relative">
            <input
              type="text"
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              placeholder="Busca por código o nombre (ej. filtro de aceite)..."
              className="w-full px-5 py-3 rounded-full bg-slate-900/90 border border-slate-800/80 font-mono text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal/70 focus:border-transparent transition-all shadow-lg"
            />
          </div>
        </div>
      </section>

      {/* B. FILTROS POR JERARQUÍA VISUAL: universo → modelo → año → categoría
          (PIEZA A, sesión 2026-07-03 — reordenamiento visual puro, misma lógica
          de filtrado combinado de siempre; solo cambia orden y prominencia de render). */}
      <section className="w-full py-8 flex flex-col items-center justify-center space-y-6 bg-surface-dark/30 border-y border-slate-800/10">
        {/* Filtro 1: universo (2R=motolineal, 3R=mototaxi_3r, 4R=mototaxi_4r) — chips grandes, máxima prominencia */}
        <div className="flex items-center space-x-3 bg-[#0b0f19]/70 p-1.5 rounded-full border border-slate-800/80 backdrop-blur-md">
          {UNIVERSOS_VALIDOS.map(u => (
            <button
              key={u}
              onClick={() => setUniverso(u)}
              className={`px-6 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all duration-300 ${
                universo === u
                  ? 'bg-teal text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
              }`}
            >
              {UNIVERSO_LABEL[u]}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 flex-wrap justify-center">
          {/* Filtro 2: modelo — dropdown con botón de despliegue manual (107 valores
              confirmados, FASE 0.3), poblado desde GET /v1/repuestos/modelos. Antes era
              <input list>+<datalist> nativo, sin affordance visible en móvil (Sant). */}
          <ModeloDropdown
            value={modeloInput}
            onChange={setModeloInput}
            opciones={modelosDisponibles}
            surface="dark"
            placeholder="Todos los modelos"
          />

          {/* Filtro 3: año — deshabilitado hasta que Elena cargue datos reales
              (16 195/16 195 repuestos con año NULL hoy, confirmado FASE 0.3). */}
          <div
            title="Próximamente — falta que Elena cargue el año real de los repuestos"
            className="flex items-center space-x-2 text-xs text-slate-600 bg-[#0b0f19]/30 px-3 py-1.5 rounded-lg border border-slate-800/40 cursor-not-allowed select-none"
          >
            <span className="font-semibold uppercase tracking-wider text-[10px]">Año:</span>
            <span className="italic">Próximamente</span>
          </div>
        </div>

        {/* Filtro 4: categoría — chips dinámicos desde GET /v1/categorias, nunca
            hardcodeados. Si Elena crea/borra una categoría, aparece/desaparece sola.
            Secundario a propósito: debajo de modelo/año, escala menor, sin el
            fondo/blur/sombra que sí tiene universo — jerarquía visual real (PIEZA A). */}
        <div className="w-full max-w-5xl px-4 overflow-visible flex items-center justify-center">
          <div className="flex items-center space-x-2 overflow-x-auto max-w-full px-2 scrollbar-none py-1">
            <button
              onClick={() => setCategoria('')}
              className={`relative px-3 py-1 rounded-full text-[10px] font-semibold tracking-wider uppercase transition-all duration-300 shrink-0 ${
                categoria === ''
                  ? 'bg-teal/80 text-white'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/30'
              }`}
            >
              Todos
            </button>
            {categorias.map(cat => {
              const active = cat.nombre === categoria
              return (
                <button
                  key={cat.id}
                  onClick={() => setCategoria(cat.nombre)}
                  className={`relative px-3 py-1 rounded-full text-[10px] font-semibold tracking-wider uppercase transition-all duration-300 shrink-0 ${
                    active
                      ? 'bg-teal/80 text-white'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/30'
                  }`}
                >
                  {cat.nombre}
                </button>
              )
            })}
          </div>
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

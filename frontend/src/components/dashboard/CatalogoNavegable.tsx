'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import RepuestoCard from '@/src/components/RepuestoCard'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import ModeloDropdown from '@/src/components/ui/ModeloDropdown'
import { RepuestoListItem } from '@/src/lib/types'
import { useCatalogoNavegable, UNIVERSOS_VALIDOS, UNIVERSO_LABEL, Universo } from '@/src/lib/useCatalogoNavegable'

interface Categoria {
  id: string
  nombre: string
  orden: number
}

export interface StockInfo {
  codigo: string
  cantidad_disponible: number
  cantidad_apartada: number
  umbral_minimo: number
  esta_agotado: boolean
  esta_bajo_umbral: boolean
}

function nivelStock(s: StockInfo): 'CRITICO' | 'BAJO' | 'OPTIMO' {
  if (s.umbral_minimo > 0 && s.cantidad_disponible <= Math.floor(s.umbral_minimo / 2)) return 'CRITICO'
  if (s.esta_bajo_umbral) return 'BAJO'
  return 'OPTIMO'
}

const NIVEL_BADGE: Record<string, string> = {
  CRITICO: 'bg-red-900/30 text-red-400',
  BAJO: 'bg-electric/20 text-electric',
  OPTIMO: 'bg-teal/20 text-teal',
}

interface CatalogoNavegableProps {
  universoFijo?: Universo
  /** Pieza C (Conductor/Rural): universo/modelo iniciales tomados del
   *  vehículo del cliente — a diferencia de universoFijo, el universo
   *  sigue siendo seleccionable (aviso "Ver catálogo completo" explícito,
   *  decisión Sant 2026-07-05: auto-filtrado con salida, no bloqueo). */
  universoInicial?: Universo
  modeloInicial?: string
  /** ADMINISTRADOR/SUPERADMIN: muestra el botón "Editar" sobre cada tarjeta. */
  modoEdicion?: boolean
  onEditar?: (repuesto: RepuestoListItem) => void
  /** DISTRITO (Pieza D): botón "Agregar" para armar la lista de reserva
   *  progresiva navegando el catálogo, en vez de solo por código manual. */
  onAgregar?: (repuesto: RepuestoListItem) => void
  codigosAgregados?: string[]
  /** Roles internos (VENDEDOR/MECANICO_MASTER) consultan precio pero nunca
   *  reservan — se omite repuestoId para que RepuestoCard no muestre el
   *  flujo de reserva (pensado para clientes). */
  permitirReserva?: boolean
  pageSize?: number
  /** Pieza 2 (fusión Stock↔Catálogo, sesión de pulido): en vez de la tabla
   *  plana sin filtrar de "Stock general", reutiliza esta misma navegación
   *  universo→modelo→categoría, mostrando cantidad/umbral por repuesto. */
  modoStock?: boolean
  onEditarStock?: (repuesto: RepuestoListItem, stock: StockInfo | null) => void
  /** Dashboards internos (Administrador/Vendedor/Mecánico Máster) son tema
   *  oscuro; Conductor/Rural/Distrito son tema claro "ya decidido — NO
   *  oscurecer" (ver PrimitivesLight.tsx) — el motor debe respetar ambos. */
  surface?: 'light' | 'dark'
}

/**
 * Motor de navegación de catálogo (universo → modelo → categoría, paginado
 * server-side) compartido por Administrador (CRUD), Vendedor/Mecánico
 * Máster (solo lectura + precio bajo demanda), Distrito (solo reserva) y
 * Conductor/Rural (universo fijo al vehículo del cliente) — un solo
 * componente, nunca duplicado por rol (R17).
 */
export default function CatalogoNavegable({
  universoFijo, universoInicial, modeloInicial, modoEdicion = false, onEditar, onAgregar, codigosAgregados = [],
  permitirReserva = false, pageSize = 12, surface = 'dark', modoStock = false, onEditarStock,
}: CatalogoNavegableProps) {
  const isDark = surface === 'dark'
  const {
    universo, setUniverso, modelo, setModelo, categoria, setCategoria,
    busqueda, setBusqueda,
    page, setPage, repuestos, total, totalPaginas, loading, error,
    modelosDisponibles, recargar, universoBloqueado,
  } = useCatalogoNavegable({ universoFijo, universoInicial, pageSize })

  const [modeloInput, setModeloInput] = useState(modeloInicial ?? '')
  const [filtroVehiculoActivo, setFiltroVehiculoActivo] = useState(!!modeloInicial)
  useEffect(() => {
    const t = setTimeout(() => setModelo(modeloInput.trim()), 400)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modeloInput])

  // Filtro avanzado por código o nombre (EP-CAT-01 `q`) — mismo componente para
  // todos los roles que usan CatalogoNavegable (Administrador, Vendedor, Mecánico
  // Máster, Distrito, Conductor, Rural): "un solo componente, nunca duplicado por
  // rol" (R17, ver comentario de módulo más abajo). Búsqueda real server-side
  // sobre las 16 195 piezas, no solo la página cargada en memoria.
  const [busquedaInput, setBusquedaInput] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setBusqueda(busquedaInput.trim()), 400)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busquedaInput])

  function verCatalogoCompleto() {
    setFiltroVehiculoActivo(false)
    setModeloInput('')
  }

  const [categorias, setCategorias] = useState<Categoria[]>([])
  useEffect(() => {
    apiClient.get<{ categorias: Categoria[] }>('/v1/categorias')
      .then(data => setCategorias(data.categorias))
      .catch(() => setCategorias([]))
  }, [])

  // Pieza 2 — solo se consulta stock de los repuestos visibles en la página
  // actual (máx. `pageSize`), nunca los 16 195 de una vez (EP-STK-02 sin
  // paginar es el cuello de botella ya documentado, fuera de alcance tocarlo
  // — esta vista lo evita por diseño en vez de arreglarlo).
  const [stockPorCodigo, setStockPorCodigo] = useState<Record<string, StockInfo | null>>({})
  const [cargandoStock, setCargandoStock] = useState(false)
  useEffect(() => {
    if (!modoStock || !repuestos || repuestos.length === 0) return
    let activo = true
    setCargandoStock(true)
    Promise.all(
      repuestos.map(r =>
        apiClient.get<StockInfo>(`/v1/stock/${r.codigo}`).then(
          s => [r.codigo, s] as const,
          () => [r.codigo, null] as const,
        ),
      ),
    ).then(pares => {
      if (!activo) return
      setStockPorCodigo(Object.fromEntries(pares))
    }).finally(() => { if (activo) setCargandoStock(false) })
    return () => { activo = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modoStock, repuestos])

  const paginaActual = Math.min(page, totalPaginas)

  return (
    <div className="space-y-6">
      {filtroVehiculoActivo && (
        <div className={`flex items-center justify-between gap-3 px-4 py-2.5 rounded-xl border text-xs ${
          isDark ? 'bg-teal/10 border-teal/30 text-slate-300' : 'bg-teal/5 border-teal/20 text-slate-600'
        }`}>
          <span>Mostrando repuestos para tu vehículo — <strong>{modeloInicial}</strong> ({UNIVERSO_LABEL[universo]})</span>
          <button
            type="button"
            onClick={verCatalogoCompleto}
            className="font-semibold text-teal hover:underline shrink-0"
          >
            Ver catálogo completo
          </button>
        </div>
      )}

      {/* Breadcrumb de nivel (MASTER.md — patrón Drill-Down Analytics del Skill,
          Pieza 1.D): orienta en la jerarquía universo → modelo → categoría en
          vez de solo tabs sueltos sin indicar "dónde estoy". */}
      <nav aria-label="Nivel de navegación del catálogo" className={`flex items-center gap-1.5 text-[11px] font-mono ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
        <button
          type="button"
          onClick={() => { setModelo(''); setModeloInput(''); setCategoria('') }}
          disabled={!modelo && !categoria}
          className={`uppercase tracking-wide ${!modelo && !categoria ? 'text-teal font-semibold cursor-default' : 'hover:text-teal transition-colors'}`}
        >
          {UNIVERSO_LABEL[universo]}
        </button>
        {modelo && (
          <>
            <span aria-hidden="true">›</span>
            <button
              type="button"
              onClick={() => setCategoria('')}
              disabled={!categoria}
              className={!categoria ? 'text-teal font-semibold cursor-default' : 'hover:text-teal transition-colors'}
            >
              {modelo}
            </button>
          </>
        )}
        {categoria && (
          <>
            <span aria-hidden="true">›</span>
            <span className="text-teal font-semibold capitalize">{categoria}</span>
          </>
        )}
      </nav>

      <div className="flex flex-col gap-4">
        {!universoBloqueado && (
          <div className="flex items-center gap-2 flex-wrap">
            {UNIVERSOS_VALIDOS.map(u => (
              <button
                key={u}
                onClick={() => setUniverso(u)}
                className={`px-5 py-2 rounded-full text-xs font-bold tracking-wider uppercase transition-all duration-200 ${
                  universo === u
                    ? 'bg-teal text-white shadow-[0_0_16px_rgba(13,148,136,0.35)]'
                    : isDark
                      ? 'bg-slate-800/70 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                      : 'bg-slate-100 text-slate-500 hover:text-slate-700 hover:bg-slate-200'
                }`}
              >
                {UNIVERSO_LABEL[u]}
              </button>
            ))}
          </div>
        )}

        <div className="flex items-center gap-3 flex-wrap">
          <ModeloDropdown
            value={modeloInput}
            onChange={setModeloInput}
            opciones={modelosDisponibles}
            surface={surface}
            placeholder="Todos los modelos"
          />

          <div className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg border ${
            isDark ? 'text-slate-400 bg-slate-800/70 border-slate-700' : 'text-slate-500 bg-slate-100 border-slate-200'
          }`}>
            <span className="font-semibold uppercase tracking-wider text-[10px]">Código/Nombre:</span>
            <input
              type="text"
              value={busquedaInput}
              onChange={e => setBusquedaInput(e.target.value)}
              placeholder="Ej. filtro de aceite"
              className={`bg-transparent border-none focus:outline-none focus:ring-0 font-medium text-xs w-40 ${
                isDark ? 'text-slate-200 placeholder-slate-600' : 'text-slate-700 placeholder-slate-400'
              }`}
            />
          </div>

          <div className="flex items-center gap-2 overflow-x-auto min-w-0 max-w-full py-1">
            <button
              onClick={() => setCategoria('')}
              className={`px-3 py-1.5 rounded-full text-[10px] font-semibold tracking-wider uppercase transition-colors shrink-0 ${
                categoria === ''
                  ? 'bg-teal/80 text-white shadow-[0_0_12px_rgba(13,148,136,0.3)]'
                  : isDark ? 'bg-slate-800/50 text-slate-500 hover:text-slate-300' : 'bg-slate-100 text-slate-500 hover:text-slate-700'
              }`}
            >
              Todos
            </button>
            {categorias.map(cat => (
              <button
                key={cat.id}
                onClick={() => setCategoria(cat.nombre)}
                className={`px-3 py-1.5 rounded-full text-[10px] font-semibold tracking-wider uppercase transition-colors shrink-0 ${
                  categoria === cat.nombre
                    ? 'bg-teal/80 text-white shadow-[0_0_12px_rgba(13,148,136,0.3)]'
                    : isDark ? 'bg-slate-800/50 text-slate-500 hover:text-slate-300' : 'bg-slate-100 text-slate-500 hover:text-slate-700'
                }`}
              >
                {cat.nombre}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="py-16 flex justify-center"><LoadingIndicator message="Cargando catálogo..." /></div>
      ) : error ? (
        <ErrorDisplay code={error} onRetry={recargar} context="catálogo" />
      ) : !repuestos || repuestos.length === 0 ? (
        <EmptyState title="Sin resultados" description="No hay repuestos para los filtros seleccionados." />
      ) : (
        <>
          <div className="flex items-center justify-between text-xs text-slate-500 font-mono">
            <span>{total} repuestos encontrados</span>
            <span>Página {paginaActual} de {totalPaginas}</span>
          </div>

          {modoStock ? (
            <div className={`rounded-xl border overflow-hidden divide-y ${
              isDark ? 'border-slate-800 divide-slate-800' : 'border-slate-200 divide-slate-200'
            }`}>
              {repuestos.map(r => {
                const stock = stockPorCodigo[r.codigo]
                const nivel = stock ? nivelStock(stock) : null
                return (
                  <div key={r.codigo} className={`flex items-center justify-between gap-3 px-4 py-3 ${isDark ? 'bg-slate-900/40' : 'bg-white'}`}>
                    <div className="min-w-0">
                      <p className={`text-sm font-semibold truncate ${isDark ? 'text-slate-200' : 'text-slate-800'}`}>{r.nombre}</p>
                      <p className="text-xs font-mono text-slate-500 truncate">{r.codigo} · {r.modelo}</p>
                    </div>
                    <div className="flex items-center gap-4 shrink-0">
                      {cargandoStock && !stock ? (
                        <span className="text-xs text-slate-500 font-mono">…</span>
                      ) : stock ? (
                        <>
                          <div className="text-right">
                            <p className={`text-sm font-mono font-bold ${isDark ? 'text-slate-100' : 'text-slate-800'}`}>{stock.cantidad_disponible} uds</p>
                            <p className="text-[10px] text-slate-500 font-mono">mínimo: {stock.umbral_minimo}</p>
                          </div>
                          {nivel && (
                            <span className={`text-[10px] px-2 py-1 rounded-full font-semibold uppercase tracking-wide ${NIVEL_BADGE[nivel]}`}>
                              {nivel}
                            </span>
                          )}
                        </>
                      ) : (
                        <span className="text-xs text-slate-500 font-mono">Sin stock</span>
                      )}
                      <button
                        type="button"
                        onClick={() => onEditarStock?.(r, stock ?? null)}
                        className="px-2.5 py-1.5 rounded-lg bg-slate-950/90 border border-slate-700 text-[10px] font-bold uppercase tracking-wider text-teal hover:bg-slate-900 transition-colors"
                      >
                        Editar
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {repuestos.map(r => (
                <div key={r.codigo} className="relative">
                  <RepuestoCard
                    variant="grid"
                    repuestoId={permitirReserva ? r.id : undefined}
                    codigo={r.codigo}
                    nombre={r.nombre}
                    modelo={r.modelo}
                    universo={r.universo}
                    disponible={r.activo}
                    imagenUrl={r.imagen_principal_url}
                    surface={surface}
                  />
                  {modoEdicion && (
                    <button
                      type="button"
                      onClick={() => onEditar?.(r)}
                      className="absolute top-2 right-2 z-10 px-2.5 py-1.5 rounded-lg bg-slate-950/90 border border-slate-700 text-[10px] font-bold uppercase tracking-wider text-teal hover:bg-slate-900 transition-colors"
                    >
                      Editar
                    </button>
                  )}
                  {!modoEdicion && onAgregar && (
                    <button
                      type="button"
                      disabled={codigosAgregados.includes(r.codigo)}
                      onClick={() => onAgregar(r)}
                      className="absolute top-2 right-2 z-10 px-2.5 py-1.5 rounded-lg bg-slate-950/90 border border-slate-700 text-[10px] font-bold uppercase tracking-wider text-teal hover:bg-slate-900 transition-colors disabled:opacity-50 disabled:text-slate-500 disabled:cursor-not-allowed"
                    >
                      {codigosAgregados.includes(r.codigo) ? 'Agregado ✓' : 'Agregar'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {totalPaginas > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={paginaActual === 1}
                className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors disabled:opacity-40 ${
                  isDark ? 'bg-slate-800/70 border-slate-700 text-slate-300 hover:bg-slate-800' : 'bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200'
                }`}
              >
                ← Anterior
              </button>
              <span className="text-xs text-slate-500 font-mono px-2">{paginaActual} / {totalPaginas}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPaginas, p + 1))}
                disabled={paginaActual === totalPaginas}
                className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors disabled:opacity-40 ${
                  isDark ? 'bg-slate-800/70 border-slate-700 text-slate-300 hover:bg-slate-800' : 'bg-slate-100 border-slate-200 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Siguiente →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'

interface Metricas {
  ots_activas: number
  pedidos_activos_hoy: number
  repuestos_bajo_umbral: number
  comprobantes_emitidos_periodo: number
  periodo_comprobantes: { desde: string; hasta: string }
}

interface Categoria { id: string; nombre: string; orden: number }
interface Mecanico { mecanico_id: string; usuario_id: string; nombre: string; nivel: string; disponible: boolean }

type Universo = 'motolineal' | 'mototaxi_3r' | 'mototaxi_4r'
const UNIVERSO_LABEL: Record<Universo, string> = { motolineal: '2R', mototaxi_3r: '3R', mototaxi_4r: '4R' }

function hoyISO(): string {
  return new Date().toISOString().slice(0, 10)
}
function inicioMesISO(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

interface KpiCardProps {
  label: string
  value: string
  accent: 'teal' | 'electric' | 'slate' | 'alert'
}

function KpiCard({ label, value, accent }: KpiCardProps) {
  const accentText = {
    teal: 'text-teal', electric: 'text-electric', slate: 'text-slate-200', alert: 'text-red-400',
  }[accent]
  const accentGlow = {
    teal: 'bg-teal/5 group-hover:bg-teal/10', electric: 'bg-electric/5 group-hover:bg-electric/10',
    slate: 'bg-slate-200/5 group-hover:bg-slate-200/10', alert: 'bg-red-500/10',
  }[accent]
  const borderCls = accent === 'alert' ? 'border-red-500/40 bg-red-950/5' : 'border-slate-700/80'

  return (
    <div className={`rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border p-5 shadow-lg relative overflow-hidden group ${borderCls}`}>
      <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">{label}</p>
      <p className={`text-3xl lg:text-4xl font-mono font-extrabold tracking-tight ${accentText}`}>{value}</p>
      <div className={`absolute bottom-0 right-0 w-24 h-24 rounded-full blur-2xl transition-colors ${accentGlow}`} />
    </div>
  )
}

/**
 * Panel BI premium — ADR-015. Compartido entre ADMINISTRADOR y SUPERADMIN
 * (mismo nivel analítico). KPIs reales + filtros premium (rango libre de
 * fechas, categoría, universo, mecánico) contra EP-ADM-10.
 */
export default function BiPanel() {
  const [metricas, setMetricas] = useState<Metricas | null>(null)
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [mecanicos, setMecanicos] = useState<Mecanico[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [desde, setDesde] = useState(inicioMesISO())
  const [hasta, setHasta] = useState(hoyISO())
  const [categoria, setCategoria] = useState('')
  const [universo, setUniverso] = useState('')
  const [mecanicoId, setMecanicoId] = useState('')

  const [configAbierta, setConfigAbierta] = useState(false)
  const [estadosOt, setEstadosOt] = useState('')
  const [diasMaximo, setDiasMaximo] = useState('')
  const [guardandoConfig, setGuardandoConfig] = useState(false)
  const [configMsg, setConfigMsg] = useState<string | null>(null)

  function fetchMetricas() {
    setLoading(true)
    setError(null)
    const params = new URLSearchParams()
    if (desde) params.set('desde', desde)
    if (hasta) params.set('hasta', hasta)
    if (categoria) params.set('categoria', categoria)
    if (universo) params.set('universo', universo)
    if (mecanicoId) params.set('mecanico_id', mecanicoId)
    apiClient
      .get<Metricas>(`/v1/admin/metricas-negocio?${params.toString()}`)
      .then(d => { setMetricas(d); setLoading(false) })
      .catch((err: ApiCallError) => { setError(err.code); setLoading(false) })
  }

  useEffect(() => {
    apiClient.get<{ categorias: Categoria[] }>('/v1/categorias').then(d => setCategorias(d.categorias)).catch(() => {})
    apiClient.get<{ mecanicos: Mecanico[] }>('/v1/admin/mecanicos').then(d => setMecanicos(d.mecanicos)).catch(() => {})
    apiClient
      .get<{ parametros: Array<{ clave: string; valor: unknown }> }>('/v1/admin/parametros')
      .then(d => {
        const estados = d.parametros.find(p => p.clave === 'taller.ot_activa.estados')
        const dias = d.parametros.find(p => p.clave === 'taller.ot_activa.dias_maximo')
        if (estados) setEstadosOt(String(estados.valor))
        if (dias) setDiasMaximo(String(dias.valor))
      })
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => { fetchMetricas() }, [desde, hasta, categoria, universo, mecanicoId]) // eslint-disable-line react-hooks/exhaustive-deps

  async function guardarConfigOtActiva() {
    setGuardandoConfig(true)
    setConfigMsg(null)
    try {
      await apiClient.patch('/v1/admin/parametros/taller.ot_activa.estados', { valor: estadosOt })
      await apiClient.patch('/v1/admin/parametros/taller.ot_activa.dias_maximo', { valor: Number(diasMaximo) })
      setConfigMsg('Guardado — la regla de "OT activa" ya usa estos valores.')
      fetchMetricas()
    } catch (err) {
      setConfigMsg(err instanceof ApiCallError ? err.message : 'No se pudo guardar la configuración.')
    } finally {
      setGuardandoConfig(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-100">Panel de control</h1>
        <p className="text-sm text-slate-400 font-body">
          Indicadores del negocio en tiempo real, con rango de fechas y filtros libres.
        </p>
      </div>

      {/* Barra de filtros premium */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 p-4 flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-500 font-body uppercase tracking-wide">Desde</label>
          <input
            type="date" value={desde} onChange={e => setDesde(e.target.value)}
            className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-teal/50"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-500 font-body uppercase tracking-wide">Hasta</label>
          <input
            type="date" value={hasta} onChange={e => setHasta(e.target.value)}
            className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-teal/50"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-500 font-body uppercase tracking-wide">Universo</label>
          <select
            value={universo} onChange={e => setUniverso(e.target.value)}
            className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-electric/50"
          >
            <option value="">Todos</option>
            {(Object.keys(UNIVERSO_LABEL) as Universo[]).map(u => (
              <option key={u} value={u}>{UNIVERSO_LABEL[u]}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-500 font-body uppercase tracking-wide">Categoría</label>
          <select
            value={categoria} onChange={e => setCategoria(e.target.value)}
            className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-electric/50"
          >
            <option value="">Todas</option>
            {categorias.map(c => <option key={c.id} value={c.nombre}>{c.nombre}</option>)}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-slate-500 font-body uppercase tracking-wide">Mecánico</label>
          <select
            value={mecanicoId} onChange={e => setMecanicoId(e.target.value)}
            className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-electric/50"
          >
            <option value="">Todos</option>
            {mecanicos.map(m => <option key={m.mecanico_id} value={m.mecanico_id}>{m.nombre} ({m.nivel})</option>)}
          </select>
        </div>
        {(categoria || universo || mecanicoId) && (
          <button
            onClick={() => { setCategoria(''); setUniverso(''); setMecanicoId('') }}
            className="text-xs text-slate-400 font-body hover:text-slate-200 hover:underline pb-2.5"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {loading ? (
        <LoadingIndicator message="Calculando métricas..." />
      ) : error ? (
        <ErrorDisplay code={error} onRetry={fetchMetricas} />
      ) : metricas ? (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-display text-sm font-semibold text-slate-400 uppercase tracking-wide">
              Resultado del período
            </h2>
            <span className="text-xs font-body text-slate-500">
              {metricas.periodo_comprobantes.desde} al {metricas.periodo_comprobantes.hasta}
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              label="Ingresos del período"
              value={`S/ ${metricas.comprobantes_emitidos_periodo.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`}
              accent="teal"
            />
            <KpiCard label="Órdenes de trabajo activas" value={String(metricas.ots_activas)} accent="electric" />
            <KpiCard label="Pedidos de hoy" value={String(metricas.pedidos_activos_hoy)} accent="slate" />
            <KpiCard
              label="Stock bajo umbral"
              value={String(metricas.repuestos_bajo_umbral)}
              accent={metricas.repuestos_bajo_umbral > 0 ? 'alert' : 'slate'}
            />
          </div>
        </div>
      ) : null}

      {/* Configuración de "OT activa" — ADR-015: estado + días, configurable */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 overflow-hidden">
        <button
          onClick={() => setConfigAbierta(v => !v)}
          className="w-full flex items-center justify-between px-5 py-3 text-left"
        >
          <span className="text-sm font-display font-semibold text-slate-300">
            Configuración: qué cuenta como &quot;OT activa&quot;
          </span>
          <span className="text-slate-500 text-xs font-body">{configAbierta ? 'Ocultar ▲' : 'Mostrar ▼'}</span>
        </button>
        {configAbierta && (
          <div className="px-5 pb-5 pt-1 space-y-3 border-t border-slate-800">
            <p className="text-xs text-slate-500 font-body">
              Una orden de trabajo cuenta como activa si su estado está en la lista de abajo
              Y no lleva abierta más de los días máximos indicados.
            </p>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500 font-body uppercase tracking-wide">
                Estados que cuentan como activa (separados por coma)
              </label>
              <input
                type="text" value={estadosOt} onChange={e => setEstadosOt(e.target.value)}
                className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm font-mono text-slate-200 focus:outline-none focus:ring-2 focus:ring-teal/50"
              />
            </div>
            <div className="flex flex-col gap-1 max-w-xs">
              <label className="text-xs text-slate-500 font-body uppercase tracking-wide">Días máximo abierta</label>
              <input
                type="number" min={1} value={diasMaximo} onChange={e => setDiasMaximo(e.target.value)}
                className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm font-mono text-slate-200 focus:outline-none focus:ring-2 focus:ring-teal/50"
              />
            </div>
            <button
              onClick={guardarConfigOtActiva}
              disabled={guardandoConfig}
              className="px-4 py-2 rounded-lg bg-teal text-white text-sm font-semibold hover:bg-teal/90 transition-colors disabled:opacity-50"
            >
              {guardandoConfig ? 'Guardando...' : 'Guardar configuración'}
            </button>
            {configMsg && <p className="text-xs text-slate-400 font-body">{configMsg}</p>}
          </div>
        )}
      </div>
    </div>
  )
}

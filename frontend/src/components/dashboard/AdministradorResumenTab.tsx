'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import { CATEGORICAL } from '@/src/lib/chartColors'
import {
  StatCard, DonutChart, BarRankingHorizontal, BarVertical, RadarWidget,
  ScatterWidget, StackedBarWidget, MultiLineWidget, IconStatCard, TiltCard,
} from '@/src/components/dashboard/charts/Primitives'

interface Metricas { comprobantes_emitidos_periodo: number }
interface RankingItem { id: string; nombre: string; total: number; ots_completadas?: number }
interface Pedido { pedido_id: string; estado: string; created_at: string }
interface StockItem { esta_bajo_umbral: boolean; codigo: string }

function inicioMesISO() { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01` }
function hoyISO() { return new Date().toISOString().slice(0, 10) }

export default function AdministradorResumenTab() {
  const [desde, setDesde] = useState(inicioMesISO())
  const [hasta, setHasta] = useState(hoyISO())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [ingresosTotales, setIngresosTotales] = useState(0)
  const [totalPedidos, setTotalPedidos] = useState(0)
  const [topVendedores, setTopVendedores] = useState<RankingItem[]>([])
  const [topMecanicos, setTopMecanicos] = useState<RankingItem[]>([])
  const [pagadoNoPagado, setPagadoNoPagado] = useState<{ clave: string; valor: number }[]>([])
  const [ingresosMensuales, setIngresosMensuales] = useState<{ label: string; ingresos: number }[]>([])
  const [porUniverso, setPorUniverso] = useState<{ clave: string; valor: number }[]>([])
  const [porCategoria, setPorCategoria] = useState<{ clave: string; valor: number }[]>([])
  const [stockRadar, setStockRadar] = useState<Record<string, any>[]>([])
  const [duracion, setDuracion] = useState<{ horas: number; monto: number }[]>([])
  const [pedidosApilados, setPedidosApilados] = useState<Record<string, any>[]>([])
  const [masVendidos, setMasVendidos] = useState<{ codigo: string; nombre: string; cantidad: number }[]>([])
  const [bajoUmbral, setBajoUmbral] = useState(0)
  const [pendientesValidacion, setPendientesValidacion] = useState(0)
  const [pendientesAcceso, setPendientesAcceso] = useState(0)

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true)
      setError(null)
      try {
        const [
          metricas, pedidosResp, ranVend, ranMec, pagoDist, universoDist, categoriaDist,
          radar, atencion, masVend, stockResp, pendAcceso, ingresosMensualesResp,
        ] = await Promise.all([
          apiClient.get<Metricas>(`/v1/admin/metricas-negocio?desde=${desde}&hasta=${hasta}`),
          apiClient.get<{ pedidos: Pedido[]; total: number }>('/v1/pedidos'),
          apiClient.get<{ ranking: RankingItem[] }>(`/v1/analitica/rankings?tipo=vendedores&desde=${desde}&hasta=${hasta}&limit=3`),
          apiClient.get<{ ranking: RankingItem[] }>(`/v1/analitica/rankings?tipo=mecanicos&desde=${desde}&hasta=${hasta}&limit=3`),
          apiClient.get<{ distribucion: { clave: string; valor: number }[] }>('/v1/analitica/distribucion?por=estado_comprobante'),
          apiClient.get<{ distribucion: { clave: string; valor: number }[] }>(`/v1/analitica/distribucion?por=universo&desde=${desde}&hasta=${hasta}`),
          apiClient.get<{ distribucion: { clave: string; valor: number }[] }>(`/v1/analitica/distribucion?por=categoria&desde=${desde}&hasta=${hasta}`),
          apiClient.get<{ radar: Record<string, any>[] }>('/v1/analitica/stock-radar'),
          apiClient.get<{ puntos: { horas: number; monto: number }[] }>('/v1/analitica/duracion-atencion?limit=150'),
          apiClient.get<{ repuestos: { codigo: string; nombre: string; cantidad: number }[] }>('/v1/analitica/repuestos-mas-vendidos?limit=5'),
          apiClient.get<{ stocks: StockItem[] }>('/v1/stock'),
          apiClient.get<{ total: number }>('/v1/admin/usuarios/pendientes'),
          apiClient.get<{ serie: { label: string; ingresos: number }[] }>('/v1/analitica/ingresos-mensuales?meses=12'),
        ])
        if (!activo) return

        setIngresosTotales(metricas.comprobantes_emitidos_periodo)
        setTotalPedidos(pedidosResp.total)
        setTopVendedores(ranVend.ranking)
        setTopMecanicos(ranMec.ranking)
        setPagadoNoPagado(pagoDist.distribucion)
        setPendientesValidacion(pagoDist.distribucion.find(d => d.clave === 'NO_PAGADO')?.valor ?? 0)
        setPorUniverso(universoDist.distribucion)
        setPorCategoria(categoriaDist.distribucion)
        setStockRadar(radar.radar)
        setDuracion(atencion.puntos)
        setMasVendidos(masVend.repuestos)
        setBajoUmbral(stockResp.stocks.filter(s => s.esta_bajo_umbral).length)
        setPendientesAcceso(pendAcceso.total)
        setIngresosMensuales(ingresosMensualesResp.serie)

        const porMesEstado: Record<string, Record<string, number>> = {}
        for (const p of pedidosResp.pedidos) {
          const mes = p.created_at.slice(0, 7)
          porMesEstado[mes] = porMesEstado[mes] ?? {}
          porMesEstado[mes][p.estado] = (porMesEstado[mes][p.estado] ?? 0) + 1
        }
        const mesesOrdenados = Object.keys(porMesEstado).sort().slice(-6)
        setPedidosApilados(mesesOrdenados.map(mes => ({ mes, ...porMesEstado[mes] })))
      } catch (err) {
        if (activo) setError((err as ApiCallError).code)
      } finally {
        if (activo) setLoading(false)
      }
    }
    cargar()
    return () => { activo = false }
  }, [desde, hasta])

  if (loading) return <LoadingIndicator message="Cargando panel de administración..." />
  if (error) return <ErrorDisplay code={error} onRetry={() => location.reload()} />

  const stockNiveles = ['CRITICO', 'BAJO', 'OPTIMO']
  const estadosPedido = Array.from(new Set(pedidosApilados.flatMap(m => Object.keys(m).filter(k => k !== 'mes'))))

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-100">Panel de administración</h1>
          <p className="text-sm text-slate-400 font-body">Vista consolidada del negocio — filtro de período aplicado a todos los widgets.</p>
        </div>
        <div className="flex items-center gap-2">
          <input type="date" value={desde} onChange={e => setDesde(e.target.value)} className="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-200 font-mono" />
          <span className="text-slate-500 text-xs">→</span>
          <input type="date" value={hasta} onChange={e => setHasta(e.target.value)} className="bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-slate-200 font-mono" />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <StatCard label="Ingresos totales del período" value={`S/ ${ingresosTotales.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`} accent={CATEGORICAL[0]} />
        <StatCard label="Total de pedidos procesados" value={totalPedidos} accent={CATEGORICAL[1]} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <BarRankingHorizontal data={topVendedores} nameKey="nombre" dataKey="total" color={CATEGORICAL[0]} />
        <BarRankingHorizontal data={topMecanicos} nameKey="nombre" dataKey="total" color={CATEGORICAL[1]} />
      </div>
      <p className="text-[11px] text-slate-500 font-body -mt-4">Izquierda: top vendedores por ventas · derecha: top mecánicos por OTs completadas (monto por mano de obra)</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DonutChart data={pagadoNoPagado} colors={[CATEGORICAL[0], CATEGORICAL[3]]} />
        <MultiLineWidget data={ingresosMensuales} keys={['ingresos']} xKey="label" colors={[CATEGORICAL[0]]} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DonutChart data={porUniverso} />
        <BarVertical data={porCategoria} nameKey="clave" dataKey="valor" color={CATEGORICAL[2]} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {stockRadar.length > 0 ? (
          <RadarWidget data={stockRadar} keys={stockNiveles} colors={[CATEGORICAL[3], CATEGORICAL[2], CATEGORICAL[0]]} />
        ) : <TiltCard className="p-5 text-sm text-slate-500 font-body">Sin datos de stock aún.</TiltCard>}
        <ScatterWidget data={duracion} xKey="horas" yKey="monto" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <StackedBarWidget data={pedidosApilados} keys={estadosPedido} height={260} />
        <BarRankingHorizontal data={topVendedores} nameKey="nombre" dataKey="total" color={CATEGORICAL[4]} />
      </div>
      <p className="text-[11px] text-slate-500 font-body -mt-4">
        Comparación de ingresos por vendedor: se muestra el ranking del período (la serie mensual por vendedor requiere una agregación nueva, pendiente de sesión de backend dedicada).
      </p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <IconStatCard label="Repuestos más vendidos (top)" value={masVendidos[0]?.nombre ?? '—'} icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 7 12 3 4 7v10l8 4 8-4V7Z"/></svg>} />
        <IconStatCard label="Bajo umbral mínimo" value={bajoUmbral} icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v4m0 4h.01"/><circle cx="12" cy="12" r="10"/></svg>} />
        <IconStatCard label="Comprobantes por validar" value={pendientesValidacion} icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>} />
        <IconStatCard label="Accesos pendientes" value={pendientesAcceso} icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4"/><path d="M4 21v-1a8 8 0 0 1 16 0v1"/></svg>} />
      </div>
    </div>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import { CATEGORICAL } from '@/src/lib/chartColors'
import {
  StatCardLight, DonutChartLight, RadarWidgetLight, BarHorizontalLight, BarLineComboLight,
} from '@/src/components/dashboard/charts/PrimitivesLight'

interface PedidoItem { codigo: string; cantidad: number; precio_unitario: string; subtotal: string }
interface Pedido { pedido_id: string; estado: string; monto_total: string; monto_efectivo: string; items: PedidoItem[]; created_at: string }

const ESTADO_LABEL: Record<string, string> = {
  BORRADOR: 'Confirmado', CONFIRMADO: 'Confirmado', EN_PREPARACION: 'En preparación',
  DESPACHADO: 'Listo/despachado', ENTREGADO: 'Entregado', INCIDENCIA: 'Con incidencia', CANCELADO: 'Cancelado',
}

export default function RuralResumenTab() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [categorias, setCategorias] = useState<{ categoria: string; cantidad: number }[]>([])
  const [tiempoConfirmacion, setTiempoConfirmacion] = useState<number | null>(null)

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true)
      setError(null)
      try {
        const [pData, catData] = await Promise.all([
          apiClient.get<{ pedidos: Pedido[]; total: number }>('/v1/pedidos'),
          apiClient.get<{ distribucion: { categoria: string; cantidad: number }[] }>('/v1/analitica/mis-categorias'),
        ])
        if (!activo) return
        setPedidos(pData.pedidos ?? [])
        setCategorias(catData.distribucion ?? [])

        const conEventos = (pData.pedidos ?? []).slice(0, 15)
        const horas: number[] = []
        for (const p of conEventos) {
          try {
            const ev = await apiClient.get<{ eventos: { evento: string; timestamp: string }[] }>(`/v1/pedidos/${p.pedido_id}/eventos`)
            const confirmacion = ev.eventos?.find(e => e.evento.includes('CONFIRMAR'))
            const creado = ev.eventos?.find(e => e.evento.includes('CREADO'))
            if (confirmacion && creado) {
              horas.push((new Date(confirmacion.timestamp).getTime() - new Date(creado.timestamp).getTime()) / 3_600_000)
            }
          } catch { /* pedido sin eventos aún — se omite del promedio */ }
        }
        if (activo && horas.length > 0) setTiempoConfirmacion(horas.reduce((a, b) => a + b, 0) / horas.length)
      } catch (err) {
        if (activo) setError((err as ApiCallError).code)
      } finally {
        if (activo) setLoading(false)
      }
    }
    cargar()
    return () => { activo = false }
  }, [])

  if (loading) return <LoadingIndicator message="Cargando tu resumen..." />
  if (error) return <ErrorDisplay code={error} onRetry={() => location.reload()} />
  if (pedidos.length === 0) {
    return <EmptyState title="Todavía no tienes pedidos" description="Cuando hagas tu primer pedido, aquí verás tu historial y estado en tiempo real." />
  }

  const activo = [...pedidos].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]
  const gastoAcumulado = pedidos.reduce((s, p) => s + Number(p.monto_efectivo), 0)
  const repuestosReservados = pedidos.reduce((s, p) => s + p.items.reduce((s2, i) => s2 + i.cantidad, 0), 0)

  const porMes: Record<string, { cantidad: number; gasto: number }> = {}
  for (const p of pedidos) {
    const mes = p.created_at.slice(0, 7)
    porMes[mes] = porMes[mes] ?? { cantidad: 0, gasto: 0 }
    porMes[mes].cantidad += 1
    porMes[mes].gasto += Number(p.monto_efectivo)
  }
  const historial = Object.entries(porMes).sort(([a], [b]) => a.localeCompare(b)).map(([periodo, v]) => ({ periodo, ...v }))

  const conteoEstados: Record<string, number> = {}
  for (const p of pedidos) conteoEstados[p.estado] = (conteoEstados[p.estado] ?? 0) + 1

  const conteoRepuestos: Record<string, number> = {}
  for (const p of pedidos) for (const i of p.items) conteoRepuestos[i.codigo] = (conteoRepuestos[i.codigo] ?? 0) + i.cantidad
  const masReservados = Object.entries(conteoRepuestos).sort(([, a], [, b]) => b - a).slice(0, 5).map(([clave, valor]) => ({ clave, valor }))

  const radarData = categorias.length > 0 ? [Object.fromEntries([['categoria', 'Mis compras'], ...categorias.map(c => [c.categoria, c.cantidad])])] : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-800">Mi resumen</h1>
        <p className="text-sm text-slate-500 font-body">Seguimiento de tu pedido activo y tu historial de compras.</p>
      </div>

      {/* Grid superior: pedido activo */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCardLight label="Repuesto" value={activo.items[0]?.codigo ?? '—'} sublabel={activo.items.length > 1 ? `+${activo.items.length - 1} más` : undefined} accent={CATEGORICAL[0]} />
        <StatCardLight label="Estado de reserva" value={ESTADO_LABEL[activo.estado] ?? activo.estado} accent={CATEGORICAL[1]} />
        <StatCardLight label="Método" value="Envío a distrito" accent={CATEGORICAL[2]} />
        <StatCardLight label="Última actividad" value={new Date(activo.created_at).toLocaleDateString('es-PE')} accent={CATEGORICAL[4]} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <p className="text-sm font-semibold text-slate-700 font-body mb-2">Historial de mis pedidos (cantidad y gasto)</p>
          <BarLineComboLight data={historial} barKey="cantidad" lineKey="gasto" xKey="periodo" />
        </div>
        <DonutChartLight data={Object.entries(conteoEstados).map(([clave, valor]) => ({ clave: ESTADO_LABEL[clave] ?? clave, valor }))} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCardLight label="Pedidos totales" value={pedidos.length} accent={CATEGORICAL[0]} />
        <StatCardLight label="Gasto acumulado" value={`S/ ${gastoAcumulado.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`} accent={CATEGORICAL[1]} />
        <StatCardLight label="Repuestos reservados" value={repuestosReservados} accent={CATEGORICAL[2]} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {radarData.length > 0 ? (
          <RadarWidgetLight data={radarData} keys={categorias.map(c => c.categoria)} />
        ) : (
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500 font-body">
            Aún no hay categorías registradas en tus compras.
          </div>
        )}
        <div className="space-y-4">
          <div>
            <p className="text-xs text-slate-500 font-body mb-1">Tiempo promedio hasta confirmación</p>
            <p className="text-2xl font-mono font-bold text-slate-800">
              {tiempoConfirmacion === null ? '—' : `${tiempoConfirmacion.toFixed(1)} h`}
            </p>
          </div>
          <BarHorizontalLight data={masReservados} />
        </div>
      </div>
    </div>
  )
}

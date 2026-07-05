'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import { CATEGORICAL, STATUS } from '@/src/lib/chartColors'
import { GaugeRadialLight, MultiLineWidgetLight, TiltCardLight } from '@/src/components/dashboard/charts/PrimitivesLight'

interface PedidoItem { codigo: string; cantidad: number; subtotal: string }
interface Pedido { pedido_id: string; estado: string; monto_efectivo: string; items: PedidoItem[]; created_at: string }
interface RepuestoDetalle { nombre: string; imagen_url: string | null; codigo: string }

export default function ConductorResumenTab({ tituloExtra }: { tituloExtra?: string }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [rangoDias, setRangoDias] = useState(30)
  const [destacado, setDestacado] = useState<RepuestoDetalle | null>(null)

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true)
      setError(null)
      try {
        const pData = await apiClient.get<{ pedidos: Pedido[]; total: number }>('/v1/pedidos')
        if (!activo) return
        const lista = pData.pedidos ?? []
        setPedidos(lista)
        const masReciente = [...lista].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]
        const codigo = masReciente?.items[0]?.codigo
        if (codigo) {
          try {
            const rep = await apiClient.get<RepuestoDetalle>(`/v1/repuestos/${codigo}`)
            if (activo) setDestacado(rep)
          } catch { /* repuesto puede haber sido dado de baja — se omite imagen */ }
        }
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
    return <EmptyState title="Todavía no tienes pedidos" description="Cuando hagas tu primer pedido, aquí verás tu seguimiento." />
  }

  const desde = new Date()
  desde.setDate(desde.getDate() - rangoDias)
  const enRango = pedidos.filter(p => new Date(p.created_at) >= desde)
  const pedidosRango = enRango.length
  const gastoRango = enRango.reduce((s, p) => s + Number(p.monto_efectivo), 0)
  const devolucionesRango = enRango.filter(p => p.estado === 'INCIDENCIA').length

  const porDia: Record<string, { pedidos: number; gasto: number }> = {}
  for (const p of enRango) {
    const key = p.created_at.slice(0, 10)
    porDia[key] = porDia[key] ?? { pedidos: 0, gasto: 0 }
    porDia[key].pedidos += 1
    porDia[key].gasto += Number(p.monto_efectivo)
  }
  const serie = Object.entries(porDia).sort(([a], [b]) => a.localeCompare(b)).map(([fecha, v]) => ({ fecha, ...v }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-800">{tituloExtra ?? 'Mi seguimiento'}</h1>
      </div>

      <TiltCardLight className="p-5 flex items-center gap-4">
        <div className="w-20 h-20 rounded-lg bg-slate-100 overflow-hidden shrink-0 flex items-center justify-center">
          {destacado?.imagen_url ? (
            <Image src={destacado.imagen_url} alt={destacado.nombre} width={80} height={80} className="object-cover w-full h-full" />
          ) : (
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="1.5"><path d="M20 7 12 3 4 7v10l8 4 8-4V7Z"/></svg>
          )}
        </div>
        <div>
          <p className="text-xs text-slate-500 font-body uppercase tracking-wide">Repuesto en seguimiento</p>
          <p className="text-lg font-display font-semibold text-slate-800">{destacado?.nombre ?? pedidos[0]?.items[0]?.codigo ?? '—'}</p>
        </div>
      </TiltCardLight>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <GaugeRadialLight porcentaje={Math.min(100, pedidosRango * 10)} label={`Pedidos (${pedidosRango}) en el rango`} color={CATEGORICAL[0]} />
        <TiltCardLight className="p-5 flex flex-col items-center justify-center">
          <p className="text-xs text-slate-500 font-body uppercase mb-2">Gasto en el rango</p>
          <p className="text-2xl font-mono font-extrabold text-slate-800">S/ {gastoRango.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</p>
        </TiltCardLight>
        <GaugeRadialLight porcentaje={enRango.length > 0 ? Math.round(devolucionesRango / enRango.length * 100) : 0} label="Devoluciones/reclamos" color={STATUS.critical} />
      </div>

      <div className="flex items-center gap-3">
        <label className="text-xs text-slate-500 font-body">Rango:</label>
        {[7, 30, 90].map(n => (
          <button
            key={n}
            onClick={() => setRangoDias(n)}
            className={`px-3 py-1 rounded-full text-xs font-body border ${rangoDias === n ? 'bg-teal border-teal text-white' : 'border-slate-300 text-slate-600 hover:bg-slate-100'}`}
          >
            {n} días
          </button>
        ))}
      </div>

      <MultiLineWidgetLight data={serie} keys={['pedidos', 'gasto']} colors={[CATEGORICAL[0], CATEGORICAL[1]]} />
    </div>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import { STATUS } from '@/src/lib/chartColors'
import { StatCard, DonutChart, StackedBarWidget, MiniSparkline } from '@/src/components/dashboard/charts/Primitives'

interface Pedido { pedido_id: string; estado: string; created_at: string }
interface Comprobante { estado: string }

const ESTADO_LABEL: Record<string, string> = {
  BORRADOR: 'Borrador', CONFIRMADO: 'Confirmado', EN_PREPARACION: 'En preparación',
  DESPACHADO: 'Despachado', ENTREGADO: 'Entregado', INCIDENCIA: 'Incidencia', CANCELADO: 'Cancelado',
}
const COLOR_TARJETA = { rosa: '#E11D48', naranja: '#D97706', roja: '#DC2626', azul: '#0284C7', verde: '#16A34A' }

function inicioMes(offsetMeses = 0): Date {
  const d = new Date()
  d.setMonth(d.getMonth() - offsetMeses, 1)
  d.setHours(0, 0, 0, 0)
  return d
}

export default function VendedorResumenTab() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [comprobantes, setComprobantes] = useState<Comprobante[]>([])

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true)
      setError(null)
      try {
        const [pData, cData] = await Promise.all([
          apiClient.get<{ pedidos: Pedido[]; total: number }>('/v1/pedidos?mios=true'),
          apiClient.get<{ comprobantes: Comprobante[]; total: number }>('/v1/pedidos/comprobantes/mios'),
        ])
        if (!activo) return
        setPedidos(pData.pedidos ?? [])
        setComprobantes(cData.comprobantes ?? [])
      } catch (err) {
        if (activo) setError((err as ApiCallError).code)
      } finally {
        if (activo) setLoading(false)
      }
    }
    cargar()
    return () => { activo = false }
  }, [])

  if (loading) return <LoadingIndicator message="Cargando tu actividad..." />
  if (error) return <ErrorDisplay code={error} onRetry={() => location.reload()} />

  const esteMes = inicioMes(0)
  const mesAnterior = inicioMes(1)
  const registradosEsteMes = pedidos.filter(p => new Date(p.created_at) >= esteMes).length
  const registradosMesAnterior = pedidos.filter(p => { const d = new Date(p.created_at); return d >= mesAnterior && d < esteMes }).length
  const variacion = registradosMesAnterior > 0 ? Math.round((registradosEsteMes - registradosMesAnterior) / registradosMesAnterior * 100) : null

  const conIncidencia = pedidos.filter(p => p.estado === 'INCIDENCIA').length
  const cancelados = pedidos.filter(p => p.estado === 'CANCELADO').length
  const pendientesAprobacion = comprobantes.filter(c => c.estado === 'PENDIENTE_VALIDACION').length
  const entregados = pedidos.filter(p => p.estado === 'ENTREGADO').length

  const conteoEstados: Record<string, number> = {}
  for (const p of pedidos) conteoEstados[p.estado] = (conteoEstados[p.estado] ?? 0) + 1

  const porMes: Record<string, { registrados: number; entregados: number }> = {}
  for (const p of pedidos) {
    const mes = p.created_at.slice(0, 7)
    porMes[mes] = porMes[mes] ?? { registrados: 0, entregados: 0 }
    porMes[mes].registrados += 1
    if (p.estado === 'ENTREGADO') porMes[mes].entregados += 1
  }
  const comparativa = Object.entries(porMes).sort(([a], [b]) => a.localeCompare(b)).slice(-6).map(([mes, v]) => ({ mes, ...v }))

  const hace30 = new Date()
  hace30.setDate(hace30.getDate() - 29)
  const porDia: Record<string, number> = {}
  for (let i = 0; i < 30; i++) {
    const d = new Date(hace30)
    d.setDate(d.getDate() + i)
    porDia[d.toISOString().slice(0, 10)] = 0
  }
  for (const p of pedidos) {
    const key = p.created_at.slice(0, 10)
    if (key in porDia) porDia[key] += 1
  }
  const tendencia = Object.entries(porDia).map(([fecha, valor]) => ({ fecha, valor }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-100">Mi actividad</h1>
        <p className="text-sm text-slate-400 font-body">Nunca incluye precio de costo ni margen — solo precio de venta.</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <StatCard label="Registrados este mes" value={registradosEsteMes} sublabel={variacion === null ? undefined : `${variacion > 0 ? '+' : ''}${variacion}% vs. mes anterior`} accent={COLOR_TARJETA.rosa} />
        <StatCard label="Con incidencia" value={conIncidencia} sublabel="proxy de reprogramado — sin estado dedicado" accent={COLOR_TARJETA.naranja} />
        <StatCard label="No concretados/cancelados" value={cancelados} accent={COLOR_TARJETA.roja} />
        <StatCard label="Pendientes de aprobación" value={pendientesAprobacion} accent={COLOR_TARJETA.azul} />
        <StatCard label="Completados/entregados" value={entregados} accent={COLOR_TARJETA.verde} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <DonutChart data={Object.entries(conteoEstados).map(([clave, valor]) => ({ clave: ESTADO_LABEL[clave] ?? clave, valor }))} />
        <div className="lg:col-span-2">
          <StackedBarWidget data={comparativa} keys={['registrados', 'entregados']} height={240} />
        </div>
      </div>

      <div>
        <p className="text-sm font-semibold text-slate-300 font-body mb-2">Mi actividad de registro · últimos 30 días</p>
        <div className="rounded-xl border border-slate-700/80 bg-gradient-to-br from-slate-800 to-slate-900 p-5">
          <MiniSparkline data={tendencia} color={COLOR_TARJETA.rosa} />
        </div>
      </div>
    </div>
  )
}

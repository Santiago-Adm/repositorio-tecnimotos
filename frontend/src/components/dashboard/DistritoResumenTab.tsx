'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import { CATEGORICAL, STATUS } from '@/src/lib/chartColors'
import { GaugeRadialLight, MultiLineWidgetLight, TiltCardLight } from '@/src/components/dashboard/charts/PrimitivesLight'

interface PedidoItem { codigo: string; cantidad: number; subtotal: string }
interface Pedido { pedido_id: string; estado: string; monto_efectivo: string; items: PedidoItem[]; created_at: string }
interface ListaItem { codigo: string; cantidad: number; precio_referencia: string }
interface Lista { lista_id: string; nombre: string | null; estado: string; total_items: number; ultima_actividad: string; items: ListaItem[] }

/**
 * Referencia 6 adaptada a DISTRITO (decisión de Sant, sesión dashboards):
 * DISTRITO opera por lista de reserva progresiva — "paquetes repetitivos"
 * de repuestos, no por un repuesto único — así que el bloque destacado de
 * Referencia 6 (una sola imagen de producto) se reemplaza por la lista de
 * reserva activa completa (ADR de dominio ya existente, 02 §2.2).
 */
export default function DistritoResumenTab() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [listas, setListas] = useState<Lista[]>([])
  const [rangoDias, setRangoDias] = useState(30)

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true)
      setError(null)
      try {
        const [pData, lData] = await Promise.all([
          apiClient.get<{ pedidos: Pedido[]; total: number }>('/v1/pedidos'),
          apiClient.get<{ listas: Lista[]; total: number }>('/v1/lista-reserva-progresiva/mias'),
        ])
        if (!activo) return
        setPedidos(pData.pedidos ?? [])
        setListas(lData.listas ?? [])
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

  const listaActiva = listas.find(l => l.estado === 'BORRADOR') ?? listas[0] ?? null

  const desde = new Date()
  desde.setDate(desde.getDate() - rangoDias)
  const enRango = pedidos.filter(p => new Date(p.created_at) >= desde)
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
        <h1 className="font-display text-2xl font-bold text-slate-800">Mi resumen — Distrito</h1>
        <p className="text-sm text-slate-500 font-body">Control por lista y envío en paquetes repetitivos, no por repuesto único.</p>
      </div>

      <TiltCardLight className="p-5">
        <p className="text-xs text-slate-500 font-body uppercase tracking-wide mb-2">Lista de reserva activa</p>
        {listaActiva ? (
          <>
            <p className="text-lg font-display font-semibold text-slate-800 mb-2">
              {listaActiva.nombre ?? 'Sin nombre'} · {listaActiva.total_items} repuestos
            </p>
            <div className="flex flex-wrap gap-2">
              {listaActiva.items.slice(0, 8).map((it, i) => (
                <span key={i} className="text-xs font-mono px-2 py-1 rounded-full bg-slate-100 text-slate-600">
                  {it.codigo} × {it.cantidad}
                </span>
              ))}
              {listaActiva.items.length > 8 && (
                <span className="text-xs font-body px-2 py-1 text-slate-400">+{listaActiva.items.length - 8} más</span>
              )}
            </div>
          </>
        ) : (
          <p className="text-sm text-slate-500 font-body">Sin lista de reserva en curso. Créala desde &quot;Mi lista activa&quot;.</p>
        )}
      </TiltCardLight>

      {pedidos.length === 0 ? (
        <EmptyState title="Todavía no tienes pedidos formalizados" description="Cuando formalices tu lista, aquí verás tu seguimiento." />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <GaugeRadialLight porcentaje={Math.min(100, enRango.length * 10)} label={`Pedidos (${enRango.length}) en el rango`} color={CATEGORICAL[0]} />
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
        </>
      )}
    </div>
  )
}

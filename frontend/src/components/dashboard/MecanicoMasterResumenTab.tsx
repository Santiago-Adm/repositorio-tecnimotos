'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import { CATEGORICAL } from '@/src/lib/chartColors'
import { StatCard, DonutChart, BarVertical } from '@/src/components/dashboard/charts/Primitives'

interface OrdenTrabajo {
  ot_id: string
  estado: string
  costo_mano_obra: string | null
  cliente_aprobo_lista: boolean
  created_at: string
}

const ESTADOS_EN_PROGRESO = new Set(['ABIERTA', 'LISTA_REPUESTOS', 'EN_EJECUCION'])

function inicioSemanaISO(): Date {
  const d = new Date()
  const dia = d.getDay() === 0 ? 7 : d.getDay()
  d.setDate(d.getDate() - (dia - 1))
  d.setHours(0, 0, 0, 0)
  return d
}
function inicioMes(): Date {
  const d = new Date()
  d.setDate(1)
  d.setHours(0, 0, 0, 0)
  return d
}

/**
 * Referencia 2 (mismo layout de MECANICO_JUNIOR), adaptado a supervisión de
 * MECANICO_MASTER: OTs del equipo (master+junior), aprobaciones de lista
 * pendientes (en vez de repuestos consumidos), ingresos por mano de obra
 * (en vez de cantidad) — decisión confirmada por Sant, sesión dashboards.
 */
export default function MecanicoMasterResumenTab({ ordenes }: { ordenes: OrdenTrabajo[] }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [porUniverso, setPorUniverso] = useState<{ clave: string; valor: number }[]>([])

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true)
      setError(null)
      try {
        const universo = await apiClient.get<{ distribucion: { clave: string; valor: number }[] }>('/v1/analitica/mecanico/ots-por-universo')
        if (!activo) return
        setPorUniverso(universo.distribucion)
      } catch (err) {
        if (activo) setError((err as ApiCallError).code)
      } finally {
        if (activo) setLoading(false)
      }
    }
    cargar()
    return () => { activo = false }
  }, [])

  if (loading) return <LoadingIndicator message="Cargando resumen..." />
  if (error) return <ErrorDisplay code={error} onRetry={() => location.reload()} />

  const inicioSemana = inicioSemanaISO()
  const inicio = inicioMes()
  const otsEstaSemana = ordenes.filter(o => new Date(o.created_at) >= inicioSemana).length
  const aprobacionesPendientes = ordenes.filter(o => !o.cliente_aprobo_lista && o.estado !== 'CERRADA' && o.estado !== 'CANCELADA').length
  const ingresosManoObra = ordenes
    .filter(o => o.costo_mano_obra && new Date(o.created_at) >= inicio)
    .reduce((s, o) => s + Number(o.costo_mano_obra), 0)

  const completadas = ordenes.filter(o => o.estado === 'CERRADA').length
  const enProgreso = ordenes.filter(o => ESTADOS_EN_PROGRESO.has(o.estado)).length
  const revisionAprobada = completadas
  const revisionPendiente = ordenes.filter(o => o.estado === 'REVISION_FINAL').length

  return (
    <section className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="OTs de mi equipo esta semana" value={otsEstaSemana} accent={CATEGORICAL[0]} />
        <StatCard label="Aprobaciones de lista pendientes" value={aprobacionesPendientes} accent={CATEGORICAL[3]} />
        <StatCard label="Ingresos por mano de obra · este mes" value={`S/ ${ingresosManoObra.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`} accent={CATEGORICAL[1]} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <DonutChart data={[{ clave: 'Completadas', valor: completadas }, { clave: 'En progreso', valor: enProgreso }]} />
        <DonutChart data={[{ clave: 'Aprobada', valor: revisionAprobada }, { clave: 'Pendiente', valor: revisionPendiente }]} colors={[CATEGORICAL[0], CATEGORICAL[3]]} />
        <BarVertical data={porUniverso} nameKey="clave" dataKey="valor" color={CATEGORICAL[4]} height={208} />
      </div>
    </section>
  )
}

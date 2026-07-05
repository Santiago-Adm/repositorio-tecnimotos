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

export default function MecanicoJuniorResumenTab({ ordenes }: { ordenes: OrdenTrabajo[] }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [repuestosConsumidos, setRepuestosConsumidos] = useState(0)
  const [porUniverso, setPorUniverso] = useState<{ clave: string; valor: number }[]>([])

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true)
      setError(null)
      try {
        const [consumidos, universo] = await Promise.all([
          apiClient.get<{ cantidad: number }>('/v1/analitica/mecanico/repuestos-consumidos'),
          apiClient.get<{ distribucion: { clave: string; valor: number }[] }>('/v1/analitica/mecanico/ots-por-universo'),
        ])
        if (!activo) return
        setRepuestosConsumidos(consumidos.cantidad)
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
  const otsEstaSemana = ordenes.filter(o => new Date(o.created_at) >= inicioSemana).length
  const completadas = ordenes.filter(o => o.estado === 'CERRADA').length
  const enProgreso = ordenes.filter(o => ESTADOS_EN_PROGRESO.has(o.estado)).length
  const revisionAprobada = ordenes.filter(o => o.estado === 'CERRADA').length
  const revisionPendiente = ordenes.filter(o => o.estado === 'REVISION_FINAL').length

  return (
    <section className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="OTs asignadas esta semana" value={otsEstaSemana} accent={CATEGORICAL[0]} />
        <StatCard label="Repuestos consumidos este mes" value={repuestosConsumidos} sublabel="cantidad, no monto" accent={CATEGORICAL[1]} />
        <StatCard label="Horas registradas en OTs" value="—" sublabel="sin registro de horas en el sistema todavía" accent={CATEGORICAL[2]} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <DonutChart data={[{ clave: 'Completadas', valor: completadas }, { clave: 'En progreso', valor: enProgreso }]} />
        <DonutChart data={[{ clave: 'Aprobada', valor: revisionAprobada }, { clave: 'Pendiente', valor: revisionPendiente }]} colors={[CATEGORICAL[0], CATEGORICAL[3]]} />
        <BarVertical data={porUniverso} nameKey="clave" dataKey="valor" color={CATEGORICAL[4]} height={208} />
      </div>
    </section>
  )
}

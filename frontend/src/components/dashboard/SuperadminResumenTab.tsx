'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import { CATEGORICAL, STATUS } from '@/src/lib/chartColors'
import {
  StatCard, IconStatCard, MiniSparkline, GaugeRadial, DonutChart,
  BarVertical, TiltCard,
} from '@/src/components/dashboard/charts/Primitives'

interface Serie { serie: { fecha: string; valor: number }[] }
interface Metricas {
  comprobantes_emitidos_periodo: number
  ots_activas: number
}

function hoyISO() { return new Date().toISOString().slice(0, 10) }
function haceNDias(n: number) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

export default function SuperadminResumenTab() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [ventasHoy, setVentasHoy] = useState(0)
  const [crecimiento, setCrecimiento] = useState<number | null>(null)
  const [totalUsuarios, setTotalUsuarios] = useState(0)
  const [ingresosPeriodo, setIngresosPeriodo] = useState(0)
  const [otATiempo, setOtATiempo] = useState<number | null>(null)
  const [serieVentas7d, setSerieVentas7d] = useState<Serie['serie']>([])
  const [serieIngresos7d, setSerieIngresos7d] = useState<Serie['serie']>([])
  const [serieClientes7d, setSerieClientes7d] = useState<Serie['serie']>([])
  const [repuestosMasVendidos, setRepuestosMasVendidos] = useState<{ codigo: string; nombre: string; cantidad: number }[]>([])
  const [reservasTotales, setReservasTotales] = useState(0)
  const [pendientesAcceso, setPendientesAcceso] = useState(0)
  const [incidentesAbiertos, setIncidentesAbiertos] = useState(0)
  const [pedidosPorDia, setPedidosPorDia] = useState<{ clave: string; valor: number }[]>([])
  const [distritos, setDistritos] = useState<{ clave: string; valor: number }[]>([])

  useEffect(() => {
    let activo = true
    async function cargar() {
      setLoading(true)
      setError(null)
      try {
        const hoy = hoyISO()
        const [
          metricasHoy, metricasAyer, usuarios, otTiempo,
          sVentas, sIngresos, sClientes, masVendidos, reservas,
          pendientes, incidentes, porDia, distrito,
        ] = await Promise.all([
          apiClient.get<Metricas>(`/v1/admin/metricas-negocio?desde=${hoy}&hasta=${hoy}`),
          apiClient.get<Metricas>(`/v1/admin/metricas-negocio?desde=${haceNDias(1)}&hasta=${haceNDias(1)}`),
          apiClient.get<{ total: number }>('/v1/admin/usuarios'),
          apiClient.get<{ porcentaje: number | null }>('/v1/analitica/ot-a-tiempo'),
          apiClient.get<Serie>('/v1/analitica/series?metrica=ventas&dias=7'),
          apiClient.get<Serie>('/v1/analitica/series?metrica=ingresos&dias=7'),
          apiClient.get<Serie>('/v1/analitica/series?metrica=clientes_nuevos&dias=7'),
          apiClient.get<{ repuestos: { codigo: string; nombre: string; cantidad: number }[] }>('/v1/analitica/repuestos-mas-vendidos?limit=5'),
          apiClient.get<{ total: number }>('/v1/analitica/reservas-totales'),
          apiClient.get<{ total: number }>('/v1/admin/usuarios/pendientes'),
          apiClient.get<{ total: number }>('/v1/admin/incidentes?estado=ABIERTO'),
          apiClient.get<{ distribucion: { clave: string; valor: number }[] }>('/v1/analitica/distribucion?por=dia_semana'),
          apiClient.get<{ distribucion: { clave: string; valor: number }[] }>('/v1/analitica/distribucion?por=distrito'),
        ])
        if (!activo) return
        setVentasHoy(metricasHoy.comprobantes_emitidos_periodo)
        const ayer = metricasAyer.comprobantes_emitidos_periodo
        setCrecimiento(ayer > 0 ? Math.round((metricasHoy.comprobantes_emitidos_periodo - ayer) / ayer * 1000) / 10 : null)
        setTotalUsuarios(usuarios.total)
        setIngresosPeriodo(metricasHoy.comprobantes_emitidos_periodo)
        setOtATiempo(otTiempo.porcentaje)
        setSerieVentas7d(sVentas.serie)
        setSerieIngresos7d(sIngresos.serie)
        setSerieClientes7d(sClientes.serie)
        setRepuestosMasVendidos(masVendidos.repuestos)
        setReservasTotales(reservas.total)
        setPendientesAcceso(pendientes.total)
        setIncidentesAbiertos(incidentes.total)
        setPedidosPorDia(porDia.distribucion)
        setDistritos(distrito.distribucion)
      } catch (err) {
        if (activo) setError((err as ApiCallError).code)
      } finally {
        if (activo) setLoading(false)
      }
    }
    cargar()
    return () => { activo = false }
  }, [])

  if (loading) return <LoadingIndicator message="Cargando panel general..." />
  if (error) return <ErrorDisplay code={error} onRetry={() => location.reload()} />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-100">Panel general</h1>
        <p className="text-sm text-slate-400 font-body">Vista consolidada de negocio, operación y acceso — datos en vivo.</p>
      </div>

      {/* 2 KPIs con barra de progreso implícita (valor + variación) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <StatCard label="Ventas de hoy" value={`S/ ${ventasHoy.toLocaleString('es-PE', { minimumFractionDigits: 2 })}`} accent={CATEGORICAL[0]} />
        <StatCard
          label="Crecimiento vs. ayer"
          value={crecimiento === null ? '—' : `${crecimiento > 0 ? '+' : ''}${crecimiento}%`}
          accent={crecimiento !== null && crecimiento < 0 ? STATUS.critical : STATUS.good}
        />
      </div>

      {/* 2 tarjetas grandes + mini-línea de tendencia */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TiltCard className="p-5">
          <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">Usuarios activos (11 roles)</p>
          <p className="text-3xl font-mono font-extrabold text-slate-100 mb-2">{totalUsuarios}</p>
          <MiniSparkline data={serieClientes7d} color={CATEGORICAL[1]} />
        </TiltCard>
        <TiltCard className="p-5">
          <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">Ingresos del período</p>
          <p className="text-3xl font-mono font-extrabold text-teal mb-2">S/ {ingresosPeriodo.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</p>
          <MiniSparkline data={serieIngresos7d} color={CATEGORICAL[0]} />
        </TiltCard>
      </div>

      {/* Gauge + 4 tarjetas compactas 7 días */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GaugeRadial porcentaje={otATiempo} label="OTs resueltas a tiempo" />
        <div className="md:col-span-2 grid grid-cols-2 gap-3">
          <TiltCard className="p-4">
            <p className="text-[11px] text-slate-400 font-body uppercase mb-1">Ventas · 7 días</p>
            <MiniSparkline data={serieVentas7d} color={CATEGORICAL[0]} />
          </TiltCard>
          <TiltCard className="p-4">
            <p className="text-[11px] text-slate-400 font-body uppercase mb-1">Ingresos · 7 días</p>
            <MiniSparkline data={serieIngresos7d} color={CATEGORICAL[1]} />
          </TiltCard>
          <TiltCard className="p-4">
            <p className="text-[11px] text-slate-400 font-body uppercase mb-1">Clientes nuevos · 7 días</p>
            <MiniSparkline data={serieClientes7d} color={CATEGORICAL[2]} />
          </TiltCard>
          <TiltCard className="p-4">
            <p className="text-[11px] text-slate-400 font-body uppercase mb-1">Cuentas activas</p>
            <p className="text-xl font-mono font-bold text-slate-200 mt-2">{totalUsuarios}</p>
            <p className="text-[10px] text-slate-500 font-body">tendencia diaria pendiente de histórico</p>
          </TiltCard>
        </div>
      </div>

      {/* 4 tarjetas ícono+número */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <IconStatCard
          label="Repuesto más vendido"
          value={repuestosMasVendidos[0]?.nombre ?? '—'}
          icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 7 12 3 4 7v10l8 4 8-4V7Z"/><path d="M12 12 4 7m8 5 8-5m-8 5v9"/></svg>}
        />
        <IconStatCard
          label="Reservas totales"
          value={reservasTotales}
          icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>}
        />
        <IconStatCard
          label="Accesos pendientes"
          value={pendientesAcceso}
          icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4"/><path d="M4 21v-1a8 8 0 0 1 16 0v1"/></svg>}
        />
        <IconStatCard
          label="Incidentes abiertos"
          value={incidentesAbiertos}
          icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>}
        />
      </div>

      {/* Barras pedidos por día de semana + distribución geográfica */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <p className="text-sm font-semibold text-slate-300 font-body mb-2">Pedidos por día de semana · últimas 4 semanas</p>
          <BarVertical data={pedidosPorDia} nameKey="clave" dataKey="valor" color={CATEGORICAL[0]} />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-300 font-body mb-2">Pedidos despachados por distrito</p>
          {distritos.length === 0 ? (
            <TiltCard className="p-5 text-xs text-slate-500 font-body">
              Sin envíos con distrito registrado todavía (ADR-018) — se completa a medida que VENDEDOR registra envíos nuevos.
            </TiltCard>
          ) : (
            <DonutChart data={distritos} />
          )}
        </div>
      </div>
    </div>
  )
}

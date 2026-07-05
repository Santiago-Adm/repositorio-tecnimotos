'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import MecanicoJuniorResumenTab from '@/src/components/dashboard/MecanicoJuniorResumenTab'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'
import AppSidebarNav from '@/src/components/dashboard/AppSidebarNav'

interface OrdenTrabajo {
  ot_id: string
  estado: string
  vehiculo_id: string
  modalidad: string
  urgencia: string
  monto_estimado: string
  created_at: string
}

const ESTADO_BADGE: Record<string, string> = {
  ABIERTA: 'bg-teal/20 text-teal',
  LISTA_REPUESTOS: 'bg-electric/20 text-electric',
  EN_EJECUCION: 'bg-electric/20 text-electric',
  REVISION_FINAL: 'bg-teal/20 text-teal',
  CERRADA: 'bg-slate-700 text-slate-400',
  CANCELADA: 'bg-red-900/30 text-red-400',
}

export default function MecanicoJuniorDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [ordenes, setOrdenes] = useState<OrdenTrabajo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // EP-TAL-14 — solo las OTs asignadas a este junior (10 §4.7: filtro en el
  // backend, no en el cliente; sin filtro "activa" — ve todas sus asignadas).
  // El backend resuelve el mecanico_id real a partir del usuario autenticado
  // (tabla `mecanico`, distinta de `usuario`) — no se envía como parámetro.
  async function fetchOrdenes() {
    if (!user) return
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.get<{ ordenes_trabajo: OrdenTrabajo[]; total: number }>(
        '/v1/ordenes-trabajo',
      )
      setOrdenes(data.ordenes_trabajo ?? [])
    } catch (err) {
      setError((err as ApiCallError).code)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user && user.rol !== 'MECANICO_JUNIOR') { router.replace('/login'); return }
    if (user) fetchOrdenes()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, router])

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="MECANICO_JUNIOR" />
      <DashboardHeader userId={user.id} rol="MECANICO_JUNIOR" onLogout={logout} />

      <div className="flex flex-col md:flex-row">
        {/* Navegación — solo taller (02 §4.1 MECANICO_JUNIOR). Sin "declarar
            listo" ni "autorizar precio" — componente no existe (10 §4.7). */}
        <AppSidebarNav secciones={['Mis OTs']} activa="Mis OTs" onSeleccionar={() => {}} />

        {/* Vista por defecto: OTs asignadas a este junior (10 §4.7) */}
        <main className="flex-1 min-w-0 p-4 md:p-6 space-y-6">
          {!loading && !error && <MecanicoJuniorResumenTab ordenes={ordenes} />}

          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg font-semibold text-slate-100">Mis órdenes</h2>
              <button onClick={fetchOrdenes} className="text-xs text-teal font-body hover:underline">Actualizar</button>
            </div>

            {loading ? (
              <LoadingIndicator message="Cargando tus órdenes..." />
            ) : error ? (
              <ErrorDisplay code={error} onRetry={fetchOrdenes} />
            ) : ordenes.length === 0 ? (
              <EmptyState
                title="Sin órdenes asignadas"
                description="El mecánico master aún no te delegó ninguna orden de trabajo."
              />
            ) : (
              <div className="space-y-3">
                {ordenes.map(ot => (
                  <div
                    key={ot.ot_id}
                    className="rounded-xl bg-slate-800 border border-slate-700 p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-mono text-slate-200 truncate max-w-[220px]">{ot.ot_id}</p>
                        <p className="text-xs text-slate-400 font-body">Vehículo: <span className="font-mono">{ot.vehiculo_id}</span></p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full font-body ${ESTADO_BADGE[ot.estado] ?? 'bg-slate-700 text-slate-400'}`}>
                        {ot.estado}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs px-2 py-0.5 rounded-full font-body bg-slate-900 text-slate-400 capitalize">
                        {ot.modalidad}
                      </span>
                      <span className="ml-auto text-sm font-mono font-semibold text-teal">
                        S/. {Number(ot.monto_estimado).toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-800/60 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.3)] p-5">
            <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
            <p className="text-sm text-slate-400 font-body">
              Aquí solo ves las OTs que el mecánico master te asignó. Registra repuestos
              consumidos y el costo de mano de obra. La revisión final y la liberación del
              vehículo las realiza el mecánico master — esas acciones no están disponibles
              en tu perfil.
            </p>
          </section>
        </main>
      </div>
    </div>
  )
}

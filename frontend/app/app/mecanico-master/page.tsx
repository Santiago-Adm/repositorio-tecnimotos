'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'

interface OrdenTrabajo {
  id: string
  estado: string
  vehiculo_id?: string
  mecanico_master_id?: string
  delegado_a_junior?: boolean
}

export default function MecanicoMasterDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [ordenes, setOrdenes] = useState<OrdenTrabajo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function fetchOrdenes() {
    setLoading(true)
    setError(null)
    apiClient
      .get<OrdenTrabajo[]>('/v1/ordenes-trabajo')
      .then(d => { setOrdenes(Array.isArray(d) ? d : []); setLoading(false) })
      .catch((err: ApiCallError) => { setError(err.code); setLoading(false) })
  }

  useEffect(() => {
    if (user && user.rol !== 'MECANICO_MASTER') { router.replace('/login'); return }
    fetchOrdenes()
  }, [user, router])

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="MECANICO_MASTER" />
      <DashboardHeader userId={user.id} rol="MECANICO_MASTER" onLogout={logout} />

      <div className="flex">
        {/* Navegación — taller, catálogo (solo lectura), stock (consulta) */}
        <nav className="hidden md:flex flex-col w-48 shrink-0 border-r border-slate-800 min-h-[calc(100vh-56px)] p-4 gap-1">
          {['Mis OTs', 'Catálogo', 'Stock'].map(m => (
            <button key={m} className="text-left px-3 py-2 rounded-lg text-sm font-body text-slate-300 hover:bg-slate-800 transition-colors">
              {m}
            </button>
          ))}
        </nav>

        {/* Vista por defecto: OTs activas propias + delegadas (10 §4.6, 02 §4.3) */}
        <main className="flex-1 p-4 md:p-6 space-y-6">
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg font-semibold text-slate-100">Mis órdenes activas</h2>
              <button onClick={fetchOrdenes} className="text-xs text-teal font-body hover:underline">Actualizar</button>
            </div>

            {loading ? (
              <LoadingIndicator message="Cargando órdenes..." />
            ) : error ? (
              <ErrorDisplay code={error} onRetry={fetchOrdenes} />
            ) : ordenes.length === 0 ? (
              <EmptyState
                title="Sin órdenes activas"
                description="Cuando abras una nueva orden de trabajo aparecerá aquí."
              />
            ) : (
              <div className="space-y-3">
                {ordenes.map(ot => (
                  <div
                    key={ot.id}
                    className="rounded-xl bg-slate-800 border border-slate-700 p-4 flex items-center justify-between"
                  >
                    <div>
                      <p className="text-sm font-mono text-slate-200 truncate max-w-[180px]">{ot.id}</p>
                      {ot.vehiculo_id && (
                        <p className="text-xs text-slate-400 font-body">Vehículo: <span className="font-mono">{ot.vehiculo_id}</span></p>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      {/* Indicador de OT delegada a junior (02 §4.3, 10 §4.6) */}
                      {ot.delegado_a_junior && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-electric/20 text-electric font-body">
                          En ejecución por junior
                        </span>
                      )}
                      <span className={`text-xs px-2 py-1 rounded-full font-body ${
                        ot.estado === 'ABIERTA' ? 'bg-teal/20 text-teal' :
                        ot.estado === 'EN_EJECUCION' ? 'bg-electric/20 text-electric' :
                        'bg-slate-700 text-slate-400'
                      }`}>
                        {ot.estado}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
            <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
            <p className="text-sm text-slate-400 font-body">
              Abre una OT, arma la lista de repuestos, espera la aprobación del cliente y pasa a
              ejecución. Puedes delegar a un mecánico junior — sus OTs aparecen con indicador
              "En ejecución por junior". El cobro y la liberación del vehículo son el paso final.
              Máximo 4 taps para registrar un consumo de repuesto.
            </p>
          </section>
        </main>
      </div>
    </div>
  )
}

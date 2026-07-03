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

interface MecanicoDisponible {
  mecanico_id: string
  nivel: string
}

export default function MecanicoMasterDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [seccion, setSeccion] = useState<'Mis OTs' | 'Catálogo' | 'Stock'>('Mis OTs')
  const [ordenes, setOrdenes] = useState<OrdenTrabajo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [disponibilidad, setDisponibilidad] = useState<MecanicoDisponible[] | null>(null)
  const [errorDisponibilidad, setErrorDisponibilidad] = useState<string | null>(null)

  function fetchOrdenes() {
    // El backend no expone GET /v1/ordenes-trabajo (lista) aún — solo POST (crear) y GET por ID
    setLoading(false)
  }

  async function fetchDisponibilidad() {
    setErrorDisponibilidad(null)
    try {
      const data = await apiClient.get<{ mecanicos_disponibles: MecanicoDisponible[] }>('/v1/taller/disponibilidad')
      setDisponibilidad(data.mecanicos_disponibles)
    } catch (err) {
      setErrorDisponibilidad((err as ApiCallError).code)
    }
  }

  useEffect(() => {
    if (user && user.rol !== 'MECANICO_MASTER') { router.replace('/login'); return }
    setLoading(false)
    if (user) fetchDisponibilidad()
  }, [user, router])

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="MECANICO_MASTER" />
      <DashboardHeader userId={user.id} rol="MECANICO_MASTER" onLogout={logout} />

      <div className="flex">
        {/* Navegación — taller, catálogo (solo lectura), stock (consulta) */}
        <nav className="hidden md:flex flex-col w-48 shrink-0 border-r border-slate-800 min-h-[calc(100vh-56px)] p-4 gap-1">
          {(['Mis OTs', 'Catálogo', 'Stock'] as const).map(m => (
            <button
              key={m}
              onClick={() => setSeccion(m)}
              className={`text-left px-3 py-2 rounded-lg text-sm font-body transition-colors ${
                seccion === m ? 'text-teal bg-teal/10 font-semibold' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              {m}
            </button>
          ))}
        </nav>

        {/* Vista por defecto: OTs activas propias + delegadas (10 §4.6, 02 §4.3) */}
        <main className="flex-1 p-4 md:p-6 space-y-6">
          {seccion !== 'Mis OTs' && (
            <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-8 text-center">
              <p className="text-slate-400 font-body text-sm">
                Sección <span className="text-slate-200 font-mono">{seccion}</span> — disponible próximamente.
              </p>
            </section>
          )}

          {seccion === 'Mis OTs' && (
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
                  title="Listado de órdenes aún no disponible"
                  description="El backend todavía no expone un endpoint para listar órdenes de trabajo activas — solo permite abrir una nueva o consultar una si ya conoces su ID. Esta vista quedará activa cuando esa pieza se construya en una sesión de backend."
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
          )}

          {seccion === 'Mis OTs' && (
            <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
              <h3 className="font-display text-sm font-semibold text-slate-300 mb-3">Disponibilidad del equipo</h3>
              {errorDisponibilidad ? (
                <ErrorDisplay code={errorDisponibilidad} onRetry={fetchDisponibilidad} />
              ) : disponibilidad === null ? (
                <LoadingIndicator message="Cargando disponibilidad..." />
              ) : disponibilidad.length === 0 ? (
                <p className="text-sm text-slate-500 font-body">Sin mecánicos disponibles en este momento.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {disponibilidad.map(m => (
                    <span
                      key={m.mecanico_id}
                      className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300"
                    >
                      {m.mecanico_id.slice(0, 8)} · {m.nivel}
                    </span>
                  ))}
                </div>
              )}
            </section>
          )}

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

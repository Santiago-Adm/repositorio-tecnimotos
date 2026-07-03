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
}

export default function MecanicoJuniorDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [ordenes, setOrdenes] = useState<OrdenTrabajo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function fetchOrdenes() {
    // El backend no expone GET /v1/ordenes-trabajo (lista) aún — solo POST (crear) y GET por ID
    setLoading(false)
  }

  useEffect(() => {
    if (user && user.rol !== 'MECANICO_JUNIOR') { router.replace('/login'); return }
    setLoading(false)
  }, [user, router])

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="MECANICO_JUNIOR" />
      <DashboardHeader userId={user.id} rol="MECANICO_JUNIOR" onLogout={logout} />

      <div className="flex">
        {/* Navegación — solo taller (02 §4.1 MECANICO_JUNIOR) */}
        <nav className="hidden md:flex flex-col w-48 shrink-0 border-r border-slate-800 min-h-[calc(100vh-56px)] p-4 gap-1">
          <button
            onClick={() => { /* única sección — sin más destinos que navegar */ }}
            className="text-left px-3 py-2 rounded-lg text-sm font-body text-teal bg-teal/10"
          >
            Mis OTs
          </button>
          {/* Sin "declarar listo" ni "autorizar precio" — componente no existe (02 §4.3, 10 §1.2, 10 §4.7) */}
        </nav>

        {/* Vista por defecto: OTs asignadas a este junior (10 §4.7) */}
        <main className="flex-1 p-4 md:p-6 space-y-6">
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
                title="Listado de órdenes aún no disponible"
                description="El backend todavía no expone un endpoint para listar tus órdenes de trabajo asignadas — solo permite consultar una orden si ya conoces su ID. Esta vista quedará activa cuando esa pieza se construya en una sesión de backend."
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
                        <p className="text-xs text-slate-400 font-body">
                          Vehículo: <span className="font-mono">{ot.vehiculo_id}</span>
                        </p>
                      )}
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full font-body ${
                      ot.estado === 'EN_EJECUCION' ? 'bg-teal/20 text-teal' : 'bg-slate-700 text-slate-400'
                    }`}>
                      {ot.estado}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
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

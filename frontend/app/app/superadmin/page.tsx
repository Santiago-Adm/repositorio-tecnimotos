'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'

interface Metrics {
  requests_total?: number
  requests_per_second?: number
  [key: string]: unknown
}

export default function SuperadminDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (user && user.rol !== 'SUPERADMIN') {
      router.replace('/login')
      return
    }
    apiClient
      .get<Metrics>('/v1/metrics')
      .then(d => { setMetrics(d); setLoading(false) })
      .catch((err: ApiCallError) => { setError(err.code); setLoading(false) })
  }, [user, router])

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="SUPERADMIN" />

      {/* Cabecera con punto de entrada visual de impersonación (DEP-10-001, solo visual) */}
      <DashboardHeader
        userId={user.id}
        rol="SUPERADMIN"
        onLogout={logout}
        extraAction={
          <button
            disabled
            title="Disponible tras DEP-10-001"
            className="hidden sm:block px-3 py-1.5 rounded-lg text-xs font-body text-slate-500 border border-slate-700 cursor-not-allowed"
          >
            Ver como rol — depuración
          </button>
        }
      />

      <div className="flex">
        {/* Navegación — todos los módulos (02 §4.1 SUPERADMIN) */}
        <nav className="hidden md:flex flex-col w-48 shrink-0 border-r border-slate-800 min-h-[calc(100vh-56px)] p-4 gap-1">
          {['Catálogo', 'Stock', 'Pedidos', 'Taller', 'Admin', 'Logs y config'].map(m => (
            <button
              key={m}
              className="text-left px-3 py-2 rounded-lg text-sm font-body text-slate-300 hover:bg-slate-800 transition-colors"
            >
              {m}
            </button>
          ))}
        </nav>

        <main className="flex-1 p-6 space-y-6">
          {/* Vista por defecto: resumen operativo (EP-OBS-01) */}
          <section>
            <h2 className="font-display text-lg font-semibold text-slate-100 mb-4">
              Resumen operativo
            </h2>
            {loading ? (
              <LoadingIndicator message="Cargando métricas..." />
            ) : error ? (
              <ErrorDisplay
                code={error}
                onRetry={() => { setLoading(true); setError(null); apiClient.get<Metrics>('/v1/metrics').then(d => { setMetrics(d); setLoading(false) }).catch((e: ApiCallError) => { setError(e.code); setLoading(false) }) }}
              />
            ) : metrics ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(metrics).map(([k, v]) => (
                  <div key={k} className="rounded-xl bg-slate-800 border border-slate-700 p-4">
                    <p className="text-xs text-slate-400 font-body mb-1">{k.replace(/_/g, ' ')}</p>
                    <p className="text-xl font-mono text-teal">{String(v)}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </section>

          {/* Cómo funciona */}
          <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
            <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
            <p className="text-sm text-slate-400 font-body">
              Como superadministrador tienes visibilidad completa del sistema: catálogo, stock, pedidos,
              taller y administración de usuarios. Las métricas en tiempo real te muestran el estado
              operativo. Ante un reporte de error, usa "Ver como rol" (disponible próximamente) para
              diagnóstico en modo solo lectura.
            </p>
          </section>
        </main>
      </div>
    </div>
  )
}

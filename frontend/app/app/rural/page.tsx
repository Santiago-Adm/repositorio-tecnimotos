'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'

const TIMEOUT_MS = 30_000

interface Repuesto {
  id: string
  codigo: string
  nombre: string
  activo?: boolean
}

export default function ClienteRuralDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [seccion, setSeccion] = useState<'¿Qué necesitas?' | 'Mis reservas'>('¿Qué necesitas?')
  const [busqueda, setBusqueda] = useState('')
  const [repuestos, setRepuestos] = useState<Repuesto[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [timedOut, setTimedOut] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (user && user.rol !== 'CLIENTE_RURAL') { router.replace('/rural'); return }
  }, [user, router])

  async function buscar(e?: React.FormEvent) {
    e?.preventDefault()
    if (!busqueda.trim()) return

    abortRef.current?.abort()
    abortRef.current = new AbortController()
    const controller = abortRef.current

    setLoading(true)
    setError(null)
    setTimedOut(false)

    // Tolerancia de 30s de desconexión (RNT-05, 10 §6.6)
    const timeoutId = setTimeout(() => {
      controller.abort()
      setLoading(false)
      setTimedOut(true)
    }, TIMEOUT_MS)

    try {
      const data = await apiClient.get<{repuestos: Repuesto[], total: number}>(
        `/v1/repuestos?universo=mototaxi_3r&q=${encodeURIComponent(busqueda)}`
      )
      clearTimeout(timeoutId)
      setRepuestos(data.repuestos ?? [])
    } catch (err) {
      clearTimeout(timeoutId)
      if ((err as Error).name === 'AbortError') return
      setError((err as ApiCallError).code ?? 'TIMEOUT')
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="CLIENTE_RURAL" />
      <DashboardHeader userId={user.id} rol="CLIENTE_RURAL" onLogout={logout} />

      <nav className="flex gap-2 px-4 py-3 border-b border-slate-800 overflow-x-auto">
        {(['¿Qué necesitas?', 'Mis reservas'] as const).map(m => (
          <button
            key={m}
            onClick={() => setSeccion(m)}
            className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-body transition-colors border ${
              seccion === m
                ? 'bg-teal border-teal text-white font-semibold'
                : 'text-slate-300 border-slate-700 hover:bg-slate-800'
            } whitespace-nowrap`}
          >
            {m}
          </button>
        ))}
      </nav>

      {/* Vista por defecto: confirmación de stock (10 §4.10 — mismo dolor principal que S1) */}
      <main className="p-4 md:p-6 space-y-6 max-w-lg mx-auto">
        {seccion !== '¿Qué necesitas?' && (
          <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-8 text-center">
            <p className="text-slate-400 font-body text-sm">
              Sección <span className="text-slate-200 font-mono">{seccion}</span> — disponible próximamente.
            </p>
          </section>
        )}

        {seccion === '¿Qué necesitas?' && (
          <section>
            <h2 className="font-display text-lg font-semibold text-slate-100 mb-4">
              ¿Qué necesitas hoy?
            </h2>
            <form onSubmit={buscar} className="flex gap-2">
              <input
                type="search"
                placeholder="Código o nombre del repuesto..."
                value={busqueda}
                onChange={e => setBusqueda(e.target.value)}
                className="flex-1 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-body focus:outline-none focus:ring-2 focus:ring-teal"
                autoFocus
              />
              <button
                type="submit"
                className="px-4 py-3 rounded-xl bg-teal text-white text-sm font-body hover:bg-teal/90 transition-colors"
              >
                Buscar
              </button>
            </form>

            <div className="mt-4">
              {loading ? (
                <LoadingIndicator message="Buscando..." />
              ) : timedOut ? (
                <div className="rounded-xl bg-slate-800/80 border border-slate-700 p-6 text-center">
                  <p className="text-sm font-body text-slate-300 mb-2">Conexión inestable</p>
                  <p className="text-xs font-body text-slate-400 mb-4">La búsqueda está tardando más de lo esperado debido a la cobertura rural.</p>
                  <button
                    onClick={() => buscar()}
                    className="px-4 py-2 rounded-lg bg-teal text-white text-sm font-body hover:bg-teal/90 transition-colors"
                  >
                    Reintentar
                  </button>
                </div>
              ) : error ? (
                <ErrorDisplay code={error} onRetry={() => buscar()} />
              ) : repuestos.length > 0 ? (
                <div className="space-y-2">
                  {repuestos.map(r => (
                    <div key={r.codigo} className="rounded-xl bg-slate-800 border border-slate-700 p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-mono text-slate-200">{r.codigo}</p>
                        <p className="text-xs text-slate-400 font-body">{r.nombre}</p>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full font-body ${r.activo !== false ? 'bg-teal/20 text-teal' : 'bg-red-900/30 text-red-400'}`}>
                        {r.activo !== false ? 'Disponible' : 'Sin stock'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : busqueda && !loading ? (
                <EmptyState title="Sin resultados" description="No encontramos ese repuesto. Prueba con otro código." />
              ) : null}
            </div>
          </section>
        )}

        <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
          <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
          <p className="text-sm text-slate-400 font-body">
            Busca el repuesto que necesitas. Si hay señal, ves el stock en segundos. Si la conexión
            se corta, tu búsqueda no se pierde — cuando vuelvas a tener señal puedes reintentar.
            Reserva con 2 a 3 días de anticipación para asegurar tu repuesto antes del viaje.
          </p>
        </section>
      </main>
    </div>
  )
}

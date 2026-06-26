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

interface Repuesto {
  codigo: string
  nombre: string
  disponible?: boolean
}

export default function ClienteConductorDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [busqueda, setBusqueda] = useState('')
  const [repuestos, setRepuestos] = useState<Repuesto[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (user && user.rol !== 'CLIENTE_CONDUCTOR') { router.replace('/conductor'); return }
  }, [user, router])

  async function buscar(e?: React.FormEvent) {
    e?.preventDefault()
    if (!busqueda.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.get<Repuesto[]>(`/v1/repuestos?q=${encodeURIComponent(busqueda)}`)
      setRepuestos(Array.isArray(data) ? data : [])
    } catch (err) {
      setError((err as ApiCallError).code)
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="CLIENTE_CONDUCTOR" />
      <DashboardHeader userId={user.id} rol="CLIENTE_CONDUCTOR" onLogout={logout} />

      {/* Navegación móvil-first — máximo 2 taps a consulta de stock (10 §6.5) */}
      <nav className="flex gap-2 px-4 py-3 border-b border-slate-800 overflow-x-auto">
        {['¿Qué necesitas?', 'Mis reservas', 'Mis pedidos', 'Mi historial'].map(m => (
          <button key={m} className="shrink-0 px-3 py-1.5 rounded-full text-xs font-body text-slate-300 border border-slate-700 hover:bg-slate-800 whitespace-nowrap">
            {m}
          </button>
        ))}
      </nav>

      {/* Vista por defecto: confirmación de stock — dolor principal S1 (10 §4.8, 01 §Segmentos) */}
      <main className="p-4 md:p-6 space-y-6 max-w-lg mx-auto">
        <section>
          <h2 className="font-display text-lg font-semibold text-slate-100 mb-4">
            ¿Qué necesitas hoy?
          </h2>
          <form onSubmit={buscar} className="flex gap-2">
            <input
              type="search"
              placeholder="Busca tu repuesto por código o nombre..."
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
              <LoadingIndicator message="Verificando stock..." />
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
                    <span className={`text-xs px-2 py-1 rounded-full font-body ${r.disponible !== false ? 'bg-teal/20 text-teal' : 'bg-red-900/30 text-red-400'}`}>
                      {r.disponible !== false ? 'Disponible' : 'Sin stock'}
                    </span>
                  </div>
                ))}
              </div>
            ) : busqueda ? (
              <EmptyState title="Sin resultados" description="No encontramos ese repuesto. Prueba con otro código o nombre." />
            ) : null}
          </div>
        </section>

        {/* mecánico_preferido_id — capacidad prometida en landing S1 (10 §4.8, §2.2) */}
        <section className="rounded-xl bg-slate-800 border border-slate-800 p-4">
          <p className="text-xs text-slate-400 font-body mb-1">Tu mecánico preferido</p>
          <p className="text-sm text-slate-300 font-body">No configurado</p>
          <button className="mt-2 text-xs text-teal font-body hover:underline">Configurar</button>
        </section>

        <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
          <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
          <p className="text-sm text-slate-400 font-body">
            Busca el repuesto que necesitas y confirma si hay stock antes de viajar a la tienda.
            Si está disponible, reserva con un día de anticipación. Tu mecánico preferido siempre
            estará asignado a tu vehículo.
          </p>
        </section>
      </main>
    </div>
  )
}

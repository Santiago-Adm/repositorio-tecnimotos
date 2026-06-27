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

interface Pedido {
  pedido_id: string
  estado: string
  monto_total?: number
  monto_efectivo?: number
  canal_origen?: string
  created_at?: string
  precio_visible?: boolean
  precio_ajustado?: number | null
}

export default function ClienteDistritoDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [listas, setListas] = useState<Pedido[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function fetchListas() {
    setLoading(true)
    setError(null)
    apiClient
      .get<{pedidos: Pedido[], total: number}>('/v1/pedidos')
      .then(d => { setListas(d.pedidos ?? []); setLoading(false) })
      .catch((err: ApiCallError) => { setError(err.code); setLoading(false) })
  }

  useEffect(() => {
    if (user && user.rol !== 'CLIENTE_DISTRITO') { router.replace('/distrito'); return }
    fetchListas()
  }, [user, router])

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="CLIENTE_DISTRITO" />
      <DashboardHeader userId={user.id} rol="CLIENTE_DISTRITO" onLogout={logout} />

      <nav className="flex gap-2 px-4 py-3 border-b border-slate-800 overflow-x-auto">
        {['Mi lista activa', 'Mis pedidos'].map(m => (
          <button key={m} className="shrink-0 px-3 py-1.5 rounded-full text-xs font-body text-slate-300 border border-slate-700 hover:bg-slate-800 whitespace-nowrap">
            {m}
          </button>
        ))}
      </nav>

      {/* Vista por defecto: lista progresiva activa (10 §4.9, 02 §5.3 HU-S2-06) */}
      <main className="p-4 md:p-6 space-y-6 max-w-2xl mx-auto">
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-lg font-semibold text-slate-100">Mi lista de repuestos</h2>
            <button onClick={fetchListas} className="text-xs text-teal font-body hover:underline">Actualizar</button>

          </div>

          {loading ? (
            <LoadingIndicator message="Cargando tu lista..." />
          ) : error ? (
            <ErrorDisplay code={error} onRetry={fetchListas} />
          ) : listas.length === 0 ? (
            <EmptyState
              title="No tienes listas activas"
              description="Arma tu pedido por lista de repuestos para tu tienda o taller."
              action={{ label: 'Crear lista nueva', onClick: () => {} }}
            />
          ) : (
            <div className="space-y-3">
              {listas.map(l => (
                <div key={l.pedido_id} className="rounded-xl bg-slate-800 border border-slate-700 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-mono text-slate-200 truncate max-w-[160px]">{l.pedido_id}</p>
                    <span className={`text-xs px-2 py-1 rounded-full font-body ${
                      l.estado === 'PENDIENTE_CONFIRMACION' ? 'bg-teal/20 text-teal' :
                      l.estado === 'PENDIENTE_VALIDACION' ? 'bg-electric/20 text-electric' :
                      l.estado === 'CONFIRMADO' ? 'bg-green-900/40 text-green-400' :
                      'bg-slate-700 text-slate-400'
                    }`}>
                      {l.estado?.replace(/_/g, ' ')}
                    </span>
                  </div>
                  {/*
                    precio_ajustado solo visible cuando ADMINISTRADOR lo aprobó
                    (02 §5.3 HU-S2-02 — antes de aprobación NO se muestra el precio)
                  */}
                  {l.monto_total != null ? (
                    <p className="text-sm font-mono text-teal mt-1">
                      S/ {l.monto_total.toFixed(2)}
                    </p>
                  ) : (
                    <p className="text-xs text-slate-500 font-body mt-1">Precio en revisión</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
          <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
          <p className="text-sm text-slate-400 font-body">
            Arma tu lista completa de repuestos de una sola vez. El equipo revisa precios y
            disponibilidad. Recibirás la proforma final con precio confirmado una vez que el
            administrador apruebe — antes de eso verás el estado "en revisión".
          </p>
        </section>
      </main>
    </div>
  )
}

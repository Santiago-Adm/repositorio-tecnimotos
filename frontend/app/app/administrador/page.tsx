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

interface StockItem {
  repuesto_id: string
  codigo: string
  cantidad_disponible: number
  cantidad_apartada: number
  umbral_minimo: number
  esta_bajo_umbral: boolean
  esta_agotado: boolean
}

interface StockResponse {
  stocks: StockItem[]
  total: number
}

type Seccion = 'Stock' | 'Catálogo' | 'Pedidos' | 'Taller' | 'Admin'

export default function AdministradorDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [seccion, setSeccion] = useState<Seccion>('Stock')
  const [stock, setStock] = useState<StockItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function fetchStock(silencioso = false) {
    if (!silencioso) setLoading(true)
    setError(null)
    apiClient
      .get<StockResponse>('/v1/stock')
      .then(d => { setStock(d.stocks); setLoading(false) })
      .catch((err: ApiCallError) => { if (!silencioso) setError(err.code); setLoading(false) })
  }

  useEffect(() => {
    if (user && user.rol !== 'ADMINISTRADOR') { router.replace('/login'); return }
    fetchStock()
    const intervalo = setInterval(() => fetchStock(true), 30000)
    return () => clearInterval(intervalo)
  }, [user, router])

  if (!user) return null

  const alertas = stock.filter(s => s.esta_bajo_umbral)

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="ADMINISTRADOR" />
      <DashboardHeader userId={user.id} rol="ADMINISTRADOR" onLogout={logout} />

      <div className="flex">
        {/* Navegación — 02 §4.1 ADMINISTRADOR */}
        <nav className="hidden md:flex flex-col w-48 shrink-0 border-r border-slate-800 min-h-[calc(100vh-56px)] p-4 gap-1">
          {(['Stock', 'Catálogo', 'Pedidos', 'Taller', 'Admin'] as Seccion[]).map(m => (
            <button
              key={m}
              onClick={() => setSeccion(m)}
              className={`text-left px-3 py-2 rounded-lg text-sm font-body transition-colors ${
                seccion === m ? 'text-teal bg-teal/10' : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              {m}
            </button>
          ))}
        </nav>

        <main className="flex-1 p-6 space-y-6">
          {seccion !== 'Stock' && (
            <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-8 text-center">
              <p className="text-slate-400 font-body text-sm">
                Sección <span className="text-slate-200 font-mono">{seccion}</span> — disponible próximamente.
              </p>
            </section>
          )}
          {seccion === 'Stock' && alertas.length > 0 && (
            <section>
              <h2 className="font-display text-base font-semibold text-electric mb-3">
                Alertas de stock ({alertas.length})
              </h2>
              <div className="rounded-xl border border-electric/30 bg-electric/5 divide-y divide-slate-800">
                {alertas.map(s => (
                  <div key={s.codigo} className="flex items-center justify-between px-4 py-3">
                    <p className="text-sm font-mono text-slate-200">{s.codigo}</p>
                    <div className="text-right">
                      <p className="text-sm font-mono text-electric">{s.cantidad_disponible} uds</p>
                      <p className="text-xs text-slate-500 font-body">mínimo: {s.umbral_minimo}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {seccion === 'Stock' && <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg font-semibold text-slate-100">Stock general</h2>
              <button onClick={() => fetchStock()} className="text-xs text-teal font-body hover:underline">Actualizar</button>
            </div>
            {loading ? (
              <LoadingIndicator message="Cargando stock..." />
            ) : error ? (
              <ErrorDisplay code={error} onRetry={() => fetchStock()} />
            ) : stock.length === 0 ? (
              <EmptyState title="No hay stock registrado" description="Cuando se registren repuestos en el catálogo, aparecerán aquí." />
            ) : (
              <div className="rounded-xl border border-slate-800 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-800/60">
                    <tr>
                      <th className="text-left px-4 py-2 text-xs text-slate-400 font-body">Código</th>
                      <th className="text-right px-4 py-2 text-xs text-slate-400 font-body">Disponible</th>
                      <th className="text-right px-4 py-2 text-xs text-slate-400 font-body">Mínimo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {stock.map(s => (
                      <tr key={s.codigo} className={s.esta_bajo_umbral ? 'bg-electric/5' : ''}>
                        <td className="px-4 py-2 font-mono text-slate-200">{s.codigo}</td>
                        <td className="px-4 py-2 text-right font-mono text-slate-200">{s.cantidad_disponible}</td>
                        <td className="px-4 py-2 text-right font-mono text-slate-400">{s.umbral_minimo}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>}

          <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
            <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
            <p className="text-sm text-slate-400 font-body">
              El sistema informa, tú decides. Cuando un repuesto cae bajo su umbral mínimo, aparece
              en la sección de alertas. Desde aquí puedes gestionar catálogo, aprobar pedidos y
              comprobantes, supervisar taller y administrar usuarios. Elena tiene acceso en escritorio
              y en móvil — ambas superficies están optimizadas.
            </p>
          </section>
        </main>
      </div>
    </div>
  )
}

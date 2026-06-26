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
  descripcion?: string
  disponible?: boolean
}

export default function VendedorDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [busqueda, setBusqueda] = useState('')
  const [repuestos, setRepuestos] = useState<Repuesto[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)

  useEffect(() => {
    if (user && user.rol !== 'VENDEDOR') { router.replace('/login'); return }
  }, [user, router])

  async function buscar(e?: React.FormEvent) {
    e?.preventDefault()
    setLoading(true)
    setError(null)
    setSearched(true)
    try {
      const params = busqueda ? `?q=${encodeURIComponent(busqueda)}` : ''
      const data = await apiClient.get<Repuesto[]>(`/v1/repuestos${params}`)
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
      <SessionExpiredHandler rol="VENDEDOR" />
      <DashboardHeader userId={user.id} rol="VENDEDOR" onLogout={logout} />

      <div className="flex">
        {/* Navegación — catálogo y pedidos (02 §4.1 VENDEDOR) */}
        <nav className="hidden md:flex flex-col w-48 shrink-0 border-r border-slate-800 min-h-[calc(100vh-56px)] p-4 gap-1">
          {['Catálogo', 'Mis pedidos'].map(m => (
            <button key={m} className="text-left px-3 py-2 rounded-lg text-sm font-body text-slate-300 hover:bg-slate-800 transition-colors">
              {m}
            </button>
          ))}
          {/* No: modificar precio, aplicar descuento, aprobar comprobante, ajuste de stock (02 §4.1 VENDEDOR ❌) */}
        </nav>

        {/* Vista por defecto: catálogo en modo búsqueda (10 §4.5) */}
        <main className="flex-1 p-6 space-y-6">
          <section>
            <h2 className="font-display text-lg font-semibold text-slate-100 mb-4">Catálogo</h2>
            <form onSubmit={buscar} className="flex gap-3 mb-6">
              <input
                type="search"
                placeholder="Buscar por código o nombre..."
                value={busqueda}
                onChange={e => setBusqueda(e.target.value)}
                className="flex-1 px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-sm font-body focus:outline-none focus:ring-2 focus:ring-teal"
              />
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-teal text-white text-sm font-body hover:bg-teal/90 transition-colors"
              >
                Buscar
              </button>
            </form>

            {loading ? (
              <LoadingIndicator message="Buscando repuestos..." />
            ) : error ? (
              <ErrorDisplay code={error} onRetry={buscar} />
            ) : searched && repuestos.length === 0 ? (
              <EmptyState title="Sin resultados" description="No se encontraron repuestos con ese criterio." />
            ) : repuestos.length > 0 ? (
              <div className="rounded-xl border border-slate-800 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-800/60">
                    <tr>
                      <th className="text-left px-4 py-2 text-xs text-slate-400 font-body">Código</th>
                      <th className="text-left px-4 py-2 text-xs text-slate-400 font-body">Nombre</th>
                      {/* precio_costo y margen no visibles para VENDEDOR (02 §4.1) */}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {repuestos.map(r => (
                      <tr key={r.codigo} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-4 py-3 font-mono text-slate-200">{r.codigo}</td>
                        <td className="px-4 py-3 text-slate-300 font-body">{r.nombre}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-slate-500 font-body">Busca un repuesto para comenzar.</p>
            )}
          </section>

          <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
            <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
            <p className="text-sm text-slate-400 font-body">
              Busca repuestos en el catálogo, registra pedidos y genera comprobantes en
              estado "pendiente de validación". El administrador revisa y aprueba. Puedes
              ver el stock disponible, pero los precios de costo y márgenes son confidenciales.
            </p>
          </section>
        </main>
      </div>
    </div>
  )
}

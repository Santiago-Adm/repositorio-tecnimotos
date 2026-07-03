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
import { consultarPrecio, PrecioResult } from '@/src/lib/precio'

interface Repuesto {
  id: string
  codigo: string
  nombre: string
  categoria?: string
  activo?: boolean
}

interface RepuestosResponse {
  repuestos: Repuesto[]
  total: number
}

type Seccion = 'Catálogo' | 'Mis pedidos'

export default function VendedorDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [seccion, setSeccion] = useState<Seccion>('Catálogo')
  const [busqueda, setBusqueda] = useState('')
  const [todos, setTodos] = useState<Repuesto[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)
  const [precios, setPrecios] = useState<Record<string, PrecioResult | 'cargando' | 'error'>>({})

  useEffect(() => {
    if (user && user.rol !== 'VENDEDOR') { router.replace('/login'); return }
  }, [user, router])

  // EP-CAT-01 no tiene parámetro de búsqueda por texto — se trae el universo
  // completo y se filtra en cliente por código/nombre.
  async function buscar(e?: React.FormEvent) {
    e?.preventDefault()
    setLoading(true)
    setError(null)
    setSearched(true)
    try {
      const data = await apiClient.get<RepuestosResponse>('/v1/repuestos?universo=mototaxi_3r')
      setTodos(data.repuestos ?? [])
    } catch (err) {
      setError((err as ApiCallError).code)
    } finally {
      setLoading(false)
    }
  }

  const repuestos = busqueda.trim()
    ? todos.filter(r =>
        r.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
        r.codigo.toLowerCase().includes(busqueda.toLowerCase()),
      )
    : todos

  // EP-CAT-02-B — rol interno: nivel_visibilidad=0, sin cupo diario.
  async function verPrecio(codigo: string) {
    setPrecios(prev => ({ ...prev, [codigo]: 'cargando' }))
    try {
      const result = await consultarPrecio(codigo, false)
      setPrecios(prev => ({ ...prev, [codigo]: result }))
    } catch {
      setPrecios(prev => ({ ...prev, [codigo]: 'error' }))
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
          {(['Catálogo', 'Mis pedidos'] as Seccion[]).map(m => (
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
          {/* No: modificar precio, aplicar descuento, aprobar comprobante, ajuste de stock (02 §4.1 VENDEDOR ❌) */}
        </nav>

        <main className="flex-1 p-6 space-y-6">
          {seccion === 'Mis pedidos' && (
            <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-8 text-center">
              <p className="text-slate-400 font-body text-sm">Sección <span className="text-slate-200 font-mono">Mis pedidos</span> — disponible próximamente.</p>
            </section>
          )}
          {seccion === 'Catálogo' && <section>
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
                      <th className="text-left px-4 py-2 text-xs text-slate-400 font-body">Precio de venta</th>
                      {/* precio_costo y margen no visibles para VENDEDOR (02 §4.1) */}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {repuestos.map(r => {
                      const p = precios[r.codigo]
                      return (
                        <tr key={r.codigo} className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-3 font-mono text-slate-200">{r.codigo}</td>
                          <td className="px-4 py-3 text-slate-300 font-body">{r.nombre}</td>
                          <td className="px-4 py-3 font-mono">
                            {!p ? (
                              <button onClick={() => verPrecio(r.codigo)} className="text-xs text-teal hover:underline">
                                Ver precio
                              </button>
                            ) : p === 'cargando' ? (
                              <span className="text-xs text-slate-500">Consultando...</span>
                            ) : p === 'error' ? (
                              <span className="text-xs text-red-400">Error al consultar</span>
                            ) : p.precio_visible ? (
                              <span className="text-teal font-bold">S/. {Number(p.precio_venta).toFixed(2)}</span>
                            ) : (
                              <span className="text-xs text-slate-500">{p.mensaje ?? 'No disponible'}</span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-slate-500 font-body">Busca un repuesto para comenzar.</p>
            )}
          </section>}

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

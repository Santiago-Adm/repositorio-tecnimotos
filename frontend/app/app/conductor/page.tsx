'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'
import RepuestoCard from '@/src/components/RepuestoCard'
import { useReservar, PENDING_RESERVA_KEY } from '@/src/lib/useReservar'

interface Repuesto {
  id: string
  codigo: string
  nombre: string
  activo?: boolean
  imagen_principal_url?: string | null
}

export default function ClienteConductorDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [seccion, setSeccion] = useState<'¿Qué necesitas?' | 'Mis reservas' | 'Mis pedidos' | 'Mi historial'>('¿Qué necesitas?')
  const [busqueda, setBusqueda] = useState('')
  const [todos, setTodos] = useState<Repuesto[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pendienteCodigo, setPendienteCodigo] = useState<string | null>(null)
  const { reservar, reservandoCodigo, confirmacion, error: errorReserva } = useReservar()

  useEffect(() => {
    if (user && user.rol !== 'CLIENTE_CONDUCTOR') { router.replace('/conductor'); return }
  }, [user, router])

  // EP-CAT-01 no tiene parámetro de búsqueda por texto — se trae el universo
  // completo y se filtra en cliente por código/nombre.
  async function buscar(e?: React.FormEvent) {
    e?.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.get<{ repuestos: Repuesto[]; total: number }>('/v1/repuestos?universo=mototaxi_3r')
      setTodos(data.repuestos ?? [])
    } catch (err) {
      setError((err as ApiCallError).code)
    } finally {
      setLoading(false)
    }
  }

  // Regla 2.2 — retoma una reserva iniciada sin sesión desde una landing pública.
  useEffect(() => {
    const codigo = localStorage.getItem(PENDING_RESERVA_KEY)
    if (codigo) {
      setPendienteCodigo(codigo)
      setBusqueda(codigo)
      localStorage.removeItem(PENDING_RESERVA_KEY)
    }
    buscar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const repuestos = useMemo(() => {
    if (!todos) return []
    const term = busqueda.toLowerCase().trim()
    if (!term) return todos
    return todos.filter(r => r.nombre.toLowerCase().includes(term) || r.codigo.toLowerCase().includes(term))
  }, [todos, busqueda])

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="CLIENTE_CONDUCTOR" />
      <DashboardHeader userId={user.id} rol="CLIENTE_CONDUCTOR" onLogout={logout} />

      {/* Navegación móvil-first — máximo 2 taps a consulta de stock (10 §6.5) */}
      <nav className="flex gap-2 px-4 py-3 border-b border-slate-800 overflow-x-auto">
        {(['¿Qué necesitas?', 'Mis reservas', 'Mis pedidos', 'Mi historial'] as const).map(m => (
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

      {/* Vista por defecto: confirmación de stock — dolor principal S1 (10 §4.8, 01 §Segmentos) */}
      <main className="p-4 md:p-6 space-y-6 max-w-lg mx-auto">
        {seccion !== '¿Qué necesitas?' && (
          <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-8 text-center">
            <p className="text-slate-400 font-body text-sm">
              Sección <span className="text-slate-200 font-mono">{seccion}</span> — disponible próximamente.
            </p>
          </section>
        )}

        {seccion === '¿Qué necesitas?' && (
          <>
            <section>
              <h2 className="font-display text-lg font-semibold text-slate-100 mb-4">
                ¿Qué necesitas hoy?
              </h2>

              {pendienteCodigo && (
                <p className="mb-3 text-xs font-body text-electric bg-electric/10 border border-electric/30 rounded-lg px-3 py-2">
                  Retomando tu reserva de <span className="font-mono font-bold">{pendienteCodigo}</span> — confírmala abajo.
                </p>
              )}

              <form onSubmit={e => e.preventDefault()} className="flex gap-2">
                <input
                  type="search"
                  placeholder="Busca tu repuesto por código o nombre..."
                  value={busqueda}
                  onChange={e => setBusqueda(e.target.value)}
                  className="flex-1 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-body focus:outline-none focus:ring-2 focus:ring-teal"
                  autoFocus
                />
              </form>

              {errorReserva && <p className="mt-2 text-xs text-red-400 font-body">{errorReserva}</p>}

              <div className="mt-4 space-y-2">
                {loading || todos === null ? (
                  <LoadingIndicator message="Verificando stock..." />
                ) : error ? (
                  <ErrorDisplay code={error} onRetry={() => buscar()} />
                ) : repuestos.length > 0 ? (
                  repuestos.map(r => (
                    <RepuestoCard
                      key={r.codigo}
                      codigo={r.codigo}
                      nombre={r.nombre}
                      imagenUrl={r.imagen_principal_url}
                      disponible={r.activo !== false}
                      extra={
                        confirmacion?.codigo === r.codigo ? (
                          <span className="text-xs font-mono text-teal font-bold">
                            Reservado ✓ {confirmacion.reserva_id.slice(0, 8)}
                          </span>
                        ) : (
                          <button
                            onClick={() => reservar(r.id, r.codigo)}
                            disabled={reservandoCodigo === r.codigo || r.activo === false}
                            className="text-xs font-body font-semibold px-3 py-1.5 rounded-lg bg-teal text-white hover:bg-teal/90 disabled:opacity-50 transition-colors"
                          >
                            {reservandoCodigo === r.codigo ? 'Reservando...' : 'Reservar'}
                          </button>
                        )
                      }
                    />
                  ))
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
          </>
        )}

        <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
          <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
          <p className="text-sm text-slate-400 font-body">
            Busca el repuesto que necesitas y confirma si hay stock antes de viajar a la tienda.
            Si está disponible, resérvalo con un día de anticipación. Tu mecánico preferido siempre
            estará asignado a tu vehículo.
          </p>
        </section>
      </main>
    </div>
  )
}

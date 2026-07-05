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
import RepuestoCard from '@/src/components/RepuestoCard'
import RuralResumenTab from '@/src/components/dashboard/RuralResumenTab'
import { useMiVehiculo } from '@/src/lib/useMiVehiculo'
import AppSidebarNav from '@/src/components/dashboard/AppSidebarNav'

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
  const [seccion, setSeccion] = useState<'Resumen' | '¿Qué necesitas?' | 'Mis reservas'>('Resumen')
  const [busqueda, setBusqueda] = useState('')
  const [repuestos, setRepuestos] = useState<Repuesto[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [timedOut, setTimedOut] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const { vehiculo } = useMiVehiculo()

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
      // EP-CAT-01 no soporta búsqueda por texto (`q` no existe en el
      // contrato real) — antes se enviaba igual y el backend lo ignoraba
      // silenciosamente, mostrando el universo completo sin filtrar. Ahora
      // se filtra en cliente sobre el universo real del vehículo (Pieza C).
      const data = await apiClient.get<{repuestos: Repuesto[], total: number}>(
        `/v1/repuestos?universo=${vehiculo?.universo ?? 'mototaxi_3r'}`
      )
      clearTimeout(timeoutId)
      const termino = busqueda.toLowerCase().trim()
      const filtrados = termino
        ? (data.repuestos ?? []).filter(r => r.nombre.toLowerCase().includes(termino) || r.codigo.toLowerCase().includes(termino))
        : (data.repuestos ?? [])
      setRepuestos(filtrados)
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

      <div className="flex flex-col md:flex-row">
        <AppSidebarNav
          surface="light"
          secciones={['Resumen', '¿Qué necesitas?', 'Mis reservas']}
          activa={seccion}
          onSeleccionar={s => setSeccion(s as typeof seccion)}
        />

      {/* Vista por defecto: confirmación de stock (10 §4.10 — mismo dolor principal que S1) */}
      <main className={`flex-1 min-w-0 w-full p-4 md:p-6 space-y-6 ${seccion === 'Resumen' ? 'max-w-6xl mx-auto' : 'max-w-lg mx-auto'}`}>
        {seccion === 'Resumen' && <RuralResumenTab />}

        {seccion === 'Mis reservas' && (
          <section className="rounded-xl bg-white border border-slate-200 shadow-[0_4px_20px_-8px_rgba(15,23,42,0.06)] p-8 text-center">
            <p className="text-slate-400 font-body text-sm">
              El backend todavía no expone un endpoint para listar tus reservas
              (solo permite crear una reserva o liberarla). Esta sección quedará
              activa cuando esa pieza se construya en una sesión de backend.
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
                className="flex-1 min-w-0 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-body focus:outline-none focus:ring-2 focus:ring-teal"
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
                  {/* Payload mínimo (RNT-05/10 §6.6): sin imagen, sin consulta de precio */}
                  {repuestos.map(r => (
                    <RepuestoCard
                      key={r.codigo}
                      codigo={r.codigo}
                      nombre={r.nombre}
                      disponible={r.activo !== false}
                    />
                  ))}
                </div>
              ) : busqueda && !loading ? (
                <EmptyState title="Sin resultados" description="No encontramos ese repuesto. Prueba con otro código." />
              ) : null}
            </div>
          </section>
        )}

        <section className="rounded-xl bg-white border border-slate-200 shadow-[0_4px_20px_-8px_rgba(15,23,42,0.06)] p-5">
          <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
          <p className="text-sm text-slate-400 font-body">
            Busca el repuesto que necesitas. Si hay señal, ves el stock en segundos. Si la conexión
            se corta, tu búsqueda no se pierde — cuando vuelvas a tener señal puedes reintentar.
            Reserva con 2 a 3 días de anticipación para asegurar tu repuesto antes del viaje.
          </p>
        </section>
      </main>
      </div>
    </div>
  )
}

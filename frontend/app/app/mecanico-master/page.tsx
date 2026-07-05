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
import MecanicoMasterResumenTab from '@/src/components/dashboard/MecanicoMasterResumenTab'
import CatalogoNavegable from '@/src/components/dashboard/CatalogoNavegable'
import AppSidebarNav from '@/src/components/dashboard/AppSidebarNav'

type Seccion = 'Mis OTs' | 'Catálogo' | 'Stock'

interface OrdenTrabajo {
  ot_id: string
  estado: string
  vehiculo_id: string
  mecanico_master_id: string
  mecanico_junior_id: string | null
  modalidad: string
  urgencia: string
  monto_estimado: string
  costo_mano_obra: string | null
  cliente_aprobo_lista: boolean
  aceptada_en: string | null
  vehiculo: VehiculoOT | null
  created_at: string
}

interface VehiculoOT {
  universo: 'mototaxi_3r' | 'mototaxi_4r' | 'motolineal'
  modelo: string
  año: number | null
}

interface MecanicoDisponible {
  mecanico_id: string
  nivel: string
}

const ESTADO_BADGE: Record<string, string> = {
  ABIERTA: 'bg-teal/20 text-teal',
  LISTA_REPUESTOS: 'bg-electric/20 text-electric',
  EN_EJECUCION: 'bg-electric/20 text-electric',
  REVISION_FINAL: 'bg-teal/20 text-teal',
  CERRADA: 'bg-slate-700 text-slate-400',
  CANCELADA: 'bg-red-900/30 text-red-400',
}

const URGENCIA_BADGE: Record<string, string> = {
  alta: 'bg-red-900/30 text-red-400',
  media: 'bg-slate-700 text-slate-300',
  baja: 'bg-slate-800 text-slate-500',
}

export default function MecanicoMasterDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [seccion, setSeccion] = useState<Seccion>('Mis OTs')
  const [ordenes, setOrdenes] = useState<OrdenTrabajo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [disponibilidad, setDisponibilidad] = useState<MecanicoDisponible[] | null>(null)
  const [errorDisponibilidad, setErrorDisponibilidad] = useState<string | null>(null)

  // Pieza E — al aceptar una OT se entra a su contexto de trabajo: catálogo
  // filtrado por el modelo del vehículo de ESE cliente, con precios visibles
  // (a diferencia del cliente, que solo ve disponibilidad). Conectado al
  // flujo de "Mis OTs", no es un módulo aislado.
  const [otEnTrabajo, setOtEnTrabajo] = useState<{ ot_id: string; vehiculo: VehiculoOT } | null>(null)
  const [aceptando, setAceptando] = useState<string | null>(null)
  const [errorAceptar, setErrorAceptar] = useState<string | null>(null)

  async function aceptarOT(ot: OrdenTrabajo) {
    setAceptando(ot.ot_id)
    setErrorAceptar(null)
    try {
      const data = await apiClient.post<{ ot_id: string; aceptada_en: string; vehiculo: VehiculoOT }>(
        `/v1/ordenes-trabajo/${ot.ot_id}/aceptar`,
      )
      setOrdenes(prev => prev.map(o => o.ot_id === ot.ot_id ? { ...o, aceptada_en: data.aceptada_en } : o))
      setOtEnTrabajo({ ot_id: ot.ot_id, vehiculo: data.vehiculo })
    } catch (err) {
      setErrorAceptar(err instanceof ApiCallError ? err.message : 'No se pudo aceptar la OT.')
    } finally {
      setAceptando(null)
    }
  }

  // EP-TAL-14 — OTs activas asignadas a este master (propias + delegadas a un
  // junior), regla "activa" configurable vía ADR-015 (estado + días abierta).
  // El backend resuelve el mecanico_id real a partir del usuario autenticado
  // (tabla `mecanico`, distinta de `usuario`) — no se envía como parámetro.
  async function fetchOrdenes() {
    if (!user) return
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.get<{ ordenes_trabajo: OrdenTrabajo[]; total: number }>(
        '/v1/ordenes-trabajo?activa=true',
      )
      setOrdenes(data.ordenes_trabajo ?? [])
    } catch (err) {
      setError((err as ApiCallError).code)
    } finally {
      setLoading(false)
    }
  }

  async function fetchDisponibilidad() {
    setErrorDisponibilidad(null)
    try {
      const data = await apiClient.get<{ mecanicos_disponibles: MecanicoDisponible[] }>('/v1/taller/disponibilidad')
      setDisponibilidad(data.mecanicos_disponibles)
    } catch (err) {
      setErrorDisponibilidad((err as ApiCallError).code)
    }
  }

  useEffect(() => {
    if (user && user.rol !== 'MECANICO_MASTER') { router.replace('/login'); return }
    if (user) {
      fetchOrdenes()
      fetchDisponibilidad()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, router])

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="MECANICO_MASTER" />
      <DashboardHeader userId={user.id} rol="MECANICO_MASTER" onLogout={logout} />

      <div className="flex flex-col md:flex-row">
        {/* Navegación — taller, catálogo (solo lectura), stock (consulta) */}
        <AppSidebarNav
          secciones={['Mis OTs', 'Catálogo', 'Stock']}
          activa={seccion}
          onSeleccionar={s => setSeccion(s as Seccion)}
        />

        {/* Vista por defecto: OTs activas propias + delegadas (10 §4.6, 02 §4.3) */}
        <main className="flex-1 min-w-0 p-4 md:p-6 space-y-6">
          {seccion === 'Stock' && (
            <section className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-800/60 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.3)] p-8 text-center">
              <p className="text-slate-400 font-body text-sm">
                Sección <span className="text-slate-200 font-mono">Stock</span> — disponible próximamente.
              </p>
            </section>
          )}

          {seccion === 'Catálogo' && (
            <section>
              <h2 className="font-display text-lg font-semibold text-slate-100 mb-4">Catálogo (solo lectura)</h2>
              <CatalogoNavegable />
            </section>
          )}

          {seccion === 'Mis OTs' && !loading && !error && !otEnTrabajo && <MecanicoMasterResumenTab ordenes={ordenes} />}

          {seccion === 'Mis OTs' && otEnTrabajo && (
            <section>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="font-display text-lg font-semibold text-slate-100">Trabajando en OT</h2>
                  <p className="text-xs text-slate-500 font-mono">{otEnTrabajo.ot_id}</p>
                </div>
                <button
                  onClick={() => setOtEnTrabajo(null)}
                  className="text-xs text-teal font-body hover:underline"
                >
                  ← Volver a Mis OTs
                </button>
              </div>
              {/* Precios visibles para el mecánico (rol interno) — a diferencia
                  del cliente, que solo ve disponibilidad. */}
              <CatalogoNavegable
                universoInicial={otEnTrabajo.vehiculo.universo}
                modeloInicial={otEnTrabajo.vehiculo.modelo}
              />
            </section>
          )}

          {seccion === 'Mis OTs' && !otEnTrabajo && (
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-display text-lg font-semibold text-slate-100">Mis órdenes activas</h2>
                <button onClick={fetchOrdenes} className="text-xs text-teal font-body hover:underline">Actualizar</button>
              </div>

              {errorAceptar && <p className="text-xs text-red-400 font-body mb-3">{errorAceptar}</p>}

              {loading ? (
                <LoadingIndicator message="Cargando órdenes..." />
              ) : error ? (
                <ErrorDisplay code={error} onRetry={fetchOrdenes} />
              ) : ordenes.length === 0 ? (
                <EmptyState
                  title="Sin órdenes activas"
                  description="No tienes órdenes de trabajo activas en este momento. Abre una nueva desde el registro de vehículos para empezar."
                />
              ) : (
                <div className="space-y-3">
                  {ordenes.map(ot => (
                    <div
                      key={ot.ot_id}
                      className="rounded-xl bg-slate-800 border border-slate-700 p-4 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-mono text-slate-200 truncate max-w-[220px]">{ot.ot_id}</p>
                          <p className="text-xs text-slate-400 font-body">Vehículo: <span className="font-mono">{ot.vehiculo_id}</span></p>
                        </div>
                        <div className="flex items-center gap-2">
                          {/* Indicador de OT delegada a junior (02 §4.3, 10 §4.6) */}
                          {ot.mecanico_junior_id && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-electric/20 text-electric font-body">
                              En ejecución por junior
                            </span>
                          )}
                          <span className={`text-xs px-2 py-1 rounded-full font-body ${ESTADO_BADGE[ot.estado] ?? 'bg-slate-700 text-slate-400'}`}>
                            {ot.estado}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs px-2 py-0.5 rounded-full font-body bg-slate-900 text-slate-400 capitalize">
                          {ot.modalidad}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-body capitalize ${URGENCIA_BADGE[ot.urgencia] ?? 'bg-slate-800 text-slate-500'}`}>
                          Urgencia {ot.urgencia}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded-full font-body bg-slate-900 text-slate-400">
                          {ot.cliente_aprobo_lista ? 'Lista aprobada' : 'Lista pendiente de aprobación'}
                        </span>
                        <span className="ml-auto text-sm font-mono font-semibold text-teal">
                          S/. {Number(ot.monto_estimado).toFixed(2)}
                        </span>
                      </div>
                      <div className="pt-1">
                        {ot.aceptada_en ? (
                          <button
                            onClick={() => ot.vehiculo && setOtEnTrabajo({ ot_id: ot.ot_id, vehiculo: ot.vehiculo })}
                            disabled={!ot.vehiculo}
                            className="text-xs font-body font-semibold px-3 py-2 rounded-lg bg-slate-900 text-teal border border-slate-700 hover:bg-slate-950 transition-colors disabled:opacity-50"
                          >
                            Aceptada ✓ — continuar trabajo
                          </button>
                        ) : (
                          <button
                            onClick={() => aceptarOT(ot)}
                            disabled={aceptando === ot.ot_id}
                            className="w-full sm:w-auto text-xs font-body font-semibold px-4 py-2.5 rounded-lg bg-teal text-white hover:bg-teal/90 disabled:opacity-50 transition-colors"
                          >
                            {aceptando === ot.ot_id ? 'Aceptando...' : 'Aceptar OT'}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {seccion === 'Mis OTs' && (
            <section className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-800/60 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.3)] p-5">
              <h3 className="font-display text-sm font-semibold text-slate-300 mb-3">Disponibilidad del equipo</h3>
              {errorDisponibilidad ? (
                <ErrorDisplay code={errorDisponibilidad} onRetry={fetchDisponibilidad} />
              ) : disponibilidad === null ? (
                <LoadingIndicator message="Cargando disponibilidad..." />
              ) : disponibilidad.length === 0 ? (
                <p className="text-sm text-slate-500 font-body">Sin mecánicos disponibles en este momento.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {disponibilidad.map(m => (
                    <span
                      key={m.mecanico_id}
                      className="text-xs font-mono px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300"
                    >
                      {m.mecanico_id.slice(0, 8)} · {m.nivel}
                    </span>
                  ))}
                </div>
              )}
            </section>
          )}

          <section className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-800/60 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.3)] p-5">
            <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
            <p className="text-sm text-slate-400 font-body">
              Abre una OT, arma la lista de repuestos, espera la aprobación del cliente y pasa a
              ejecución. Puedes delegar a un mecánico junior — sus OTs aparecen con indicador
              "En ejecución por junior". El cobro y la liberación del vehículo son el paso final.
              Máximo 4 taps para registrar un consumo de repuesto.
            </p>
          </section>
        </main>
      </div>
    </div>
  )
}

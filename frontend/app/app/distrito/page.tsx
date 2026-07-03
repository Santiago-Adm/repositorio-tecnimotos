'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'

interface ItemLista {
  repuestoId: string
  codigo: string
  nombre: string
  cantidad: number
  precioReferencia: string
}

interface ListaCreada {
  lista_id: string
  estado: string
  total_items: number
}

export default function ClienteDistritoDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [seccion, setSeccion] = useState<'Mi lista activa' | 'Mis pedidos'>('Mi lista activa')

  const [codigoBusqueda, setCodigoBusqueda] = useState('')
  const [buscando, setBuscando] = useState(false)
  const [errorBusqueda, setErrorBusqueda] = useState<string | null>(null)
  const [items, setItems] = useState<ItemLista[]>([])

  const [creando, setCreando] = useState(false)
  const [errorCrear, setErrorCrear] = useState<string | null>(null)
  const [listaActiva, setListaActiva] = useState<ListaCreada | null>(null)

  const [formalizando, setFormalizando] = useState(false)
  const [errorFormalizar, setErrorFormalizar] = useState<string | null>(null)
  const [formalizada, setFormalizada] = useState(false)

  useEffect(() => {
    if (user && user.rol !== 'CLIENTE_DISTRITO') { router.replace('/distrito'); return }
  }, [user, router])

  // EP-CAT-02 — agrega un repuesto a la lista en construcción por código exacto.
  async function agregarItem(e: React.FormEvent) {
    e.preventDefault()
    if (!codigoBusqueda.trim()) return
    setBuscando(true)
    setErrorBusqueda(null)
    try {
      const r = await apiClient.get<{ id: string; codigo: string; nombre: string }>(
        `/v1/repuestos/${encodeURIComponent(codigoBusqueda.trim())}`,
      )
      if (items.some(i => i.codigo === r.codigo)) {
        setErrorBusqueda('Ese repuesto ya está en tu lista.')
        return
      }
      setItems(prev => [...prev, { repuestoId: r.id, codigo: r.codigo, nombre: r.nombre, cantidad: 1, precioReferencia: '' }])
      setCodigoBusqueda('')
    } catch (err) {
      setErrorBusqueda((err as ApiCallError).code === 'REPUESTO_NO_ENCONTRADO' ? 'Código no encontrado.' : 'No se pudo buscar el repuesto.')
    } finally {
      setBuscando(false)
    }
  }

  function actualizarItem(codigo: string, campo: 'cantidad' | 'precioReferencia', valor: string) {
    setItems(prev => prev.map(i => i.codigo === codigo ? { ...i, [campo]: campo === 'cantidad' ? Number(valor) : valor } : i))
  }

  function quitarItem(codigo: string) {
    setItems(prev => prev.filter(i => i.codigo !== codigo))
  }

  // EP-PED-13 — crea la lista de reserva progresiva con los items armados.
  async function crearLista() {
    if (!user || items.length === 0) return
    setCreando(true)
    setErrorCrear(null)
    try {
      const data = await apiClient.post<ListaCreada>('/v1/lista-reserva-progresiva', {
        cliente_id: user.id,
        items: items.map(i => ({
          repuesto_id: i.repuestoId,
          codigo: i.codigo,
          cantidad: i.cantidad,
          precio_referencia: Number(i.precioReferencia),
        })),
      })
      setListaActiva(data)
      setItems([])
    } catch (err) {
      setErrorCrear(err instanceof ApiCallError ? err.message : 'No se pudo crear la lista.')
    } finally {
      setCreando(false)
    }
  }

  // EP-PED-14 — formaliza la lista ya creada (crea pedido en BORRADOR).
  async function formalizar() {
    if (!listaActiva) return
    setFormalizando(true)
    setErrorFormalizar(null)
    try {
      await apiClient.post(`/v1/lista-reserva-progresiva/${listaActiva.lista_id}/formalizar`)
      setFormalizada(true)
    } catch (err) {
      setErrorFormalizar(err instanceof ApiCallError ? err.message : 'No se pudo formalizar la lista.')
    } finally {
      setFormalizando(false)
    }
  }

  const itemsListos = items.length > 0 && items.every(i => i.cantidad > 0 && Number(i.precioReferencia) > 0)

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="CLIENTE_DISTRITO" />
      <DashboardHeader userId={user.id} rol="CLIENTE_DISTRITO" onLogout={logout} />

      <nav className="flex gap-2 px-4 py-3 border-b border-slate-800 overflow-x-auto">
        {(['Mi lista activa', 'Mis pedidos'] as const).map(m => (
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

      {/* Vista por defecto: lista progresiva activa (10 §4.9, 02 §5.3 HU-S2-06) */}
      <main className="p-4 md:p-6 space-y-6 max-w-2xl mx-auto">
        {seccion !== 'Mi lista activa' && (
          <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-8 text-center">
            <p className="text-slate-400 font-body text-sm">
              Sección <span className="text-slate-200 font-mono">{seccion}</span> — disponible próximamente.
            </p>
          </section>
        )}

        {seccion === 'Mi lista activa' && (
          <section>
            <h2 className="font-display text-lg font-semibold text-slate-100 mb-4">Mi lista de repuestos</h2>

            {listaActiva ? (
              <div className="rounded-xl bg-slate-800 border border-slate-700 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-mono text-slate-200">{listaActiva.lista_id}</p>
                  <span className="text-xs px-2 py-1 rounded-full font-body bg-teal/20 text-teal">
                    {formalizada ? 'FORMALIZADA' : listaActiva.estado}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-body">{listaActiva.total_items} repuestos en la lista.</p>
                {!formalizada ? (
                  <button
                    onClick={formalizar}
                    disabled={formalizando}
                    className="w-full py-2.5 rounded-xl bg-teal text-white text-sm font-body font-semibold hover:bg-teal/90 disabled:opacity-50 transition-colors"
                  >
                    {formalizando ? 'Formalizando...' : 'Formalizar lista'}
                  </button>
                ) : (
                  <p className="text-xs text-teal font-body">
                    Lista formalizada — se creó tu pedido en estado BORRADOR. El equipo revisará precios y disponibilidad.
                  </p>
                )}
                {errorFormalizar && <ErrorDisplay code="ERROR_INTERNO" context={errorFormalizar} onRetry={formalizar} />}
                {!formalizada && (
                  <button
                    onClick={() => setListaActiva(null)}
                    className="w-full py-2 text-xs text-slate-400 hover:text-slate-200 font-body"
                  >
                    Armar una lista nueva
                  </button>
                )}
              </div>
            ) : (
              <>
                <form onSubmit={agregarItem} className="flex gap-2 mb-4">
                  <input
                    type="text"
                    placeholder="Código de repuesto (ej. BAJ-4592)"
                    value={codigoBusqueda}
                    onChange={e => setCodigoBusqueda(e.target.value)}
                    className="flex-1 px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-teal"
                  />
                  <button
                    type="submit"
                    disabled={buscando}
                    className="px-4 py-2.5 rounded-xl bg-teal text-white text-sm font-body hover:bg-teal/90 disabled:opacity-50 transition-colors"
                  >
                    {buscando ? 'Buscando...' : 'Agregar'}
                  </button>
                </form>
                {errorBusqueda && <p className="text-xs text-red-400 font-body mb-4">{errorBusqueda}</p>}

                {items.length === 0 ? (
                  <p className="text-sm text-slate-500 font-body py-6 text-center">
                    Agrega repuestos por código para armar tu lista. Arma tu pedido completo de una sola vez.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {items.map(i => (
                      <div key={i.codigo} className="rounded-xl bg-slate-800 border border-slate-700 p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <p className="text-sm font-mono text-slate-200">{i.codigo}</p>
                            <p className="text-xs text-slate-400 font-body">{i.nombre}</p>
                          </div>
                          <button onClick={() => quitarItem(i.codigo)} className="text-xs text-red-400 hover:underline font-body">
                            Quitar
                          </button>
                        </div>
                        <div className="flex gap-3">
                          <label className="flex-1 text-xs font-body text-slate-400">
                            Cantidad
                            <input
                              type="number"
                              min={1}
                              value={i.cantidad}
                              onChange={e => actualizarItem(i.codigo, 'cantidad', e.target.value)}
                              className="w-full mt-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-sm font-mono"
                            />
                          </label>
                          <label className="flex-1 text-xs font-body text-slate-400">
                            Precio referencial (S/)
                            <input
                              type="number"
                              min={0}
                              step="0.01"
                              value={i.precioReferencia}
                              onChange={e => actualizarItem(i.codigo, 'precioReferencia', e.target.value)}
                              className="w-full mt-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-sm font-mono"
                            />
                          </label>
                        </div>
                      </div>
                    ))}

                    {errorCrear && <p className="text-xs text-red-400 font-body">{errorCrear}</p>}

                    <button
                      onClick={crearLista}
                      disabled={!itemsListos || creando}
                      className="w-full py-2.5 rounded-xl bg-teal text-white text-sm font-body font-semibold hover:bg-teal/90 disabled:opacity-50 transition-colors"
                    >
                      {creando ? 'Creando lista...' : 'Crear lista'}
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        )}

        <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-5">
          <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
          <p className="text-sm text-slate-400 font-body">
            Arma tu lista completa de repuestos de una sola vez y formalízala. El equipo revisa
            precios y disponibilidad. Recibirás la proforma final con precio confirmado una vez
            que el administrador apruebe.
          </p>
        </section>
      </main>
    </div>
  )
}

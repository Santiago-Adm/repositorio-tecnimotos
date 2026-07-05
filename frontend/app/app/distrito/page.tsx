'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import EmptyState from '@/src/components/EmptyState'
import PedidoCard from '@/src/components/PedidoCard'
import CatalogoNavegable from '@/src/components/dashboard/CatalogoNavegable'
import { usePedidos } from '@/src/lib/usePedidos'
import DistritoResumenTab from '@/src/components/dashboard/DistritoResumenTab'
import { RepuestoListItem } from '@/src/lib/types'
import AppSidebarNav from '@/src/components/dashboard/AppSidebarNav'

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
  const [seccion, setSeccion] = useState<'Resumen' | 'Mi lista activa' | 'Mis pedidos'>('Resumen')

  const [codigoBusqueda, setCodigoBusqueda] = useState('')
  const [buscando, setBuscando] = useState(false)
  const [errorBusqueda, setErrorBusqueda] = useState<string | null>(null)
  const [items, setItems] = useState<ItemLista[]>([])
  const [modoArmado, setModoArmado] = useState<'catalogo' | 'codigo'>('catalogo')

  const [creando, setCreando] = useState(false)
  const [errorCrear, setErrorCrear] = useState<string | null>(null)
  const [listaActiva, setListaActiva] = useState<ListaCreada | null>(null)

  const [formalizando, setFormalizando] = useState(false)
  const [errorFormalizar, setErrorFormalizar] = useState<string | null>(null)
  const [formalizada, setFormalizada] = useState(false)

  // EP-PED-02 — el backend resuelve el cliente_id real del usuario autenticado
  // (tabla `cliente`); CLIENTE_DISTRITO solo ve sus propios pedidos.
  const { pedidos, loading: loadingPed, error: errorPed, fetchPedidos } = usePedidos()

  useEffect(() => {
    if (user && user.rol !== 'CLIENTE_DISTRITO') { router.replace('/distrito'); return }
    if (user && seccion === 'Mis pedidos' && pedidos === null) fetchPedidos()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, router, seccion])

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

  // Pieza D — agrega un repuesto a la lista navegando el catálogo estructurado
  // (universo → modelo → categoría), en vez de solo por código manual.
  function agregarDesdeCatalogo(r: RepuestoListItem) {
    if (items.some(i => i.codigo === r.codigo)) return
    setItems(prev => [...prev, { repuestoId: r.id, codigo: r.codigo, nombre: r.nombre, cantidad: 1, precioReferencia: '' }])
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

      <div className="flex flex-col md:flex-row">
        <AppSidebarNav
          surface="light"
          secciones={['Resumen', 'Mi lista activa', 'Mis pedidos']}
          activa={seccion}
          onSeleccionar={s => setSeccion(s as typeof seccion)}
        />

      {/* Vista por defecto: lista progresiva activa (10 §4.9, 02 §5.3 HU-S2-06) */}
      <main className={`flex-1 min-w-0 w-full p-4 md:p-6 space-y-6 ${
        seccion === 'Mi lista activa' && modoArmado === 'catalogo' ? 'max-w-6xl mx-auto' : 'max-w-2xl mx-auto'
      }`}>
        {seccion === 'Resumen' && <DistritoResumenTab />}

        {seccion === 'Mis pedidos' && (
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-display text-lg font-semibold text-slate-100">Mis pedidos</h2>
              <button onClick={fetchPedidos} className="text-xs text-teal font-body hover:underline">Actualizar</button>
            </div>
            {loadingPed ? (
              <LoadingIndicator message="Cargando pedidos..." />
            ) : errorPed ? (
              <ErrorDisplay code={errorPed} onRetry={fetchPedidos} />
            ) : !pedidos || pedidos.length === 0 ? (
              <EmptyState title="Sin pedidos" description="Todavía no tienes pedidos registrados." />
            ) : (
              <div className="space-y-3">
                {pedidos.map(p => <PedidoCard key={p.pedido_id} pedido={p} />)}
              </div>
            )}
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
                <div className="flex gap-2 mb-4">
                  <button
                    type="button"
                    onClick={() => setModoArmado('catalogo')}
                    className={`px-3 py-1.5 rounded-full text-xs font-body transition-colors border ${
                      modoArmado === 'catalogo' ? 'bg-teal border-teal text-white font-semibold' : 'text-slate-300 border-slate-700 hover:bg-slate-800'
                    }`}
                  >
                    Explorar catálogo
                  </button>
                  <button
                    type="button"
                    onClick={() => setModoArmado('codigo')}
                    className={`px-3 py-1.5 rounded-full text-xs font-body transition-colors border ${
                      modoArmado === 'codigo' ? 'bg-teal border-teal text-white font-semibold' : 'text-slate-300 border-slate-700 hover:bg-slate-800'
                    }`}
                  >
                    Por código
                  </button>
                </div>

                {modoArmado === 'catalogo' ? (
                  <div className="mb-6">
                    <CatalogoNavegable
                      surface="light"
                      onAgregar={agregarDesdeCatalogo}
                      codigosAgregados={items.map(i => i.codigo)}
                    />
                  </div>
                ) : (
                  <>
                    <form onSubmit={agregarItem} className="flex gap-2 mb-4">
                      <input
                        type="text"
                        placeholder="Código de repuesto (ej. BAJ-4592)"
                        value={codigoBusqueda}
                        onChange={e => setCodigoBusqueda(e.target.value)}
                        className="flex-1 min-w-0 px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-teal"
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
                  </>
                )}

                {items.length === 0 ? (
                  <p className="text-sm text-slate-500 font-body py-6 text-center">
                    Navega el catálogo o agrega por código para armar tu lista. Arma tu pedido completo de una sola vez.
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
                          <label className="flex-1 min-w-0 text-xs font-body text-slate-400">
                            Cantidad
                            <input
                              type="number"
                              min={1}
                              value={i.cantidad}
                              onChange={e => actualizarItem(i.codigo, 'cantidad', e.target.value)}
                              className="w-full mt-1 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 text-sm font-mono"
                            />
                          </label>
                          <label className="flex-1 min-w-0 text-xs font-body text-slate-400">
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

        <section className="rounded-xl bg-white border border-slate-200 shadow-[0_4px_20px_-8px_rgba(15,23,42,0.06)] p-5">
          <h3 className="font-display text-sm font-semibold text-slate-300 mb-2">Cómo funciona</h3>
          <p className="text-sm text-slate-400 font-body">
            Arma tu lista completa de repuestos de una sola vez y formalízala. El equipo revisa
            precios y disponibilidad. Recibirás la proforma final con precio confirmado una vez
            que el administrador apruebe.
          </p>
        </section>
      </main>
      </div>
    </div>
  )
}

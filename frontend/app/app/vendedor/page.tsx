'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'
import PedidoCard from '@/src/components/PedidoCard'
import CatalogoNavegable from '@/src/components/dashboard/CatalogoNavegable'
import AppSidebarNav from '@/src/components/dashboard/AppSidebarNav'
import { usePedidos } from '@/src/lib/usePedidos'
import VendedorResumenTab from '@/src/components/dashboard/VendedorResumenTab'

type Seccion = 'Resumen' | 'Catálogo' | 'Mis pedidos'

export default function VendedorDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [seccion, setSeccion] = useState<Seccion>('Resumen')
  // EP-PED-02 — VENDEDOR es rol interno: ve todos los pedidos de la tienda,
  // no solo los que él registró (el dominio no rastrea "vendedor_id" por pedido).
  const { pedidos, loading: loadingPed, error: errorPed, fetchPedidos } = usePedidos()

  useEffect(() => {
    if (user && user.rol !== 'VENDEDOR') { router.replace('/login'); return }
    if (user && seccion === 'Mis pedidos' && pedidos === null) fetchPedidos()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, router, seccion])

  if (!user) return null

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100">
      <SessionExpiredHandler rol="VENDEDOR" />
      <DashboardHeader userId={user.id} rol="VENDEDOR" onLogout={logout} />

      <div className="flex flex-col md:flex-row">
        {/* Navegación — catálogo y pedidos (02 §4.1 VENDEDOR). No: modificar
            precio, aplicar descuento, aprobar comprobante, ajuste de stock. */}
        <AppSidebarNav
          secciones={['Resumen', 'Catálogo', 'Mis pedidos']}
          activa={seccion}
          onSeleccionar={s => setSeccion(s as Seccion)}
        />

        <main className="flex-1 min-w-0 p-6 space-y-6">
          {seccion === 'Resumen' && <VendedorResumenTab />}

          {seccion === 'Mis pedidos' && (
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-display text-lg font-semibold text-slate-100">Pedidos de la tienda</h2>
                <button onClick={fetchPedidos} className="text-xs text-teal font-body hover:underline">Actualizar</button>
              </div>
              {loadingPed ? (
                <LoadingIndicator message="Cargando pedidos..." />
              ) : errorPed ? (
                <ErrorDisplay code={errorPed} onRetry={fetchPedidos} />
              ) : !pedidos || pedidos.length === 0 ? (
                <EmptyState title="Sin pedidos" description="Todavía no hay pedidos registrados." />
              ) : (
                <div className="space-y-3">
                  {pedidos.map(p => <PedidoCard key={p.pedido_id} pedido={p} />)}
                </div>
              )}
            </section>
          )}
          {seccion === 'Catálogo' && <section>
            <h2 className="font-display text-lg font-semibold text-slate-100 mb-4">Catálogo</h2>
            {/* precio_costo y margen no visibles para VENDEDOR (02 §4.1) — RepuestoCard
                ya oculta esos campos, aquí solo se navega y se consulta precio bajo demanda. */}
            <CatalogoNavegable />
          </section>}

          <section className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-800/60 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.3)] p-5">
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

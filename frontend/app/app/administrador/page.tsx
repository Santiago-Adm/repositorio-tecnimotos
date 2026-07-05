'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import CategoriasManager from '@/src/components/dashboard/CategoriasManager'
import BiPanel from '@/src/components/dashboard/BiPanel'
import AdministradorResumenTab from '@/src/components/dashboard/AdministradorResumenTab'
import CatalogoAdminTab from '@/src/components/dashboard/CatalogoAdminTab'
import UsuariosManager from '@/src/components/dashboard/UsuariosManager'
import AppSidebarNav from '@/src/components/dashboard/AppSidebarNav'
import CatalogoNavegable, { StockInfo } from '@/src/components/dashboard/CatalogoNavegable'
import EditarStockModal from '@/src/components/dashboard/EditarStockModal'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'
import { RepuestoListItem } from '@/src/lib/types'

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

type Seccion = 'Resumen' | 'Panel BI' | 'Stock' | 'Catálogo' | 'Categorías' | 'Pedidos' | 'Taller' | 'Admin'

export default function AdministradorDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [seccion, setSeccion] = useState<Seccion>('Resumen')
  const [stock, setStock] = useState<StockItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editandoStock, setEditandoStock] = useState<{ repuesto: RepuestoListItem; stock: StockInfo | null } | null>(null)
  const [versionStock, setVersionStock] = useState(0)

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

      <div className="flex flex-col md:flex-row">
        {/* Navegación — 02 §4.1 ADMINISTRADOR (Pieza F: sidebar+drawer compartido) */}
        <AppSidebarNav
          secciones={['Resumen', 'Panel BI', 'Stock', 'Catálogo', 'Categorías', 'Pedidos', 'Taller', 'Admin']}
          activa={seccion}
          onSeleccionar={s => setSeccion(s as Seccion)}
        />

        <main className="flex-1 min-w-0 p-6 space-y-6">
          {seccion !== 'Stock' && seccion !== 'Categorías' && seccion !== 'Panel BI' && seccion !== 'Admin' && seccion !== 'Resumen' && seccion !== 'Catálogo' && (
            <section className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-800/60 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.3)] p-8 text-center">
              <p className="text-slate-400 font-body text-sm">
                Sección <span className="text-slate-200 font-mono">{seccion}</span> — disponible próximamente.
              </p>
            </section>
          )}

          {seccion === 'Resumen' && <AdministradorResumenTab />}

          {seccion === 'Panel BI' && <BiPanel />}

          {seccion === 'Catálogo' && <CatalogoAdminTab />}

          {seccion === 'Categorías' && <CategoriasManager />}

          {seccion === 'Admin' && (
            <section>
              <h2 className="font-display text-lg font-semibold text-slate-100 mb-4">Gestión de usuarios</h2>
              <UsuariosManager />
            </section>
          )}

          {seccion === 'Stock' && alertas.length > 0 && (
            <section>
              <h2 className="font-display text-base font-semibold text-electric mb-3 flex items-center gap-2">
                {/* MASTER.md — patrón Real-Time Monitoring del Skill: la
                    alerta se percibe viva, no un dato estático más. */}
                <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-electric opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-electric" />
                </span>
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
            </div>
            {/* Pieza 2 — antes tabla plana con los 16 195 repuestos sin
                filtrar; ahora reutiliza la navegación universo→modelo→
                categoría de Catálogo, consultando stock solo de lo visible. */}
            <CatalogoNavegable
              key={versionStock}
              modoStock
              onEditarStock={(repuesto, stockInfo) => setEditandoStock({ repuesto, stock: stockInfo })}
            />
          </section>}

          {editandoStock && (
            <EditarStockModal
              repuesto={editandoStock.repuesto}
              stock={editandoStock.stock}
              onCerrar={() => setEditandoStock(null)}
              onGuardado={() => { setEditandoStock(null); setVersionStock(v => v + 1) }}
            />
          )}

          <section className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-800/60 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.3)] p-5">
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

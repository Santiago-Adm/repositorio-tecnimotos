'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'

interface StockItem {
  codigo: string
  cantidad_disponible: number
  cantidad_apartada: number
  umbral_minimo: number
  esta_bajo_umbral: boolean
}

/**
 * Control de stock con polling silencioso cada 30s — extraído de
 * superadmin/page.tsx (990 líneas, sección "Stock" era inline con estado
 * sin tipar `any[]`).
 */
export default function StockConsultaTab() {
  const [items, setItems] = useState<StockItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function fetchStock(silencioso = false) {
    if (!silencioso) setLoading(true)
    setError(null)
    try {
      const data = await apiClient.get<{ stocks: StockItem[]; total: number }>('/v1/stock')
      setItems(data.stocks ?? [])
    } catch (err) {
      if (!silencioso) setError((err as ApiCallError).code)
    } finally {
      if (!silencioso) setLoading(false)
    }
  }

  useEffect(() => {
    fetchStock()
    const intervalo = setInterval(() => fetchStock(true), 30000)
    return () => clearInterval(intervalo)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-100">Control de Stock</h1>
        <p className="text-sm text-slate-400 font-body">Estado actual de inventario y alertas por debajo del umbral.</p>
      </div>

      {loading ? (
        <LoadingIndicator message="Cargando existencias..." />
      ) : error ? (
        <ErrorDisplay code={error} onRetry={() => fetchStock()} />
      ) : items.length === 0 ? (
        <EmptyState title="Sin registros de stock" description="Registra repuestos en el catálogo para ver niveles de stock." />
      ) : (
        <div className="space-y-6">
          {items.some(s => s.esta_bajo_umbral) && (
            <div className="space-y-2">
              <h2 className="text-sm font-semibold text-red-400 font-body">Alertas Críticas de Stock</h2>
              <div className="rounded-xl border border-red-500/25 bg-red-950/5 overflow-hidden divide-y divide-slate-800">
                {items.filter(s => s.esta_bajo_umbral).map(s => (
                  <div key={s.codigo} className="flex justify-between items-center px-4 py-3">
                    <span className="font-mono text-sm text-slate-200">{s.codigo}</span>
                    <div className="text-right">
                      <span className="text-sm font-mono text-red-400 font-semibold">{s.cantidad_disponible} unidades</span>
                      <p className="text-[10px] text-slate-500 font-body">mínimo: {s.umbral_minimo}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-2">
            <h2 className="text-sm font-semibold text-slate-300 font-body">Inventario General</h2>
            <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-855">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-800 text-slate-400 font-body border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Código</th>
                    <th className="px-4 py-3 font-semibold text-right">Disponible</th>
                    <th className="px-4 py-3 font-semibold text-right">Apartada</th>
                    <th className="px-4 py-3 font-semibold text-right">Umbral Mínimo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {items.map(s => (
                    <tr key={s.codigo} className={`hover:bg-slate-800/30 ${s.esta_bajo_umbral ? 'bg-red-500/5' : ''}`}>
                      <td className="px-4 py-2.5 font-mono text-slate-200">{s.codigo}</td>
                      <td className="px-4 py-2.5 text-right font-mono font-semibold text-slate-200">{s.cantidad_disponible}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-slate-400">{s.cantidad_apartada}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-slate-400">{s.umbral_minimo}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

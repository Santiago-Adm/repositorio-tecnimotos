'use client'

import { FormEvent, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { useAuth } from '@/src/context/AuthContext'
import { ApiCallError } from '@/src/lib/types'
import { RepuestoListItem } from '@/src/lib/types'
import { StockInfo } from './CatalogoNavegable'

interface Props {
  repuesto: RepuestoListItem
  stock: StockInfo | null
  onCerrar: () => void
  onGuardado: () => void
}

/**
 * Pieza 2.C (fusión Stock↔Catálogo) — EP-STK-04 (ajuste) recibe un DELTA,
 * no un valor absoluto (confirmado en `ajustar_stock.py`: cantidad>0 entrada,
 * <0 salida). Esta UI pide la cantidad disponible deseada (absoluta, más
 * natural para editar) y calcula el delta antes de enviarlo. El umbral
 * mínimo sí se edita aquí (EP-STK-05) — es el umbral de alerta de stock por
 * repuesto, sin relación con el umbral de días de ADR-015 (ese es de OT).
 */
export default function EditarStockModal({ repuesto, stock, onCerrar, onGuardado }: Props) {
  const { user } = useAuth()
  const [cantidad, setCantidad] = useState(String(stock?.cantidad_disponible ?? 0))
  const [umbral, setUmbral] = useState(String(stock?.umbral_minimo ?? 0))
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function guardar(e: FormEvent) {
    e.preventDefault()
    if (!user) return
    setGuardando(true)
    setError(null)
    try {
      const nuevaCantidad = Number(cantidad)
      const nuevoUmbral = Number(umbral)
      const delta = nuevaCantidad - (stock?.cantidad_disponible ?? 0)

      if (delta !== 0) {
        await apiClient.post(`/v1/stock/${repuesto.codigo}/ajuste`, {
          cantidad: delta,
          actor_id: user.id,
          motivo: 'Ajuste manual — panel de Stock',
        })
      }
      if (nuevoUmbral !== (stock?.umbral_minimo ?? 0)) {
        await apiClient.patch(`/v1/stock/${repuesto.codigo}/umbral`, {
          umbral_minimo: nuevoUmbral,
          actor_id: user.id,
        })
      }
      onGuardado()
    } catch (err) {
      setError(err instanceof ApiCallError ? err.message : 'No se pudo guardar el stock.')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" onClick={onCerrar}>
      <div
        className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-display text-lg font-bold text-slate-100">Editar stock</h3>
            <p className="text-xs text-slate-500 font-mono">{repuesto.codigo} · {repuesto.nombre}</p>
          </div>
          <button
            type="button"
            onClick={onCerrar}
            aria-label="Cerrar"
            className="w-9 h-9 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            ✕
          </button>
        </div>

        {!stock && (
          <p className="text-xs text-electric bg-electric/10 border border-electric/30 rounded-lg px-3 py-2">
            Este repuesto no tiene registro de stock — se creará uno nuevo al guardar.
          </p>
        )}

        <form onSubmit={guardar} className="space-y-4">
          <div>
            <label htmlFor="cantidad" className="block text-xs font-semibold text-slate-400 mb-1">Cantidad disponible</label>
            <input
              id="cantidad"
              type="number"
              min={0}
              value={cantidad}
              onChange={e => setCantidad(e.target.value)}
              required
              className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-teal"
            />
          </div>

          <div>
            <label htmlFor="umbral" className="block text-xs font-semibold text-slate-400 mb-1">Umbral mínimo (alerta de stock bajo)</label>
            <input
              id="umbral"
              type="number"
              min={0}
              value={umbral}
              onChange={e => setUmbral(e.target.value)}
              required
              className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-teal"
            />
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onCerrar}
              className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={guardando}
              className="px-4 py-2 rounded-lg bg-teal text-white text-sm font-semibold hover:bg-teal/90 transition-colors disabled:opacity-50"
            >
              {guardando ? 'Guardando...' : 'Guardar cambios'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import PedidoCard, { Pedido } from '@/src/components/PedidoCard'

/**
 * Bandeja de todos los pedidos del negocio (rol interno, sin scoping por
 * cliente) — extraído de superadmin/page.tsx (990 líneas, sección "Pedidos"
 * era inline con estado sin tipar `any[]`). Reutiliza `PedidoCard`, el mismo
 * componente ya usado en VENDEDOR/CLIENTE_DISTRITO/CLIENTE_CONDUCTOR.
 */
export default function PedidosBandejaTab() {
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function fetchPedidos() {
    setLoading(true)
    setError(null)
    try {
      const data = await apiClient.get<{ pedidos: Pedido[]; total: number }>('/v1/pedidos')
      setPedidos(data.pedidos ?? [])
    } catch (err) {
      setError((err as ApiCallError).code)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPedidos()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-100">Bandeja de Pedidos</h1>
          <p className="text-sm text-slate-400 font-body">Monitoreo de pedidos y transiciones de compra.</p>
        </div>
        <button onClick={fetchPedidos} className="text-xs text-teal font-body hover:underline">Actualizar</button>
      </div>

      {loading ? (
        <LoadingIndicator message="Recuperando pedidos..." />
      ) : error ? (
        <ErrorDisplay code={error} onRetry={fetchPedidos} />
      ) : pedidos.length === 0 ? (
        <EmptyState title="Sin pedidos" description="No hay pedidos registrados en el sistema." />
      ) : (
        <div className="space-y-3">
          {pedidos.map(p => <PedidoCard key={p.pedido_id} pedido={p} />)}
        </div>
      )}
    </div>
  )
}

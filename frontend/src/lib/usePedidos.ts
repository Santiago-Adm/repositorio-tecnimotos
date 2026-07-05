import { useState } from 'react'
import { apiClient } from './api-client'
import { ApiCallError } from './types'
import { Pedido } from '@/src/components/PedidoCard'

/**
 * Fetch de `GET /v1/pedidos` con estado de carga/error — el backend ya
 * resuelve el scoping (rol interno ve todos, CLIENTE_* solo los propios).
 * Extraído de vendedor/distrito/conductor page.tsx, que duplicaban
 * exactamente este mismo estado y la misma función.
 */
export function usePedidos() {
  const [pedidos, setPedidos] = useState<Pedido[] | null>(null)
  const [loading, setLoading] = useState(false)
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

  return { pedidos, loading, error, fetchPedidos }
}

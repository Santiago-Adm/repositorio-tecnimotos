import { useEffect, useState } from 'react'
import { apiClient } from './api-client'
import { Universo } from './useCatalogoNavegable'

export interface MiVehiculo {
  vehiculo_id: string
  universo: Universo
  modelo: string
  año: number | null
  placa: string | null
}

/**
 * GET /v1/mis-vehiculos (EP-TAL-16, Pieza C) — resuelve el vehículo del
 * cliente autenticado para auto-filtrar el catálogo. Si el cliente no tiene
 * vehículo registrado, `vehiculo` queda null y el consumidor debe mostrar
 * el catálogo completo sin filtro (no bloquear la navegación).
 */
export function useMiVehiculo() {
  const [vehiculo, setVehiculo] = useState<MiVehiculo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let activo = true
    apiClient.get<{ vehiculos: MiVehiculo[] }>('/v1/mis-vehiculos')
      .then(data => { if (activo) setVehiculo(data.vehiculos[0] ?? null) })
      .catch(() => { if (activo) setVehiculo(null) })
      .finally(() => { if (activo) setLoading(false) })
    return () => { activo = false }
  }, [])

  return { vehiculo, loading }
}

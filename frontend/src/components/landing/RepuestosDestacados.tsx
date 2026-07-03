'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import RepuestoCard from '@/src/components/RepuestoCard'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'

interface Repuesto {
  id: string
  codigo: string
  nombre: string
  modelo: string
  activo: boolean
  imagen_principal_url?: string | null
}

const MAX_ITEMS = 6

interface Props {
  universo: 'mototaxi' | 'motolineal'
  /** Payload mínimo S4/rural (10 §2.3/§6.6) — sin imagen, sin consulta de precio. */
  minimal?: boolean
}

// EP-CAT-01 — sin auth, universo obligatorio (verificado contra api/routes/catalogo.py).
export default function RepuestosDestacados({ universo, minimal = false }: Props) {
  const [repuestos, setRepuestos] = useState<Repuesto[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function cargar() {
    setError(null)
    setRepuestos(null)
    try {
      const data = await apiClient.get<{ repuestos: Repuesto[] }>(`/v1/repuestos?universo=${universo}`)
      setRepuestos(data.repuestos.slice(0, MAX_ITEMS))
    } catch (err) {
      setError(err instanceof ApiCallError ? err.code : 'ERROR_INTERNO')
    }
  }

  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [universo])

  if (error) return <ErrorDisplay code={error} onRetry={cargar} context="repuestos destacados" />
  if (repuestos === null) return <LoadingIndicator message="Cargando repuestos disponibles..." />
  if (repuestos.length === 0) return null

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {repuestos.map(r => (
        <RepuestoCard
          key={r.codigo}
          variant="grid"
          surface="light"
          minimal={minimal}
          repuestoId={r.id}
          codigo={r.codigo}
          nombre={r.nombre}
          modelo={r.modelo}
          disponible={r.activo}
          imagenUrl={minimal ? null : r.imagen_principal_url}
        />
      ))}
    </div>
  )
}

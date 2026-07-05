import { useEffect, useState } from 'react'
import { apiClient } from './api-client'
import { ApiCallError, RepuestoListItem } from './types'

export type Universo = 'mototaxi_3r' | 'mototaxi_4r' | 'motolineal'

export const UNIVERSOS_VALIDOS: Universo[] = ['mototaxi_3r', 'mototaxi_4r', 'motolineal']

// Jerarquía real confirmada (2R=motolineal, 3R=mototaxi_3r, 4R=mototaxi_4r) —
// mismo criterio ya validado en frontend/app/catalogo/page.tsx.
export const UNIVERSO_LABEL: Record<Universo, string> = {
  mototaxi_3r: '3R',
  mototaxi_4r: '4R',
  motolineal: '2R',
}

interface Opciones {
  universoInicial?: Universo
  /** Si se pasa, el universo queda fijo (Pieza C: catálogo filtrado por el
   *  vehículo del cliente) — el consumidor no debe mostrar el selector. */
  universoFijo?: Universo
  pageSize?: number
}

/**
 * Motor de navegación universo → modelo → categoría con paginación
 * server-side real (EP-CAT-01 + EP-CAT-17) — extraído de la lógica ya
 * probada en /catalogo (pública) para que Administrador, Vendedor,
 * Mecánico Máster, Conductor/Rural y Distrito compartan una sola
 * implementación en vez de duplicar el mismo fetch con un universo
 * hardcodeado (bug real: antes solo se veía mototaxi_3r, 28% del catálogo).
 */
export function useCatalogoNavegable({ universoInicial = 'mototaxi_3r', universoFijo, pageSize = 12 }: Opciones = {}) {
  const [universo, setUniversoState] = useState<Universo>(universoFijo ?? universoInicial)
  const [modelo, setModelo] = useState('')
  const [categoria, setCategoria] = useState('')
  const [page, setPage] = useState(1)

  const [repuestos, setRepuestos] = useState<RepuestoListItem[] | null>(null)
  const [total, setTotal] = useState(0)
  const [totalPaginas, setTotalPaginas] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [modelosDisponibles, setModelosDisponibles] = useState<string[]>([])

  function setUniverso(u: Universo) {
    if (universoFijo) return
    setUniversoState(u)
  }

  useEffect(() => {
    apiClient.get<{ modelos: string[] }>(`/v1/repuestos/modelos?universo=${universo}`)
      .then(data => setModelosDisponibles(data.modelos))
      .catch(() => setModelosDisponibles([]))
  }, [universo])

  useEffect(() => {
    setPage(1)
  }, [universo, modelo, categoria])

  async function cargar() {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ universo, page: String(page), limit: String(pageSize) })
      if (modelo) params.set('modelo', modelo)
      if (categoria) params.set('categoria', categoria)
      const data = await apiClient.get<{ repuestos: RepuestoListItem[]; total: number; total_paginas: number }>(
        `/v1/repuestos?${params.toString()}`,
      )
      setRepuestos(data.repuestos)
      setTotal(data.total)
      setTotalPaginas(Math.max(1, data.total_paginas))
    } catch (err) {
      setError(err instanceof ApiCallError ? err.code : 'ERROR_INTERNO')
      setRepuestos([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [universo, modelo, categoria, page])

  return {
    universo, setUniverso, modelo, setModelo, categoria, setCategoria,
    page, setPage, repuestos, total, totalPaginas, loading, error,
    modelosDisponibles, recargar: cargar, universoBloqueado: !!universoFijo,
  }
}

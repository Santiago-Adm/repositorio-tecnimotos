import { apiClient } from './api-client'

const CONSULTAS_KEY = 'tm_consultas_precio'

interface ConsultasHoy {
  fecha: string
  cantidad: number
}

// Reset 05:00 UTC (03 — tabla de rate limit, EP-CAT-02-B)
function fechaReferencia(): string {
  const ref = new Date()
  if (ref.getUTCHours() < 5) ref.setUTCDate(ref.getUTCDate() - 1)
  return ref.toISOString().slice(0, 10)
}

function getConsultasRealizadas(): number {
  if (typeof window === 'undefined') return 0
  try {
    const raw = localStorage.getItem(CONSULTAS_KEY)
    if (!raw) return 0
    const data = JSON.parse(raw) as ConsultasHoy
    return data.fecha === fechaReferencia() ? data.cantidad : 0
  } catch {
    return 0
  }
}

function registrarConsulta(): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(
    CONSULTAS_KEY,
    JSON.stringify({ fecha: fechaReferencia(), cantidad: getConsultasRealizadas() + 1 }),
  )
}

export interface PrecioResult {
  repuesto_id: string
  codigo: string
  precio_venta: number | null
  precio_visible: boolean
  precio_limite_alcanzado: boolean
  mensaje: string | null
  disponible: boolean
  opcion_notificacion: boolean
}

// EP-CAT-02-B — solo se llama para usuarios autenticados (precio_visible es regla de
// negocio en backend, pero la gate principal de "nunca mostrar a visitantes" es de UI).
// esCliente=true aplica el cupo diario de consultas (CLIENTE_*); false = rol interno, sin cupo.
export async function consultarPrecio(codigo: string, esCliente: boolean): Promise<PrecioResult> {
  const nivelVisibilidad = esCliente ? 1 : 0
  const consultasRealizadas = esCliente ? getConsultasRealizadas() : 0
  const params = new URLSearchParams({
    nivel_visibilidad: String(nivelVisibilidad),
    consultas_realizadas: String(consultasRealizadas),
  })
  const result = await apiClient.get<PrecioResult>(
    `/v1/repuestos/${encodeURIComponent(codigo)}/precio?${params.toString()}`,
  )
  if (esCliente) registrarConsulta()
  return result
}

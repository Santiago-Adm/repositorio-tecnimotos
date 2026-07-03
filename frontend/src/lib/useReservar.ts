'use client'

import { useCallback, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'

export const PENDING_RESERVA_KEY = 'tm_pending_reserva'

const SEGMENTOS = ['conductor', 'distrito', 'rural'] as const

function segmentoDeRuta(pathname: string): (typeof SEGMENTOS)[number] {
  return SEGMENTOS.find(s => pathname.startsWith(`/${s}`)) ?? 'conductor'
}

interface ReservaConfirmada {
  reserva_id: string
  codigo: string
  expira_en: string
}

// Regla 2.2 — sin sesión, navega a la landing de segmento con intención (nunca llama
// EP-PED-06 sin auth, evita el 401 silencioso). Con sesión, reserva directo.
export function useReservar() {
  const { user } = useAuth()
  const router = useRouter()
  const pathname = usePathname()
  const [reservandoCodigo, setReservandoCodigo] = useState<string | null>(null)
  const [confirmacion, setConfirmacion] = useState<ReservaConfirmada | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reservar = useCallback(
    async (repuestoId: string, codigo: string) => {
      if (!user) {
        const segmento = segmentoDeRuta(pathname)
        router.push(`/${segmento}?intent=reservar&codigo=${encodeURIComponent(codigo)}`)
        return
      }

      setReservandoCodigo(codigo)
      setError(null)
      try {
        const data = await apiClient.post<{ reserva_id: string; expira_en: string }>('/v1/reservas', {
          cliente_id: user.id,
          repuesto_id: repuestoId,
          cantidad: 1,
          segmento: user.rol,
        })
        setConfirmacion({ reserva_id: data.reserva_id, codigo, expira_en: data.expira_en })
      } catch (err) {
        setError(err instanceof ApiCallError ? err.message : 'No se pudo reservar. Intenta de nuevo.')
      } finally {
        setReservandoCodigo(null)
      }
    },
    [user, pathname, router],
  )

  return {
    reservar,
    reservandoCodigo,
    confirmacion,
    error,
    clearConfirmacion: () => setConfirmacion(null),
  }
}

'use client'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import { PENDING_RESERVA_KEY } from '@/src/lib/useReservar'

function IntentBannerContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()
  const [codigo, setCodigo] = useState<string | null>(null)

  useEffect(() => {
    const intent = searchParams.get('intent')
    const cod = searchParams.get('codigo')
    if (intent === 'reservar' && cod) {
      localStorage.setItem(PENDING_RESERVA_KEY, cod)
      setCodigo(cod)
      router.replace(pathname)
    }
  }, [searchParams, pathname, router])

  if (!codigo) return null

  return (
    <div className="bg-electric/10 border-b border-electric/30 px-6 py-3 text-center">
      <p className="text-sm font-body text-slate-700">
        Para reservar <span className="font-mono font-bold">{codigo}</span>, ingresa o crea tu cuenta —
        retomamos tu reserva apenas inicies sesión.
      </p>
    </div>
  )
}

// Regla 2.2 — consume ?intent=reservar&codigo=XXX dejado por un click en "Reservar"
// sin sesión, lo persiste para retomarlo tras login/registro, y limpia la URL.
// useSearchParams exige límite de Suspense (Next 14 app router) — se envuelve aquí
// para que las páginas que lo usan no tengan que preocuparse por eso.
export default function IntentBanner() {
  return (
    <Suspense fallback={null}>
      <IntentBannerContent />
    </Suspense>
  )
}

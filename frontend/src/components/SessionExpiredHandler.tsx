'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { isClienteRol, rolToLanding, Rol } from '@/src/lib/types'
import { clearStoredToken } from '@/src/lib/api-client'

interface Props {
  rol?: Rol
}

export default function SessionExpiredHandler({ rol }: Props) {
  const [expired, setExpired] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const handler = () => setExpired(true)
    window.addEventListener('tm:session-expired', handler)
    return () => window.removeEventListener('tm:session-expired', handler)
  }, [])

  function handleReauth() {
    clearStoredToken()
    const dest = rol && isClienteRol(rol) ? rolToLanding(rol) : '/login'
    router.replace(dest)
  }

  if (!expired) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-slate-800 border border-slate-700 p-6 shadow-2xl text-center">
        <p className="font-display text-base font-semibold text-slate-100 mb-2">
          Sesión terminada
        </p>
        <p className="font-body text-sm text-slate-300 mb-6">
          Tu sesión terminó por seguridad. Ingresa de nuevo para continuar.
        </p>
        <button
          onClick={handleReauth}
          className="w-full px-4 py-2 rounded-lg bg-teal text-white text-sm font-body hover:bg-teal/90 transition-colors"
        >
          Ingresar de nuevo
        </button>
      </div>
    </div>
  )
}

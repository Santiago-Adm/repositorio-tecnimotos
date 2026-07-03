'use client'

import { Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import RegistroForm from '@/src/components/RegistroForm'
import { LogoSanti } from '@/src/components/ui/LogoSanti'

function RegistroContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Captura de dónde viene el usuario o fallback al historial
  const fromRoute = searchParams.get('from')
  const defaultVolver = '/distrito'

  const handleVolver = () => {
    if (fromRoute) {
      router.push(fromRoute)
    } else {
      router.push(defaultVolver)
    }
  }

  return (
    <div className="min-h-screen bg-[#0F172A] flex flex-col items-center justify-center px-4 py-12 relative overflow-y-auto select-none">
      
      {/* BOTÓN VOLVER CONTEXTUAL: Esquina superior izquierda */}
      <button 
        onClick={handleVolver}
        className="absolute top-6 left-6 md:top-8 md:left-8 inline-flex items-center space-x-2 text-slate-400 hover:text-teal-400 transition-colors duration-200 text-sm font-semibold tracking-wide group"
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          className="w-4 h-4 transform group-hover:-translate-x-1 transition-transform duration-200" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor" 
          strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        <span>Volver</span>
      </button>

      {/* Malla de gradiente profunda para volumen visual */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(13,148,136,0.06),transparent_50%),radial-gradient(circle_at_70%_70%,rgba(139,92,246,0.06),transparent_50%)] pointer-events-none" />

      <div className="w-full max-w-md relative z-10 flex flex-col items-center">
        
        {/* CABECERA CON IMAGOTIPO EN CAJA CUADRADA PERFECTA */}
        <LogoSanti sizeClassName="w-20 h-20 md:w-24 md:h-24 mb-2" />
        
        <h1 className="text-white text-3xl font-black font-display tracking-tight text-center mt-2 mb-2">
          Crea tu cuenta
        </h1>
        <p className="text-sm text-slate-400 text-center font-sans max-w-xs mb-8">
          Para distribuidores y mecánicos de taller. Tu cuenta queda pendiente de aprobación hasta que el equipo verifique tus documentos.
        </p>

        {/* FORMULARIO GLASSMORPHIC */}
        <div className="w-full bg-[#1E293B]/30 border border-slate-800/80 rounded-2xl p-8 backdrop-blur-md shadow-2xl flex flex-col space-y-4">
          <RegistroForm
            rolPredefinido="CLIENTE_DISTRITO"
            tituloLanding="distribuidor"
            volverHref={fromRoute || defaultVolver}
          />
        </div>

        {/* PIE DE PÁGINA DE CUMPLIMIENTO */}
        <div className="mt-12 text-center text-slate-600 text-[11px] font-sans max-w-xs leading-normal">
          Este sitio está protegido. Consulta nuestra{' '}
          <Link href="/privacidad" className="underline hover:text-[#0D9488] transition-colors">
            Política de Privacidad
          </Link>{' '}
          y el consentimiento explícito de tratamiento de datos personales.
        </div>

      </div>
    </div>
  )
}

export default function RegistroDistrito() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-4 border-teal border-t-transparent animate-spin" />
      </div>
    }>
      <RegistroContent />
    </Suspense>
  )
}

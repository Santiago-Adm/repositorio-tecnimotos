'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { ApiCallError, rolToRoute } from '@/src/lib/types'
import Link from 'next/link'
import Image from 'next/image'
import { LogoSanti } from '@/src/components/ui/LogoSanti'

type Step = 'credentials' | 'mfa'

function LoginContent() {
  const { login, verifyMfa, user, loading } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()

  const [step, setStep] = useState<Step>('credentials')
  const [mfaSessionToken, setMfaSessionToken] = useState('')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [totp, setTotp] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Captura de dónde viene el usuario o fallback al historial
  const fromRoute = searchParams.get('from')

  useEffect(() => {
    if (!loading && user) {
      router.replace(rolToRoute(user.rol))
    }
  }, [loading, user, router])

  const handleVolver = () => {
    if (fromRoute) {
      router.push(fromRoute)
    } else {
      router.back()
    }
  }

  async function handleCredentials(e: React.FormEvent) {
    e.preventDefault()
    setErrorMsg(null)
    setSubmitting(true)
    try {
      const token = await login(email, password)
      setMfaSessionToken(token)
      setStep('mfa')
    } catch (err) {
      if (err instanceof ApiCallError) {
        setErrorMsg(
          err.code === 'AUTENTICACION_REQUERIDA'
            ? 'Correo o contraseña incorrectos.'
            : err.message,
        )
      } else {
        setErrorMsg('Ocurrió un error. Intenta de nuevo.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function handleMfa(e: React.FormEvent) {
    e.preventDefault()
    setErrorMsg(null)
    // R28: bloquear el código obvio "123456" solo en producción (NODE_ENV,
    // inyectado por Next.js en build/start — 'development' en `next dev`).
    // En desarrollo los 9 roles "de forma" (ADR-011) aceptan cualquier
    // 6 dígitos por diseño del backend — bloquear aquí sin distinguir
    // entorno rompía el login de VENDEDOR/MECANICO_*/CLIENTE_* en local.
    if (totp === '123456' && process.env.NODE_ENV === 'production') {
      setErrorMsg('Código de bypass no permitido en producción.')
      return
    }
    setSubmitting(true)
    try {
      await verifyMfa(mfaSessionToken, totp)
    } catch (err) {
      if (err instanceof ApiCallError) {
        if (err.code === 'AUTENTICACION_REQUERIDA') {
          const isExpired = err.message?.toLowerCase().includes('expir')
          if (isExpired) {
            setErrorMsg('El tiempo para verificar venció. Ingresa tus datos de nuevo.')
            setStep('credentials')
            setTotp('')
          } else {
            setErrorMsg('Código incorrecto. Intenta de nuevo.')
          }
        } else {
          setErrorMsg(err.message)
        }
      } else {
        setErrorMsg('Ocurrió un error. Intenta de nuevo.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-4 border-teal border-t-transparent animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0F172A] flex flex-col items-center justify-center px-4 py-12 relative overflow-hidden select-none">
      
      {/* BOTÓN VOLVER CONTEXTUAL: Esquina superior izquierda, limpio y accesible */}
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

      <div className="w-full max-w-sm relative z-10 flex flex-col items-center">
        
        {/* CABECERA: CENTRALIZACIÓN DE ISOTIPO CORPORATIVO */}
        <LogoSanti sizeClassName="w-20 h-20 md:w-24 md:h-24 mb-2" />
        
        <h1 className="text-white text-3xl font-black font-display tracking-tight text-center mt-2 mb-8">
          <span className="inline-block bg-gradient-to-r from-white via-cyan-200 via-purple-300 to-white bg-[length:200%_auto] bg-clip-text text-transparent animate-[shimmer_3s_linear_infinite] drop-shadow-[0_4px_12px_rgba(34,211,238,0.15)]">
            Ingresa para continuar
          </span>
        </h1>

        {/* FORMULARIO SEGURO Y COMPATIBLE CON EL PIPELINE DE RAILWAY */}
        <div className="w-full bg-[#1E293B]/30 border border-slate-800/85 rounded-2xl p-8 backdrop-blur-md shadow-2xl flex flex-col space-y-6">
          {step === 'credentials' ? (
            <form onSubmit={handleCredentials} className="flex flex-col gap-4">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 tracking-wider uppercase font-sans">
                  Correo electrónico
                </label>
                <input
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="ejemplo@correo.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  disabled={submitting}
                  className="w-full bg-[#1E293B]/60 border border-slate-800 focus:border-[#0D9488] text-white text-sm rounded-xl px-4 py-3.5 outline-none transition-all placeholder:text-slate-650 font-sans disabled:opacity-50"
                />
              </div>
              
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 tracking-wider uppercase font-sans">
                  Contraseña
                </label>
                <input
                  type="password"
                  autoComplete="current-password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  disabled={submitting}
                  className="w-full bg-[#1E293B]/60 border border-slate-800 focus:border-[#0D9488] text-white text-sm rounded-xl px-4 py-3.5 outline-none transition-all placeholder:text-slate-650 font-sans disabled:opacity-50"
                />
              </div>

              {errorMsg && (
                <p className="text-xs text-red-500 font-sans bg-red-950/20 border border-red-900/30 px-3 py-2 rounded-lg leading-relaxed">
                  {errorMsg}
                </p>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-[#0D9488] hover:bg-[#0b7a70] text-white font-bold py-3.5 rounded-full transition-all text-sm tracking-wide shadow-[0_4px_15px_rgba(13,148,136,0.2)] disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] mt-2"
              >
                {submitting ? 'Verificando...' : 'Continuar'}
              </button>

              {/* CONMUTADOR DE FLUJO ESTILO ECOISOTIPO */}
              <p className="text-center text-xs text-slate-400 font-sans mt-2 pt-2 border-t border-slate-800/40">
                ¿No tienes una cuenta?{' '}
                <Link href="/conductor/registro" className="text-[#0D9488] hover:underline font-bold transition-all ml-0.5">
                  Regístrate aquí
                </Link>
              </p>
            </form>
          ) : (
            <form onSubmit={handleMfa} className="flex flex-col gap-4">
              <div className="text-center space-y-1 mb-2">
                <h2 className="text-white text-lg font-bold font-display">
                  Verificación de Seguridad
                </h2>
                <p className="text-xs text-slate-400 font-sans leading-relaxed">
                  Ingresa el código de 6 dígitos enviado a tu aplicación.
                </p>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 tracking-wider uppercase font-sans text-center">
                  Código de verificación
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  autoComplete="one-time-code"
                  required
                  value={totp}
                  onChange={e => setTotp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  disabled={submitting}
                  placeholder="000000"
                  className="w-full bg-[#1E293B]/60 border border-slate-800 focus:border-[#0D9488] text-white text-center text-lg font-mono tracking-[0.4em] rounded-xl px-4 py-3.5 outline-none transition-all placeholder:text-slate-700 disabled:opacity-50"
                />
              </div>

              {errorMsg && (
                <p className="text-xs text-red-500 font-sans bg-red-950/20 border border-red-900/30 px-3 py-2 rounded-lg leading-relaxed">
                  {errorMsg}
                </p>
              )}

              <button
                type="submit"
                disabled={submitting || totp.length !== 6}
                className="w-full bg-[#0D9488] hover:bg-[#0b7a70] text-white font-bold py-3.5 rounded-full transition-all text-sm tracking-wide shadow-[0_4px_15px_rgba(13,148,136,0.2)] disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] mt-2"
              >
                {submitting ? 'Verificando...' : 'Ingresar'}
              </button>

              <button
                type="button"
                onClick={() => { setStep('credentials'); setErrorMsg(null); setTotp('') }}
                className="text-xs text-slate-500 hover:text-teal-400 transition-colors font-sans underline text-center mt-2"
              >
                Volver a credenciales
              </button>
            </form>
          )}
        </div>

        {/* PIE DE PÁGINA (LEGAL - R30) */}
        <div className="mt-12 text-center text-slate-600 text-[11px] font-sans max-w-xs leading-normal">
          Este sitio está protegido. Consulta nuestra{' '}
          <Link href="/privacidad" className="underline hover:text-[#0D9488] transition-colors">
            Política de Privacidad
          </Link>{' '}
          y{' '}
          <a href="#" className="underline hover:text-[#0D9488] transition-colors">
            Términos de Servicio
          </a>.
        </div>

      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-4 border-teal border-t-transparent animate-spin" />
      </div>
    }>
      <LoginContent />
    </Suspense>
  )
}

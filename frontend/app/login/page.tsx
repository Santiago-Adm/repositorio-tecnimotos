'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { ApiCallError, rolToRoute } from '@/src/lib/types'
import Link from 'next/link'

type Step = 'credentials' | 'mfa'

export default function LoginPage() {
  const { login, verifyMfa, user, loading } = useAuth()
  const router = useRouter()

  const [step, setStep] = useState<Step>('credentials')
  const [mfaSessionToken, setMfaSessionToken] = useState('')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [totp, setTotp] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && user) {
      router.replace(rolToRoute(user.rol))
    }
  }, [loading, user, router])

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
      <div className="min-h-screen bg-surface-light flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-4 border-teal border-t-transparent animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface-light flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          {/* Referencia al asset de logo — requiere /brand/logo-positivo.svg provisto por Sant (10 §3.5) */}
          <img
            src="/brand/logo-positivo.svg"
            alt="Tecnimotos"
            className="h-10 mx-auto"
          />
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
          {step === 'credentials' ? (
            <>
              <h1 className="font-display text-xl font-semibold text-slate-800 mb-1">
                Ingresar
              </h1>
              <p className="font-body text-sm text-slate-500 mb-6">
                Ingresa tus credenciales para continuar.
              </p>
              <form onSubmit={handleCredentials} className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs font-body font-semibold text-slate-600 mb-1">
                    Correo electrónico
                  </label>
                  <input
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    disabled={submitting}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-slate-800 text-sm font-body focus:outline-none focus:ring-2 focus:ring-teal disabled:opacity-60"
                  />
                </div>
                <div>
                  <label className="block text-xs font-body font-semibold text-slate-600 mb-1">
                    Contraseña
                  </label>
                  <input
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    disabled={submitting}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-slate-800 text-sm font-body focus:outline-none focus:ring-2 focus:ring-teal disabled:opacity-60"
                  />
                </div>
                {errorMsg && (
                  <p className="text-sm text-red-600 font-body">{errorMsg}</p>
                )}
                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-2.5 rounded-lg bg-teal text-white text-sm font-body font-semibold hover:bg-teal/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Verificando...' : 'Continuar'}
                </button>
              </form>
            </>
          ) : (
            <>
              <h1 className="font-display text-xl font-semibold text-slate-800 mb-1">
                Verificación
              </h1>
              <p className="font-body text-sm text-slate-500 mb-6">
                Ingresa el código de 6 dígitos de tu aplicación de autenticación.
              </p>
              <form onSubmit={handleMfa} className="flex flex-col gap-4">
                <div>
                  <label className="block text-xs font-body font-semibold text-slate-600 mb-1">
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
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-slate-800 text-sm font-mono tracking-widest focus:outline-none focus:ring-2 focus:ring-teal disabled:opacity-60"
                  />
                </div>
                {errorMsg && (
                  <p className="text-sm text-red-600 font-body">{errorMsg}</p>
                )}
                <button
                  type="submit"
                  disabled={submitting || totp.length !== 6}
                  className="w-full py-2.5 rounded-lg bg-teal text-white text-sm font-body font-semibold hover:bg-teal/90 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Verificando...' : 'Ingresar'}
                </button>
                <button
                  type="button"
                  onClick={() => { setStep('credentials'); setErrorMsg(null); setTotp('') }}
                  className="text-sm text-slate-500 hover:text-slate-700 font-body underline"
                >
                  Volver a credenciales
                </button>
              </form>
            </>
          )}
        </div>

        <p className="mt-6 text-center text-xs text-slate-500 font-body">
          <Link href="/privacidad" className="underline hover:text-slate-700">
            Política de privacidad
          </Link>
        </p>
      </div>
    </div>
  )
}

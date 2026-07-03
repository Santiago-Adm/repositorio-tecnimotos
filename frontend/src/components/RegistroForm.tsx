'use client'

import { useState, useRef } from 'react'
import Link from 'next/link'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'

type RolCliente = 'CLIENTE_CONDUCTOR' | 'CLIENTE_DISTRITO' | 'CLIENTE_RURAL'

interface Props {
  rolPredefinido: RolCliente
  tituloLanding: string
  volverHref: string
}

interface CamposFormulario {
  nombre: string
  email: string
  password: string
  consentimiento_privacidad: boolean
  dni_frente: File | null
  dni_dorso: File | null
}

type EstadoEnvio = 'idle' | 'enviando' | 'exito' | 'error'

const MENSAJES_ERROR: Record<string, string> = {
  VALIDACION_FALLIDA: 'Revisa los datos ingresados.',
  EMAIL_DUPLICADO: 'Ya existe una cuenta con ese correo.',
  ACCESO_DENEGADO: 'No tienes acceso a esta acción.',
}

export default function RegistroForm({ rolPredefinido, volverHref }: Props) {
  const [campos, setCampos] = useState<CamposFormulario>({
    nombre: '',
    email: '',
    password: '',
    consentimiento_privacidad: false,
    dni_frente: null,
    dni_dorso: null,
  })
  const [estado, setEstado] = useState<EstadoEnvio>('idle')
  const [mensajeError, setMensajeError] = useState<string | null>(null)

  const refFrente = useRef<HTMLInputElement>(null)
  const refDorso = useRef<HTMLInputElement>(null)

  function actualizarCampo<K extends keyof CamposFormulario>(k: K, v: CamposFormulario[K]) {
    setCampos(prev => ({ ...prev, [k]: v }))
  }

  async function enviar(e: React.FormEvent) {
    e.preventDefault()
    if (!campos.dni_frente || !campos.dni_dorso) {
      setMensajeError('Adjunta ambas fotos de tu DNI para continuar.')
      return
    }

    setEstado('enviando')
    setMensajeError(null)

    try {
      const form = new FormData()
      form.append('email', campos.email)
      form.append('nombre', campos.nombre)
      form.append('password', campos.password)
      form.append('rol', rolPredefinido)
      form.append('consentimiento_privacidad', String(campos.consentimiento_privacidad))
      form.append('dni_frente', campos.dni_frente)
      form.append('dni_dorso', campos.dni_dorso)

      await apiClient.postForm('/v1/auth/registro', form)
      setEstado('exito')
    } catch (err) {
      const code = (err as ApiCallError).code ?? 'VALIDACION_FALLIDA'
      setMensajeError(MENSAJES_ERROR[code] ?? 'Algo salió mal. Intenta de nuevo.')
      setEstado('error')
    }
  }

  if (estado === 'exito') {
    return (
      <div className="text-center space-y-6 py-4">
        <div className="w-16 h-16 mx-auto rounded-full bg-[#0D9488]/20 flex items-center justify-center text-[#0D9488] shadow-[0_0_20px_rgba(13,148,136,0.3)] animate-pulse">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <div className="space-y-2">
          <h2 className="font-display text-2xl font-bold text-white">¡Solicitud Enviada!</h2>
          <p className="font-body text-slate-300 text-sm leading-relaxed max-w-sm mx-auto">
            Revisaremos tus documentos y te notificaremos cuando tu cuenta esté activa. El equipo administrador verificará los datos a la brevedad.
          </p>
        </div>
        <div className="pt-4 border-t border-slate-800/40">
          <Link href={volverHref} className="inline-flex items-center space-x-2 text-sm text-[#0D9488] font-bold hover:underline">
            <span>Volver a la página principal</span>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={enviar} className="space-y-5">
      <div>
        <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 tracking-wider uppercase font-sans">
          Nombre completo
        </label>
        <input
          type="text"
          required
          minLength={1}
          maxLength={200}
          value={campos.nombre}
          onChange={e => actualizarCampo('nombre', e.target.value)}
          className="w-full bg-[#1E293B]/60 border border-slate-800 focus:border-[#0D9488] text-white text-sm rounded-xl px-4 py-3 outline-none transition-all placeholder:text-slate-650 font-sans disabled:opacity-50"
          placeholder="Tu nombre y apellidos"
          disabled={estado === 'enviando'}
        />
      </div>

      <div>
        <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 tracking-wider uppercase font-sans">
          Correo electrónico
        </label>
        <input
          type="email"
          required
          minLength={5}
          maxLength={200}
          value={campos.email}
          onChange={e => actualizarCampo('email', e.target.value)}
          className="w-full bg-[#1E293B]/60 border border-slate-800 focus:border-[#0D9488] text-white text-sm rounded-xl px-4 py-3 outline-none transition-all placeholder:text-slate-655 font-sans disabled:opacity-50"
          placeholder="ejemplo@correo.com"
          disabled={estado === 'enviando'}
        />
      </div>

      <div>
        <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 tracking-wider uppercase font-sans">
          Contraseña
        </label>
        <input
          type="password"
          required
          minLength={8}
          value={campos.password}
          onChange={e => actualizarCampo('password', e.target.value)}
          className="w-full bg-[#1E293B]/60 border border-slate-800 focus:border-[#0D9488] text-white text-sm rounded-xl px-4 py-3 outline-none transition-all placeholder:text-slate-655 font-sans disabled:opacity-50"
          placeholder="Mínimo 8 caracteres"
          disabled={estado === 'enviando'}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-[11px] font-semibold text-slate-400 mb-0.5 tracking-wider uppercase font-sans">
          Carga de DNI
        </label>
        <p className="text-xs text-slate-400 leading-normal">
          Necesitamos fotografiar ambas caras de tu documento para habilitar tu perfil (RNL-04).
        </p>
        <div className="grid grid-cols-2 gap-4">
          <button
            type="button"
            onClick={() => refFrente.current?.click()}
            className={`flex-1 bg-[#1E293B]/40 border border-dashed rounded-xl p-4 text-center text-xs transition-colors cursor-pointer flex flex-col items-center justify-center space-y-1 ${
              campos.dni_frente
                ? 'border-[#0D9488] text-teal bg-[#0D9488]/10'
                : 'border-slate-700 text-slate-400 hover:border-[#0D9488] hover:text-white'
            }`}
            disabled={estado === 'enviando'}
          >
            <svg className="w-5 h-5 mb-1 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span className="font-bold">{campos.dni_frente ? '✓ Frente Cargado' : 'Frente del DNI'}</span>
            {campos.dni_frente && <span className="text-[10px] text-slate-500 font-mono truncate max-w-full block px-1">{campos.dni_frente.name.slice(0, 15)}</span>}
          </button>
          
          <button
            type="button"
            onClick={() => refDorso.current?.click()}
            className={`flex-1 bg-[#1E293B]/40 border border-dashed rounded-xl p-4 text-center text-xs transition-colors cursor-pointer flex flex-col items-center justify-center space-y-1 ${
              campos.dni_dorso
                ? 'border-[#0D9488] text-teal bg-[#0D9488]/10'
                : 'border-slate-700 text-slate-400 hover:border-[#0D9488] hover:text-white'
            }`}
            disabled={estado === 'enviando'}
          >
            <svg className="w-5 h-5 mb-1 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span className="font-bold">{campos.dni_dorso ? '✓ Reverso Cargado' : 'Dorso del DNI'}</span>
            {campos.dni_dorso && <span className="text-[10px] text-slate-500 font-mono truncate max-w-full block px-1">{campos.dni_dorso.name.slice(0, 15)}</span>}
          </button>
        </div>
        <input
          ref={refFrente}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={e => actualizarCampo('dni_frente', e.target.files?.[0] ?? null)}
        />
        <input
          ref={refDorso}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={e => actualizarCampo('dni_dorso', e.target.files?.[0] ?? null)}
        />
      </div>

      <label className="flex items-start gap-3 cursor-pointer select-none">
        <input
          type="checkbox"
          required
          checked={campos.consentimiento_privacidad}
          onChange={e => actualizarCampo('consentimiento_privacidad', e.target.checked)}
          className="mt-1 accent-[#0D9488]"
          disabled={estado === 'enviando'}
        />
        <span className="text-xs font-sans text-slate-400 leading-relaxed">
          He leído y acepto la{' '}
          <Link href="/privacidad" className="text-[#0D9488] hover:underline font-bold" target="_blank">
            política de privacidad
          </Link>
          {' '}y doy mi consentimiento explícito para el tratamiento de mis datos personales.
        </span>
      </label>

      {mensajeError && (
        <p className="text-xs text-red-500 font-sans bg-red-950/20 border border-red-900/30 px-3 py-2 rounded-lg leading-relaxed">
          {mensajeError}
        </p>
      )}

      <button
        type="submit"
        disabled={estado === 'enviando'}
        className="w-full bg-[#0D9488] hover:bg-[#0b7a70] text-white font-bold py-3.5 rounded-full transition-all text-sm tracking-wide shadow-[0_4px_15px_rgba(13,148,136,0.2)] disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98] mt-2"
      >
        {estado === 'enviando' ? 'Enviando solicitud...' : 'Crear mi cuenta'}
      </button>

      <p className="text-center text-xs text-slate-400 font-sans mt-2 pt-2 border-t border-slate-800/40">
        ¿Ya tienes una cuenta?{' '}
        <Link href={`/login?from=${volverHref}`} className="text-[#0D9488] hover:underline font-bold transition-all ml-0.5">
          Inicia sesión
        </Link>
      </p>
    </form>
  )
}

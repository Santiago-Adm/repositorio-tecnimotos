'use client'

import { FormEvent, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import { ROL_LABELS, ROLES_CREABLES, ROLES_CLIENTE } from './usuariosConstants'

interface Props {
  onCerrar: () => void
  onCreado: () => void
}

function generarPasswordTemporal(): string {
  const alfabeto = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789'
  const bytes = new Uint32Array(12)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, b => alfabeto[b % alfabeto.length]).join('')
}

/**
 * EP-ADM-05 (Crear usuario) — ADR-016 ya bloquea SUPERADMIN/ADMINISTRADOR en
 * el backend (solo vía seed/bootstrap), por eso el selector aquí solo ofrece
 * los 9 roles no-master; no hace falta confirmación reforzada para master
 * porque ese caso es arquitectónicamente imposible desde este endpoint.
 */
export default function CrearUsuarioModal({ onCerrar, onCreado }: Props) {
  const [nombre, setNombre] = useState('')
  const [email, setEmail] = useState('')
  const [rol, setRol] = useState(ROLES_CREABLES[0])
  const [password, setPassword] = useState(generarPasswordTemporal())
  const [consentimiento, setConsentimiento] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [creado, setCreado] = useState<{ email: string; password: string } | null>(null)

  const esRolCliente = ROLES_CLIENTE.has(rol)

  async function guardar(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (esRolCliente && !consentimiento) {
      setError('El consentimiento de privacidad es obligatorio para roles de cliente (Ley N.° 29733).')
      return
    }
    setGuardando(true)
    try {
      await apiClient.post('/v1/admin/usuarios', {
        nombre, email, rol, password,
        consentimiento_privacidad: esRolCliente ? consentimiento : false,
      })
      setCreado({ email, password })
    } catch (err) {
      setError(err instanceof ApiCallError ? err.message : 'No se pudo crear el usuario.')
    } finally {
      setGuardando(false)
    }
  }

  if (creado) {
    return (
      <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
        <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-xl">
          <h3 className="font-display text-lg font-bold text-slate-100">Usuario creado</h3>
          <p className="text-sm text-slate-300 font-body">
            Comparte esta contraseña temporal con <strong>{creado.email}</strong> por un canal seguro.
            Es responsabilidad del usuario cambiarla en su primer ingreso.
          </p>
          <div className="flex items-center gap-2">
            <input
              readOnly
              value={creado.password}
              className="flex-1 min-w-0 px-3 py-2.5 rounded-lg bg-slate-800 border border-teal/40 text-sm text-teal font-mono"
            />
            <button
              type="button"
              onClick={() => navigator.clipboard?.writeText(creado.password)}
              className="px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-300 hover:text-teal transition-colors shrink-0"
            >
              Copiar
            </button>
          </div>
          <div className="flex justify-end pt-2">
            <button
              type="button"
              onClick={onCreado}
              className="px-4 py-2 rounded-lg bg-teal text-white text-sm font-semibold hover:bg-teal/90 transition-colors"
            >
              Listo
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" onClick={onCerrar}>
      <div
        className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-xl"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h3 className="font-display text-lg font-bold text-slate-100">Crear usuario</h3>
          <button
            type="button"
            onClick={onCerrar}
            aria-label="Cerrar"
            className="w-9 h-9 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            ✕
          </button>
        </div>

        <form onSubmit={guardar} className="space-y-4">
          <div>
            <label htmlFor="nombre" className="block text-xs font-semibold text-slate-400 mb-1">Nombre completo</label>
            <input
              id="nombre" type="text" required value={nombre} onChange={e => setNombre(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 font-body focus:outline-none focus:ring-2 focus:ring-teal"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-xs font-semibold text-slate-400 mb-1">Correo electrónico</label>
            <input
              id="email" type="email" required value={email} onChange={e => setEmail(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 font-body focus:outline-none focus:ring-2 focus:ring-teal"
            />
          </div>

          <div>
            <label htmlFor="rol" className="block text-xs font-semibold text-slate-400 mb-1">Rol</label>
            <select
              id="rol" value={rol} onChange={e => setRol(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 font-body focus:outline-none focus:ring-2 focus:ring-teal"
            >
              {ROLES_CREABLES.map(r => <option key={r} value={r}>{ROL_LABELS[r]}</option>)}
            </select>
            <p className="text-[11px] text-slate-500 font-body mt-1">
              Los roles Superadmin y Administrador son protegidos — solo se crean vía bootstrap del sistema.
            </p>
          </div>

          {esRolCliente && (
            <label className="flex items-start gap-2 text-xs text-slate-300 font-body">
              <input
                type="checkbox" checked={consentimiento} onChange={e => setConsentimiento(e.target.checked)}
                className="mt-0.5 accent-teal"
              />
              <span>El usuario dio su consentimiento explícito para el tratamiento de datos personales (Ley N.° 29733).</span>
            </label>
          )}

          <div>
            <label htmlFor="password" className="block text-xs font-semibold text-slate-400 mb-1">Contraseña temporal</label>
            <div className="flex items-center gap-2">
              <input
                id="password" type="text" required minLength={8} value={password} onChange={e => setPassword(e.target.value)}
                className="flex-1 min-w-0 px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-teal"
              />
              <button
                type="button"
                onClick={() => setPassword(generarPasswordTemporal())}
                className="px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-300 hover:text-teal transition-colors shrink-0"
              >
                Regenerar
              </button>
            </div>
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button" onClick={onCerrar}
              className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit" disabled={guardando}
              className="px-4 py-2 rounded-lg bg-teal text-white text-sm font-semibold hover:bg-teal/90 transition-colors disabled:opacity-50"
            >
              {guardando ? 'Creando...' : 'Crear usuario'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

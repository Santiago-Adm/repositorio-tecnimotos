'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import ConfirmActionModal from '@/src/components/ConfirmActionModal'

interface UserRecord {
  usuario_id: string
  email: string
  nombre: string
  rol: string
  estado_cuenta: string
  activo?: boolean
  variante_tema?: string | null
}

const ROL_LABELS: Record<string, string> = {
  SUPERADMIN: 'Superadmin',
  ADMINISTRADOR: 'Administrador',
  VENDEDOR: 'Vendedor',
  MECANICO_MASTER: 'Mecánico Master',
  MECANICO_JUNIOR: 'Mecánico Junior',
  CLIENTE_CONDUCTOR: 'Cliente Conductor',
  CLIENTE_DISTRITO: 'Cliente Distrito',
  CLIENTE_RURAL: 'Cliente Rural',
  CLIENTE_FLOTA_DUENO: 'Flota Dueño',
  CLIENTE_FLOTA_CONDUCTOR: 'Flota Conductor',
  CLIENTE_MOTOLINEAL: 'Motolineal',
}

const ROLES_EDITABLES = [
  'VENDEDOR', 'MECANICO_MASTER', 'MECANICO_JUNIOR',
  'CLIENTE_CONDUCTOR', 'CLIENTE_DISTRITO', 'CLIENTE_RURAL',
  'CLIENTE_FLOTA_DUENO', 'CLIENTE_FLOTA_CONDUCTOR', 'CLIENTE_MOTOLINEAL',
]

const ROLES_MASTER = new Set(['SUPERADMIN', 'ADMINISTRADOR'])

const ESTADO_CUENTA_LABELS: Record<string, string> = {
  PENDIENTE_DOCUMENTOS: 'Pendiente Documentos',
  EN_REVISION: 'En Revisión',
  ACTIVO: 'Activo',
  RECHAZADO: 'Rechazado',
}

type ConfirmAccion = { tipo: 'suspender' | 'reactivar' | 'eliminar'; usuario: UserRecord } | null

/**
 * Gestión real de usuarios — editar/suspender/eliminar (ADR-016).
 * Compartido entre ADMINISTRADOR y SUPERADMIN (misma paridad de CRUD).
 * Roles master (SUPERADMIN/ADMINISTRADOR) nunca muestran acciones — solo
 * existen vía seed/bootstrap, protegido también en el backend (403 real).
 */
export default function UsuariosManager() {
  const [usuarios, setUsuarios] = useState<UserRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rolFilter, setRolFilter] = useState('ALL')
  const [estadoFilter, setEstadoFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  const [editandoId, setEditandoId] = useState<string | null>(null)
  const [editNombre, setEditNombre] = useState('')
  const [editRol, setEditRol] = useState('')
  const [accionError, setAccionError] = useState<string | null>(null)

  const [confirmAccion, setConfirmAccion] = useState<ConfirmAccion>(null)

  function fetchUsuarios() {
    setLoading(true)
    setError(null)
    const params = new URLSearchParams()
    if (rolFilter !== 'ALL') params.set('rol', rolFilter)
    if (estadoFilter !== 'ALL') params.set('estado', estadoFilter)
    apiClient
      .get<{ usuarios: UserRecord[] }>(`/v1/admin/usuarios?${params.toString()}`)
      .then(d => { setUsuarios(d.usuarios); setLoading(false) })
      .catch((err: ApiCallError) => { setError(err.code); setLoading(false) })
  }

  useEffect(() => { fetchUsuarios() }, [rolFilter, estadoFilter]) // eslint-disable-line react-hooks/exhaustive-deps

  const usuariosFiltrados = usuarios.filter(u => {
    const q = searchQuery.toLowerCase()
    return !q || u.nombre.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
  })

  function iniciarEdicion(u: UserRecord) {
    setEditandoId(u.usuario_id)
    setEditNombre(u.nombre)
    setEditRol(u.rol)
    setAccionError(null)
  }

  async function guardarEdicion(usuario_id: string) {
    setAccionError(null)
    try {
      await apiClient.patch(`/v1/admin/usuarios/${usuario_id}`, { nombre: editNombre, rol: editRol })
      setEditandoId(null)
      fetchUsuarios()
    } catch (err) {
      setAccionError(err instanceof ApiCallError ? err.message : 'No se pudo editar el usuario.')
    }
  }

  async function ejecutarAccionConfirmada() {
    if (!confirmAccion) return
    const { tipo, usuario } = confirmAccion
    setAccionError(null)
    try {
      if (tipo === 'suspender') {
        await apiClient.patch(`/v1/admin/usuarios/${usuario.usuario_id}/estado`, { activo: false })
      } else if (tipo === 'reactivar') {
        await apiClient.patch(`/v1/admin/usuarios/${usuario.usuario_id}/estado`, { activo: true })
      } else {
        await apiClient.delete(`/v1/admin/usuarios/${usuario.usuario_id}`)
      }
      fetchUsuarios()
    } catch (err) {
      setAccionError(err instanceof ApiCallError ? err.message : 'No se pudo completar la acción.')
    } finally {
      setConfirmAccion(null)
    }
  }

  const modalCopy: Record<'suspender' | 'reactivar' | 'eliminar', { title: string; description: string; confirmLabel: string; dangerous: boolean }> = {
    suspender: {
      title: 'Suspender usuario',
      description: `${confirmAccion?.usuario.nombre ?? ''} no podrá iniciar sesión hasta que se reactive. Esta acción es reversible.`,
      confirmLabel: 'Suspender', dangerous: true,
    },
    reactivar: {
      title: 'Reactivar usuario',
      description: `${confirmAccion?.usuario.nombre ?? ''} podrá volver a iniciar sesión de inmediato.`,
      confirmLabel: 'Reactivar', dangerous: false,
    },
    eliminar: {
      title: 'Eliminar usuario físicamente',
      description: `Esta acción NO se puede deshacer. Si ${confirmAccion?.usuario.nombre ?? 'el usuario'} tiene historial real de pedidos/OTs, la eliminación se rechazará y quedará suspendido en su lugar.`,
      confirmLabel: 'Eliminar definitivamente', dangerous: true,
    },
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={fetchUsuarios} className="text-xs text-teal font-body hover:underline">Actualizar</button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-800">
        <div>
          <label className="text-xs text-slate-500 font-body block mb-1">Buscar por nombre o correo</label>
          <input
            type="search" placeholder="Buscar..." value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs font-body focus:outline-none focus:ring-1 focus:ring-teal"
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 font-body block mb-1">Filtrar por Rol</label>
          <select
            value={rolFilter} onChange={e => setRolFilter(e.target.value)}
            className="w-full px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs font-body focus:outline-none focus:ring-1 focus:ring-teal"
          >
            <option value="ALL">Todos los roles</option>
            {Object.entries(ROL_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500 font-body block mb-1">Filtrar por Estado de Cuenta</label>
          <select
            value={estadoFilter} onChange={e => setEstadoFilter(e.target.value)}
            className="w-full px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs font-body focus:outline-none focus:ring-1 focus:ring-teal"
          >
            <option value="ALL">Todos los estados</option>
            {Object.entries(ESTADO_CUENTA_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>
      </div>

      {accionError && <p className="text-xs text-red-400 font-body">{accionError}</p>}

      {loading ? (
        <LoadingIndicator message="Cargando usuarios..." />
      ) : error ? (
        <ErrorDisplay code={error} onRetry={fetchUsuarios} />
      ) : usuariosFiltrados.length === 0 ? (
        <EmptyState title="Sin usuarios coincidentes" description="No hay registros que coincidan con los filtros aplicados." />
      ) : (
        <div className="rounded-xl border border-slate-800 overflow-hidden overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-800 text-slate-400 font-body border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 font-semibold">Nombre</th>
                <th className="px-4 py-3 font-semibold">Email</th>
                <th className="px-4 py-3 font-semibold">Rol</th>
                <th className="px-4 py-3 font-semibold">Estado</th>
                <th className="px-4 py-3 font-semibold text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {usuariosFiltrados.map(u => {
                const esMaster = ROLES_MASTER.has(u.rol)
                const editando = editandoId === u.usuario_id
                return (
                  <tr key={u.usuario_id} className="hover:bg-slate-800/40">
                    <td className="px-4 py-2.5 text-slate-200 font-semibold">
                      {editando ? (
                        <input
                          value={editNombre} onChange={e => setEditNombre(e.target.value)}
                          className="px-2 py-1 rounded bg-slate-900 border border-teal/50 text-slate-200 text-xs w-36"
                          autoFocus
                        />
                      ) : u.nombre}
                    </td>
                    <td className="px-4 py-2.5 text-slate-400">{u.email}</td>
                    <td className="px-4 py-2.5 text-slate-300 font-body">
                      {editando ? (
                        <select
                          value={editRol} onChange={e => setEditRol(e.target.value)}
                          className="px-2 py-1 rounded bg-slate-900 border border-teal/50 text-slate-200 text-xs"
                        >
                          {ROLES_EDITABLES.map(r => <option key={r} value={r}>{ROL_LABELS[r]}</option>)}
                        </select>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">
                          {ROL_LABELS[u.rol] || u.rol}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-body ${
                        u.estado_cuenta === 'ACTIVO' ? 'bg-teal/20 text-teal' :
                        u.estado_cuenta === 'PENDIENTE_DOCUMENTOS' ? 'bg-amber-500/20 text-amber-400' :
                        u.estado_cuenta === 'EN_REVISION' ? 'bg-electric/20 text-electric' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {ESTADO_CUENTA_LABELS[u.estado_cuenta] || u.estado_cuenta}
                      </span>
                      {u.activo === false && (
                        <span className="ml-1.5 px-2 py-0.5 rounded-full text-[10px] font-body bg-red-950/40 text-red-400 border border-red-900/40">
                          Suspendido
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-right space-x-3 whitespace-nowrap">
                      {esMaster ? (
                        <span className="text-[10px] text-slate-600 font-body italic">Rol master — protegido</span>
                      ) : editando ? (
                        <>
                          <button onClick={() => guardarEdicion(u.usuario_id)} className="text-xs text-teal font-semibold hover:underline">Guardar</button>
                          <button onClick={() => setEditandoId(null)} className="text-xs text-slate-400 font-semibold hover:underline">Cancelar</button>
                        </>
                      ) : (
                        <>
                          <button onClick={() => iniciarEdicion(u)} className="text-xs text-electric font-semibold hover:underline">Editar</button>
                          {u.activo === false ? (
                            <button onClick={() => setConfirmAccion({ tipo: 'reactivar', usuario: u })} className="text-xs text-teal font-semibold hover:underline">Reactivar</button>
                          ) : (
                            <button onClick={() => setConfirmAccion({ tipo: 'suspender', usuario: u })} className="text-xs text-amber-400 font-semibold hover:underline">Suspender</button>
                          )}
                          <button onClick={() => setConfirmAccion({ tipo: 'eliminar', usuario: u })} className="text-xs text-red-400 font-semibold hover:underline">Eliminar</button>
                        </>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmActionModal
        open={confirmAccion !== null}
        title={confirmAccion ? modalCopy[confirmAccion.tipo].title : ''}
        description={confirmAccion ? modalCopy[confirmAccion.tipo].description : ''}
        confirmLabel={confirmAccion ? modalCopy[confirmAccion.tipo].confirmLabel : ''}
        dangerous={confirmAccion ? modalCopy[confirmAccion.tipo].dangerous : false}
        onConfirm={ejecutarAccionConfirmada}
        onCancel={() => setConfirmAccion(null)}
      />
    </div>
  )
}

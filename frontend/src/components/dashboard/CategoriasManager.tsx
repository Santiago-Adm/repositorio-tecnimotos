'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'

interface Categoria {
  id: string
  nombre: string
  orden: number
}

/**
 * CRUD de categorías del catálogo (EP-CAT-13 a 16, PIEZA C sesión 2026-07-03).
 * Solo ADMINISTRADOR/SUPERADMIN — compartido entre ambos dashboards para no
 * duplicar la lógica de creación/edición/eliminación en dos archivos.
 */
export default function CategoriasManager() {
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [categoriasError, setCategoriasError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(true)
  const [nuevaCategoria, setNuevaCategoria] = useState('')
  const [editandoId, setEditandoId] = useState<string | null>(null)
  const [editandoNombre, setEditandoNombre] = useState('')
  const [accionError, setAccionError] = useState<string | null>(null)

  function fetchCategorias() {
    setCategoriasError(null)
    apiClient
      .get<{ categorias: Categoria[] }>('/v1/categorias')
      .then(d => { setCategorias(d.categorias); setCargando(false) })
      .catch((err: ApiCallError) => { setCategoriasError(err.code); setCargando(false) })
  }

  useEffect(() => { fetchCategorias() }, [])

  async function crearCategoria(e: React.FormEvent) {
    e.preventDefault()
    setAccionError(null)
    if (!nuevaCategoria.trim()) return
    try {
      await apiClient.post('/v1/categorias', { nombre: nuevaCategoria.trim() })
      setNuevaCategoria('')
      fetchCategorias()
    } catch (err) {
      setAccionError(err instanceof ApiCallError ? err.message : 'No se pudo crear la categoría.')
    }
  }

  async function guardarEdicion(id: string) {
    setAccionError(null)
    try {
      await apiClient.patch(`/v1/categorias/${id}`, { nombre: editandoNombre.trim() })
      setEditandoId(null)
      fetchCategorias()
    } catch (err) {
      setAccionError(err instanceof ApiCallError ? err.message : 'No se pudo actualizar la categoría.')
    }
  }

  async function eliminarCategoria(id: string, nombre: string) {
    setAccionError(null)
    try {
      await apiClient.delete(`/v1/categorias/${id}`)
      fetchCategorias()
    } catch (err) {
      setAccionError(
        err instanceof ApiCallError ? err.message : `No se pudo eliminar "${nombre}".`
      )
    }
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display text-lg font-semibold text-slate-100">Categorías del catálogo</h2>
        <button onClick={fetchCategorias} className="text-xs text-teal font-body hover:underline">Actualizar</button>
      </div>

      <form onSubmit={crearCategoria} className="flex items-center gap-2 mb-4">
        <input
          type="text"
          value={nuevaCategoria}
          onChange={e => setNuevaCategoria(e.target.value)}
          placeholder="Nombre de la categoría nueva (ej. Iluminación)"
          className="flex-1 max-w-sm px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal/50"
        />
        <button
          type="submit"
          className="px-4 py-2 rounded-lg bg-teal text-white text-sm font-semibold hover:bg-teal/90 transition-colors"
        >
          Crear
        </button>
      </form>

      {accionError && <p className="text-xs text-red-400 font-body mb-4">{accionError}</p>}

      {cargando ? (
        <LoadingIndicator message="Cargando categorías..." />
      ) : categoriasError ? (
        <ErrorDisplay code={categoriasError} onRetry={fetchCategorias} />
      ) : categorias.length === 0 ? (
        <EmptyState title="Sin categorías" description="Crea la primera categoría con el formulario de arriba." />
      ) : (
        <div className="rounded-xl border border-slate-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-800/60">
              <tr>
                <th className="text-left px-4 py-2 text-xs text-slate-400 font-body">Nombre</th>
                <th className="text-left px-4 py-2 text-xs text-slate-400 font-body">Orden</th>
                <th className="text-right px-4 py-2 text-xs text-slate-400 font-body">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {categorias.map(cat => (
                <tr key={cat.id}>
                  <td className="px-4 py-2 font-mono text-slate-200">
                    {editandoId === cat.id ? (
                      <input
                        type="text"
                        value={editandoNombre}
                        onChange={e => setEditandoNombre(e.target.value)}
                        className="px-2 py-1 rounded bg-slate-900 border border-teal/50 text-slate-200 text-sm w-40"
                        autoFocus
                      />
                    ) : (
                      cat.nombre
                    )}
                  </td>
                  <td className="px-4 py-2 font-mono text-slate-400">{cat.orden}</td>
                  <td className="px-4 py-2 text-right space-x-3">
                    {editandoId === cat.id ? (
                      <>
                        <button onClick={() => guardarEdicion(cat.id)} className="text-xs text-teal font-semibold hover:underline">
                          Guardar
                        </button>
                        <button onClick={() => setEditandoId(null)} className="text-xs text-slate-400 font-semibold hover:underline">
                          Cancelar
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => { setEditandoId(cat.id); setEditandoNombre(cat.nombre) }}
                          className="text-xs text-electric font-semibold hover:underline"
                        >
                          Editar
                        </button>
                        <button onClick={() => eliminarCategoria(cat.id, cat.nombre)} className="text-xs text-red-400 font-semibold hover:underline">
                          Eliminar
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

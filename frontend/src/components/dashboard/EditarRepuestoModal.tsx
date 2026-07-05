'use client'

import { FormEvent, useEffect, useState } from 'react'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError, RepuestoDetalle, RepuestoListItem } from '@/src/lib/types'
import LoadingIndicator from '@/src/components/LoadingIndicator'

interface Categoria {
  id: string
  nombre: string
  orden: number
}

interface Props {
  repuesto: RepuestoListItem
  onCerrar: () => void
  onGuardado: () => void
}

/**
 * EP-CAT-10 (PATCH nombre/descripcion/categoria/modelo/año) + subida de
 * imagen única (POST /v1/repuestos/{codigo}/imagen) — el backend dejó
 * explícitamente esto "sin UI, para sesión de frontend aparte"
 * (api/routes/catalogo.py:1060). `codigo` y `universo` no son editables
 * por diseño de dominio (RNN, EP-CAT-10) — no se muestran como campos.
 */
export default function EditarRepuestoModal({ repuesto, onCerrar, onGuardado }: Props) {
  const [cargando, setCargando] = useState(true)
  const [nombre, setNombre] = useState(repuesto.nombre)
  const [descripcion, setDescripcion] = useState('')
  const [modelo, setModelo] = useState(repuesto.modelo)
  const [año, setAño] = useState<string>(repuesto.año?.toString() ?? '')
  const [categoria, setCategoria] = useState(repuesto.categoria)
  const [categorias, setCategorias] = useState<Categoria[]>([])

  const [archivo, setArchivo] = useState<File | null>(null)
  const [guardando, setGuardando] = useState(false)
  const [subiendoImagen, setSubiendoImagen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exito, setExito] = useState(false)

  useEffect(() => {
    let activo = true
    Promise.all([
      apiClient.get<RepuestoDetalle>(`/v1/repuestos/${repuesto.codigo}`),
      apiClient.get<{ categorias: Categoria[] }>('/v1/categorias'),
    ]).then(([detalle, cats]) => {
      if (!activo) return
      setDescripcion(detalle.descripcion)
      setCategorias(cats.categorias)
    }).catch(() => { /* si falla, el form igual permite editar con lo ya conocido */ })
      .finally(() => { if (activo) setCargando(false) })
    return () => { activo = false }
  }, [repuesto.codigo])

  async function guardar(e: FormEvent) {
    e.preventDefault()
    setGuardando(true)
    setError(null)
    try {
      await apiClient.patch(`/v1/repuestos/${repuesto.codigo}`, {
        nombre,
        descripcion,
        categoria,
        modelo,
        año: año ? Number(año) : null,
      })
      if (archivo) {
        setSubiendoImagen(true)
        const form = new FormData()
        form.append('archivo', archivo)
        await apiClient.postForm(`/v1/repuestos/${repuesto.codigo}/imagen`, form)
      }
      setExito(true)
      onGuardado()
    } catch (err) {
      setError(err instanceof ApiCallError ? err.message : 'No se pudo guardar el repuesto.')
    } finally {
      setGuardando(false)
      setSubiendoImagen(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={onCerrar}>
      <div
        className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-display text-lg font-bold text-slate-100">Editar repuesto</h3>
            <p className="text-xs text-slate-500 font-mono">{repuesto.codigo}</p>
          </div>
          <button
            type="button"
            onClick={onCerrar}
            aria-label="Cerrar"
            className="w-9 h-9 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            ✕
          </button>
        </div>

        {cargando ? (
          <div className="py-8 flex justify-center"><LoadingIndicator message="Cargando datos..." /></div>
        ) : (
          <form onSubmit={guardar} className="space-y-4">
            <div>
              <label htmlFor="nombre" className="block text-xs font-semibold text-slate-400 mb-1">Nombre</label>
              <input
                id="nombre"
                value={nombre}
                onChange={e => setNombre(e.target.value)}
                required
                className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal"
              />
            </div>

            <div>
              <label htmlFor="descripcion" className="block text-xs font-semibold text-slate-400 mb-1">Descripción</label>
              <textarea
                id="descripcion"
                value={descripcion}
                onChange={e => setDescripcion(e.target.value)}
                rows={3}
                className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal resize-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="modelo" className="block text-xs font-semibold text-slate-400 mb-1">Modelo</label>
                <input
                  id="modelo"
                  value={modelo}
                  onChange={e => setModelo(e.target.value)}
                  required
                  className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal"
                />
              </div>
              <div>
                <label htmlFor="anio" className="block text-xs font-semibold text-slate-400 mb-1">Año</label>
                <input
                  id="anio"
                  type="number"
                  min={1990}
                  max={2100}
                  value={año}
                  onChange={e => setAño(e.target.value)}
                  placeholder="Ej. 2022"
                  className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal"
                />
              </div>
            </div>

            <div>
              <label htmlFor="categoria" className="block text-xs font-semibold text-slate-400 mb-1">Categoría</label>
              <select
                id="categoria"
                value={categoria}
                onChange={e => setCategoria(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-teal"
              >
                {!categorias.some(c => c.nombre === categoria) && (
                  <option value={categoria}>{categoria}</option>
                )}
                {categorias.map(c => (
                  <option key={c.id} value={c.nombre}>{c.nombre}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="imagen" className="block text-xs font-semibold text-slate-400 mb-1">Imagen (JPEG/PNG/WEBP, máx. 5 MB)</label>
              <input
                id="imagen"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={e => setArchivo(e.target.files?.[0] ?? null)}
                className="w-full text-xs text-slate-400 file:mr-3 file:px-3 file:py-2 file:rounded-lg file:border-0 file:bg-teal/15 file:text-teal file:text-xs file:font-semibold hover:file:bg-teal/25"
              />
            </div>

            {error && <p className="text-xs text-red-400">{error}</p>}
            {exito && <p className="text-xs text-teal">Guardado correctamente.</p>}

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onCerrar}
                className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={guardando}
                className="px-4 py-2 rounded-lg bg-teal text-white text-sm font-semibold hover:bg-teal/90 transition-colors disabled:opacity-50"
              >
                {subiendoImagen ? 'Subiendo imagen...' : guardando ? 'Guardando...' : 'Guardar cambios'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import CatalogoNavegable from '@/src/components/dashboard/CatalogoNavegable'
import EditarRepuestoModal from '@/src/components/dashboard/EditarRepuestoModal'
import { RepuestoListItem } from '@/src/lib/types'

/** Pieza A — Catálogo ADMINISTRADOR: navegación universo → modelo → categoría
 *  paginada (EP-CAT-01/17) + CRUD real (EP-CAT-10 + subida de imagen) sobre
 *  el mismo ProductCard aprobado en el piloto del Skill. */
export default function CatalogoAdminTab() {
  const [editando, setEditando] = useState<RepuestoListItem | null>(null)
  const [version, setVersion] = useState(0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-100">Catálogo</h1>
        <p className="text-sm text-slate-400 font-body">Navega por universo y modelo — edita nombre, descripción, categoría, modelo, año e imagen.</p>
      </div>

      <CatalogoNavegable key={version} modoEdicion onEditar={setEditando} />

      {editando && (
        <EditarRepuestoModal
          repuesto={editando}
          onCerrar={() => setEditando(null)}
          onGuardado={() => { setEditando(null); setVersion(v => v + 1) }}
        />
      )}
    </div>
  )
}

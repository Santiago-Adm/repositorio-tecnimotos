'use client'

import CatalogoNavegable from '@/src/components/dashboard/CatalogoNavegable'

/**
 * Consulta de catálogo (SUPERADMIN) — antes hardcodeaba `universo=mototaxi_3r`
 * (solo 28% del catálogo real, 4 561/16 195) y no paginaba (traía el universo
 * completo de una sola vez). Ahora reutiliza el mismo motor universo→modelo→
 * categoría de Administrador, en modo solo lectura (R17 — sin duplicar lógica).
 */
export default function CatalogoConsultaTab() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-100">Catálogo de Repuestos</h1>
        <p className="text-sm text-slate-400 font-body">Consulta y verificación de repuestos.</p>
      </div>
      <CatalogoNavegable />
    </div>
  )
}

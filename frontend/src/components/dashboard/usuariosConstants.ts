export const ROL_LABELS: Record<string, string> = {
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

// Espejo de _ROLES_VALIDOS en api/routes/admin.py (EP-ADM-05) — SUPERADMIN y
// ADMINISTRADOR son roles master, nunca creables/editables desde la UI
// (ADR-016, solo vía seed/bootstrap).
export const ROLES_CREABLES = [
  'VENDEDOR', 'MECANICO_MASTER', 'MECANICO_JUNIOR',
  'CLIENTE_CONDUCTOR', 'CLIENTE_DISTRITO', 'CLIENTE_RURAL',
  'CLIENTE_FLOTA_DUENO', 'CLIENTE_FLOTA_CONDUCTOR', 'CLIENTE_MOTOLINEAL',
]

// Espejo de _ROLES_CLIENTE en api/routes/admin.py — requieren consentimiento
// explícito de privacidad (Ley N.° 29733).
export const ROLES_CLIENTE = new Set([
  'CLIENTE_CONDUCTOR', 'CLIENTE_DISTRITO', 'CLIENTE_RURAL',
  'CLIENTE_FLOTA_DUENO', 'CLIENTE_FLOTA_CONDUCTOR', 'CLIENTE_MOTOLINEAL',
])

export const ROLES_MASTER = new Set(['SUPERADMIN', 'ADMINISTRADOR'])

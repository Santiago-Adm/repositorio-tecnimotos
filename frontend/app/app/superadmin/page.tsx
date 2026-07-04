'use client'

import { useEffect, useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError, Rol } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import CategoriasManager from '@/src/components/dashboard/CategoriasManager'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'

type Seccion = 'Catálogo' | 'Categorías' | 'Stock' | 'Pedidos' | 'Taller' | 'Admin' | 'Logs y config'

// Mapeos visuales para roles
const ROL_LABELS: Record<string, string> = {
  SUPERADMIN: 'Superadmin',
  ADMINISTRADOR: 'Administrador',
  VENDEDOR: 'Vendedor',
  MECANICO_MASTER: 'Mecánico Master',
  MECANICO_JUNIOR: 'Mecánico Junior',
  CLIENTE_CONDUCTOR: 'Cliente Conductor',
  CLIENTE_DISTRITO: 'Cliente Distrito',
  CLIENTE_RURAL: 'Cliente Rural',
}

const ESTADO_CUENTA_LABELS: Record<string, string> = {
  PENDIENTE_DOCUMENTOS: 'Pendiente Documentos',
  EN_REVISION: 'En Revisión',
  ACTIVO: 'Activo',
  RECHAZADO: 'Rechazado',
}

const PARAM_INFO: Record<string, { title: string; desc: string }> = {
  max_consultas_precio_sesion: {
    title: 'Consultas de precio por sesión',
    desc: 'Límite de consultas rápidas que un cliente no registrado o de nivel 1 puede realizar por sesión.',
  },
  reintentos_notificacion: {
    title: 'Reintentos de notificación',
    desc: 'Número máximo de intentos de entrega para el bus de eventos de notificaciones.',
  },
  intervalo_reintento_notif_min: {
    title: 'Intervalo de reintentos (min)',
    desc: 'Espera en minutos entre reintentos automáticos tras fallas en la cola de notificaciones.',
  },
  ttl_cache_parametros_segundos: {
    title: 'TTL Caché Parámetros (seg)',
    desc: 'Segundos que los parámetros del sistema se almacenan en caché Redis DB-1 (Solo SUPERADMIN).',
  },
  umbral_margen_alerta: {
    title: 'Umbral margen de alerta',
    desc: 'Porcentaje por debajo del cual se notifica margen de ganancia crítico en reabastecimiento.',
  },
}

interface Metrics {
  requests_total?: number
  requests_per_second?: number
  [key: string]: unknown
}

interface BizMetrics {
  ots_activas: number
  pedidos_activos_hoy: number
  repuestos_bajo_umbral: number
  comprobantes_emitidos_mes_actual: number
  periodo_comprobantes: {
    desde: string
    hasta: string
  }
}

interface UserRecord {
  usuario_id: string
  email: string
  nombre: string
  rol: string
  estado_cuenta: string
  variante_tema?: string | null
  documentos?: { tipo: string; url: string }[]
}

interface ParameterRecord {
  clave: string
  valor: any
  modificable_por: string
}

export default function SuperadminDashboard() {
  const { user, logout } = useAuth()
  const router = useRouter()

  // Navegación
  const [seccion, setSeccion] = useState<Seccion>('Logs y config')
  const [adminTab, setAdminTab] = useState<'usuarios' | 'pendientes' | 'parametros'>('usuarios')

  // Sincronizar sección con URL query params para navegación y persistencia (evita pérdida de estado en refresco)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const secParam = params.get('seccion')
      const validSections: Array<Seccion> = [
        'Catálogo', 'Categorías', 'Stock', 'Pedidos', 'Taller', 'Admin', 'Logs y config'
      ]
      if (secParam === 'Logs') {
        setSeccion('Logs y config')
      } else if (secParam && validSections.includes(secParam as any)) {
        setSeccion(secParam as any)
      }
    }
  }, [])

  const handleSetSeccion = (sec: Seccion) => {
    setSeccion(sec)
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href)
      url.searchParams.set('seccion', sec)
      window.history.pushState({}, '', url.toString())
    }
  }

  // Estados - Logs y Métricas
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [bizMetrics, setBizMetrics] = useState<BizMetrics | null>(null)
  interface OpMetrics {
    rotacion_stock: number
    margen_promedio: number
    tasa_conversion: number
  }
  const [opMetrics, setOpMetrics] = useState<OpMetrics | null>(null)
  const [loadingMetrics, setLoadingMetrics] = useState(true)
  const [errorMetrics, setErrorMetrics] = useState<string | null>(null)

  // Estados - Usuarios Generales
  const [usuarios, setUsuarios] = useState<UserRecord[]>([])
  const [loadingUsuarios, setLoadingUsuarios] = useState(false)
  const [errorUsuarios, setErrorUsuarios] = useState<string | null>(null)
  const [rolFilter, setRolFilter] = useState<string>('ALL')
  const [estadoFilter, setEstadoFilter] = useState<string>('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  // Estados - Cuentas Pendientes
  const [pendientes, setPendientes] = useState<UserRecord[]>([])
  const [loadingPendientes, setLoadingPendientes] = useState(false)
  const [errorPendientes, setErrorPendientes] = useState<string | null>(null)
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null)
  const [actionErrorMsg, setActionErrorMsg] = useState<string | null>(null)
  const [rejectingUserId, setRejectingUserId] = useState<string | null>(null)
  const [motivoRechazo, setMotivoRechazo] = useState('')

  // Estados - Parámetros del sistema
  const [parametros, setParametros] = useState<ParameterRecord[]>([])
  const [loadingParametros, setLoadingParametros] = useState(false)
  const [errorParametros, setErrorParametros] = useState<string | null>(null)
  const [editingClave, setEditingClave] = useState<string | null>(null)
  const [editingValor, setEditingValor] = useState<string>('')
  const [savingParametro, setSavingParametro] = useState(false)

  // Estados - Sección Catálogo
  const [catalogoSearch, setCatalogoSearch] = useState('')
  const [catalogoRepuestos, setCatalogoRepuestos] = useState<any[]>([])
  const [loadingCatalogo, setLoadingCatalogo] = useState(false)
  const [errorCatalogo, setErrorCatalogo] = useState<string | null>(null)

  // Estados - Sección Stock
  const [stockItems, setStockItems] = useState<any[]>([])
  const [loadingStock, setLoadingStock] = useState(false)
  const [errorStock, setErrorStock] = useState<string | null>(null)

  // Estados - Sección Pedidos
  const [pedidosItems, setPedidosItems] = useState<any[]>([])
  const [loadingPedidos, setLoadingPedidos] = useState(false)
  const [errorPedidos, setErrorPedidos] = useState<string | null>(null)

  // Impersonación
  const [impersonationId, setImpersonationId] = useState('')

  useEffect(() => {
    if (user && user.rol !== 'SUPERADMIN') {
      router.replace('/login')
      return
    }
    fetchMetrics()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, router])

  // Carga de Métricas Técnicas + Negocio + Operacionales
  async function fetchMetrics() {
    setLoadingMetrics(true)
    setErrorMetrics(null)
    try {
      const [techData, bizData, opData] = await Promise.all([
        apiClient.get<Metrics>('/v1/metrics'),
        apiClient.get<BizMetrics>('/v1/admin/metricas-negocio'),
        apiClient.get<OpMetrics>('/v1/admin/metricas'),
      ])
      setMetrics(techData)
      setBizMetrics(bizData)
      setOpMetrics(opData)
    } catch (err) {
      setErrorMetrics((err as ApiCallError).code)
    } finally {
      setLoadingMetrics(false)
    }
  }

  // Carga de Usuarios
  async function fetchUsuarios() {
    setLoadingUsuarios(true)
    setErrorUsuarios(null)
    try {
      let url = '/v1/admin/usuarios'
      const queryParams = []
      if (rolFilter !== 'ALL') queryParams.push(`rol=${rolFilter}`)
      if (estadoFilter !== 'ALL') queryParams.push(`estado=${estadoFilter}`)
      if (queryParams.length > 0) {
        url += '?' + queryParams.join('&')
      }
      const data = await apiClient.get<{ total: number; usuarios: UserRecord[] }>(url)
      setUsuarios(data.usuarios ?? [])
    } catch (err) {
      setErrorUsuarios((err as ApiCallError).code)
    } finally {
      setLoadingUsuarios(false)
    }
  }

  // Carga de Pendientes
  async function fetchPendientes() {
    setLoadingPendientes(true)
    setErrorPendientes(null)
    try {
      const data = await apiClient.get<{ total: number; usuarios: UserRecord[] }>('/v1/admin/usuarios/pendientes')
      setPendientes(data.usuarios ?? [])
    } catch (err) {
      setErrorPendientes((err as ApiCallError).code)
    } finally {
      setLoadingPendientes(false)
    }
  }

  // Carga de Parámetros
  async function fetchParametros() {
    setLoadingParametros(true)
    setErrorParametros(null)
    try {
      const data = await apiClient.get<{ total: number; parametros: ParameterRecord[] }>('/v1/admin/parametros')
      setParametros(data.parametros ?? [])
    } catch (err) {
      setErrorParametros((err as ApiCallError).code)
    } finally {
      setLoadingParametros(false)
    }
  }

  // Carga de Catálogo
  async function fetchCatalogo(e?: FormEvent) {
    e?.preventDefault()
    setLoadingCatalogo(true)
    setErrorCatalogo(null)
    try {
      const query = catalogoSearch ? `&q=${encodeURIComponent(catalogoSearch)}` : ''
      const data = await apiClient.get<{ repuestos: any[]; total: number }>(`/v1/repuestos?universo=mototaxi_3r${query}`)
      setCatalogoRepuestos(data.repuestos ?? [])
    } catch (err) {
      setErrorCatalogo((err as ApiCallError).code)
    } finally {
      setLoadingCatalogo(false)
    }
  }

  // Carga de Stock
  async function fetchStock(silencioso = false) {
    if (!silencioso) setLoadingStock(true)
    setErrorStock(null)
    try {
      const data = await apiClient.get<{ stocks: any[]; total: number }>('/v1/stock')
      setStockItems(data.stocks ?? [])
    } catch (err) {
      if (!silencioso) setErrorStock((err as ApiCallError).code)
    } finally {
      if (!silencioso) setLoadingStock(false)
    }
  }

  // Carga de Pedidos
  async function fetchPedidos() {
    setLoadingPedidos(true)
    setErrorPedidos(null)
    try {
      const data = await apiClient.get<{ pedidos: any[]; total: number }>('/v1/pedidos')
      setPedidosItems(data.pedidos ?? [])
    } catch (err) {
      setErrorPedidos((err as ApiCallError).code)
    } finally {
      setLoadingPedidos(false)
    }
  }

  // Efecto desencadenado al cambiar de Sección
  useEffect(() => {
    if (seccion === 'Admin') {
      if (adminTab === 'usuarios') fetchUsuarios()
      if (adminTab === 'pendientes') fetchPendientes()
      if (adminTab === 'parametros') fetchParametros()
    } else if (seccion === 'Catálogo') {
      fetchCatalogo()
    } else if (seccion === 'Stock') {
      fetchStock()
    } else if (seccion === 'Pedidos') {
      fetchPedidos()
    } else if (seccion === 'Logs y config') {
      fetchMetrics()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seccion, adminTab, rolFilter, estadoFilter])

  // Polling de Stock — refresco silencioso cada 30s mientras la sección está activa
  useEffect(() => {
    if (seccion !== 'Stock') return
    const intervalo = setInterval(() => fetchStock(true), 30000)
    return () => clearInterval(intervalo)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seccion])

  // Aprobación de cuenta
  async function handleAprobar(userId: string) {
    setActionSuccessMsg(null)
    setActionErrorMsg(null)
    try {
      await apiClient.post(`/v1/admin/usuarios/${userId}/aprobar`)
      setActionSuccessMsg('Cuenta aprobada correctamente.')
      fetchPendientes()
    } catch (err) {
      setActionErrorMsg((err as ApiCallError).code)
    }
  }

  // Rechazo de cuenta
  async function handleRechazarSubmit(e: FormEvent) {
    e.preventDefault()
    if (!rejectingUserId) return
    if (motivoRechazo.trim().length < 10) {
      setActionErrorMsg('El motivo de rechazo debe tener al menos 10 caracteres.')
      return
    }
    setActionSuccessMsg(null)
    setActionErrorMsg(null)
    try {
      await apiClient.post(`/v1/admin/usuarios/${rejectingUserId}/rechazar`, {
        motivo_rechazo: motivoRechazo.trim(),
      })
      setActionSuccessMsg('Cuenta rechazada correctamente.')
      setRejectingUserId(null)
      setMotivoRechazo('')
      fetchPendientes()
    } catch (err) {
      setActionErrorMsg((err as ApiCallError).code)
    }
  }

  // Actualizar parámetro
  async function handleGuardarParametro(clave: string) {
    setSavingParametro(true)
    setErrorParametros(null)
    try {
      // Intentar parsear el valor como float/int si parece numérico, o bool
      let parsedValue: any = editingValor
      if (editingValor.toLowerCase() === 'true') parsedValue = true
      else if (editingValor.toLowerCase() === 'false') parsedValue = false
      else if (/^\d+$/.test(editingValor)) parsedValue = parseInt(editingValor, 10)
      else if (/^\d*\.\d+$/.test(editingValor)) parsedValue = parseFloat(editingValor)

      await apiClient.patch(`/v1/admin/parametros/${clave}`, { valor: parsedValue })
      setEditingClave(null)
      fetchParametros()
    } catch (err) {
      setErrorParametros((err as ApiCallError).code)
    } finally {
      setSavingParametro(false)
    }
  }

  if (!user) return null

  // Filtro cliente de usuarios por búsqueda de texto
  const usuariosFiltrados = usuarios.filter(u => {
    const q = searchQuery.toLowerCase()
    return u.nombre.toLowerCase().includes(q) || u.email.toLowerCase().includes(q) || u.usuario_id.toLowerCase().includes(q)
  })

  return (
    <div className="min-h-screen bg-surface-dark text-slate-100 font-sans">
      <SessionExpiredHandler rol="SUPERADMIN" />

      {/* CABECERA (Header) con Impersonación (DEP-10-001) */}
      <DashboardHeader
        userId={user.id}
        rol="SUPERADMIN"
        onLogout={logout}
        extraAction={
          <div className="hidden sm:flex items-center gap-2">
            <input
              type="text"
              placeholder="ID Usuario..."
              disabled
              value={impersonationId}
              onChange={e => setImpersonationId(e.target.value)}
              className="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-xs font-mono text-slate-400 placeholder-slate-600 focus:outline-none cursor-not-allowed"
            />
            <button
              disabled
              title="Deshabilitado temporalmente (DEP-10-001)"
              className="px-3 py-1 rounded bg-slate-800 border border-slate-700 text-xs font-body text-slate-500 cursor-not-allowed hover:bg-slate-700/50"
            >
              Impersonar
            </button>
          </div>
        }
      />

      <div className="flex flex-col md:flex-row">
        {/* MOBILE SECTION SELECTOR */}
        <div className="md:hidden p-6 pb-0">
          <label htmlFor="mobile-section-select" className="block text-xs text-slate-500 font-body mb-1">
            Sección actual:
          </label>
          <select
            id="mobile-section-select"
            value={seccion}
            onChange={e => handleSetSeccion(e.target.value as any)}
            className="w-full px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-semibold font-body focus:outline-none focus:ring-2 focus:ring-teal"
          >
            {(['Catálogo', 'Categorías', 'Stock', 'Pedidos', 'Taller', 'Admin', 'Logs y config'] as const).map(m => (
              <option key={m} value={m}>
                {m === 'Logs y config' ? 'Logs y config (Inicio)' : m}
              </option>
            ))}
          </select>
        </div>

        {/* SIDEBAR NAVIGATION */}
        <nav className="hidden md:flex flex-col w-56 shrink-0 border-r border-slate-800 min-h-[calc(100vh-56px)] p-4 gap-1.5 bg-slate-900/40">
          {(['Catálogo', 'Categorías', 'Stock', 'Pedidos', 'Taller', 'Admin', 'Logs y config'] as const).map(m => (
            <button
              key={m}
              onClick={() => handleSetSeccion(m)}
              className={`text-left px-3 py-2 rounded-lg text-sm font-body transition-all duration-200 ${
                seccion === m
                  ? 'bg-teal/15 text-teal font-semibold border-l-4 border-teal'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
              }`}
            >
              {m}
            </button>
          ))}
        </nav>

        {/* CONTENEDOR PRINCIPAL */}
        <main className="flex-1 p-6 space-y-6 max-w-7xl">

          {/* 1. SECCIÓN: LOGS Y CONFIG (Métricas y Estado) */}
          {seccion === 'Logs y config' && (
            <div className="space-y-6">
              <div>
                <h1 className="font-display text-2xl font-bold text-slate-100">Centro de comando Superadmin</h1>
                <p className="text-sm text-slate-400 font-body">Estado técnico y métricas de facturación agregadas en tiempo real.</p>
              </div>

              {loadingMetrics ? (
                <LoadingIndicator message="Obteniendo métricas en tiempo real..." />
              ) : errorMetrics ? (
                <ErrorDisplay code={errorMetrics} onRetry={fetchMetrics} />
              ) : (
                <div className="space-y-8">
                  {/* Métricas de Negocio (EP-ADM-10) */}
                  {bizMetrics && (
                    <div>
                      <h2 className="font-display text-lg font-semibold text-slate-200 mb-4 border-b border-slate-800 pb-1.5 flex items-center justify-between">
                        <span>Métricas de Negocio</span>
                        <span className="text-xs font-body text-slate-500 font-normal">
                          Período: {bizMetrics.periodo_comprobantes.desde} al {bizMetrics.periodo_comprobantes.hasta}
                        </span>
                      </h2>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {/* Suma Facturación */}
                        <div className="rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/80 p-5 shadow-lg relative overflow-hidden group">
                          <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">Facturación Emitida (SUNAT)</p>
                          <p className="text-3xl lg:text-4xl font-mono text-teal font-extrabold tracking-tight">
                            S/ {bizMetrics.comprobantes_emitidos_mes_actual.toLocaleString('es-PE', { minimumFractionDigits: 2 })}
                          </p>
                          <div className="absolute bottom-0 right-0 w-24 h-24 bg-teal/5 rounded-full blur-2xl group-hover:bg-teal/10 transition-colors"></div>
                        </div>

                        {/* OTs Activas */}
                        <div className="rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/80 p-5 shadow-lg relative overflow-hidden group">
                          <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">Órdenes de Trabajo Activas</p>
                          <p className="text-4xl lg:text-5xl font-mono text-electric font-extrabold tracking-tight">
                            {bizMetrics.ots_activas}
                          </p>
                          <div className="absolute bottom-0 right-0 w-24 h-24 bg-electric/5 rounded-full blur-2xl group-hover:bg-electric/10 transition-colors"></div>
                        </div>

                        {/* Pedidos hoy */}
                        <div className="rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/80 p-5 shadow-lg relative overflow-hidden group">
                          <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">Pedidos de Hoy</p>
                          <p className="text-4xl lg:text-5xl font-mono text-slate-200 font-extrabold tracking-tight">
                            {bizMetrics.pedidos_activos_hoy}
                          </p>
                          <div className="absolute bottom-0 right-0 w-24 h-24 bg-slate-200/5 rounded-full blur-2xl group-hover:bg-slate-200/10 transition-colors"></div>
                        </div>

                        {/* Stock Crítico */}
                        <div className={`rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border p-5 shadow-lg relative overflow-hidden group ${
                          bizMetrics.repuestos_bajo_umbral > 0 ? 'border-red-500/40 bg-red-950/5' : 'border-slate-700/80'
                        }`}>
                          <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">Stock Bajo Umbral Mínimo</p>
                          <p className={`text-4xl lg:text-5xl font-mono font-extrabold tracking-tight ${
                            bizMetrics.repuestos_bajo_umbral > 0 ? 'text-red-400' : 'text-slate-200'
                          }`}>
                            {bizMetrics.repuestos_bajo_umbral}
                          </p>
                          <div className="absolute bottom-0 right-0 w-24 h-24 bg-red-500/5 rounded-full blur-2xl"></div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Métricas Operacionales (EP-ADM-11) */}
                  {opMetrics && (
                    <div className="space-y-4">
                      <h2 className="font-display text-lg font-semibold text-slate-200 mb-4 border-b border-slate-800 pb-1.5 flex items-center justify-between">
                        <span>Métricas de Rendimiento Operacional</span>
                      </h2>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        {/* Rotación de Stock */}
                        <div className="rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/80 p-5 shadow-lg relative overflow-hidden group">
                          <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">Rotación de Stock (30d)</p>
                          <p className="text-3xl lg:text-4xl font-mono text-teal font-extrabold tracking-tight">
                            {opMetrics.rotacion_stock}x
                          </p>
                          <div className="absolute bottom-0 right-0 w-24 h-24 bg-teal/5 rounded-full blur-2xl group-hover:bg-teal/10 transition-colors"></div>
                        </div>

                        {/* Margen Promedio */}
                        <div className="rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/80 p-5 shadow-lg relative overflow-hidden group">
                          <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">Margen Promedio del Catálogo</p>
                          <p className="text-3xl lg:text-4xl font-mono text-electric font-extrabold tracking-tight">
                            {opMetrics.margen_promedio}%
                          </p>
                          <div className="absolute bottom-0 right-0 w-24 h-24 bg-electric/5 rounded-full blur-2xl group-hover:bg-electric/10 transition-colors"></div>
                        </div>

                        {/* Tasa de Conversión */}
                        <div className="rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/80 p-5 shadow-lg relative overflow-hidden group">
                          <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1.5">Tasa de Conversión del Taller</p>
                          <p className="text-3xl lg:text-4xl font-mono text-slate-200 font-extrabold tracking-tight">
                            {opMetrics.tasa_conversion}%
                          </p>
                          <div className="absolute bottom-0 right-0 w-24 h-24 bg-slate-200/5 rounded-full blur-2xl group-hover:bg-slate-200/10 transition-colors"></div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Métricas Técnicas (EP-OBS-01) */}
                  {metrics && (
                    <div>
                      <h2 className="font-display text-lg font-semibold text-slate-200 mb-4 border-b border-slate-800 pb-1.5">
                        Métricas de Infraestructura y Tráfico
                      </h2>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {Object.entries(metrics).map(([k, v]) => (
                          <div key={k} className="rounded-xl bg-slate-800 border border-slate-700/60 p-4">
                            <p className="text-xs text-slate-400 font-body uppercase tracking-wider mb-1">
                              {k.replace(/_/g, ' ')}
                            </p>
                            <p className="text-2xl font-mono text-teal font-bold">{String(v)}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 2. SECCIÓN: ADMIN (Usuarios, Pendientes, Parámetros) */}
          {seccion === 'Admin' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
                <div className="flex gap-2">
                  {(['usuarios', 'pendientes', 'parametros'] as const).map(tab => (
                    <button
                      key={tab}
                      onClick={() => setAdminTab(tab)}
                      className={`px-4 py-2 rounded-lg text-sm font-body transition-colors ${
                        adminTab === tab
                          ? 'bg-slate-800 text-teal font-semibold'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                      }`}
                    >
                      {tab === 'usuarios'
                        ? 'Usuarios Generales'
                        : tab === 'pendientes'
                        ? 'Cuentas Pendientes'
                        : 'Parámetros del Sistema'}
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => {
                    if (adminTab === 'usuarios') fetchUsuarios()
                    if (adminTab === 'pendientes') fetchPendientes()
                    if (adminTab === 'parametros') fetchParametros()
                  }}
                  className="text-xs text-teal font-body hover:underline self-start sm:self-center"
                >
                  Actualizar Datos
                </button>
              </div>

              {/* A: Tab Usuarios Generales (EP-ADM-09) */}
              {adminTab === 'usuarios' && (
                <div className="space-y-4">
                  {/* Controles de Búsqueda y Filtro */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-900/30 p-3 rounded-lg border border-slate-800">
                    <div>
                      <label className="text-xs text-slate-500 font-body block mb-1">Buscar por nombre o correo</label>
                      <input
                        type="search"
                        placeholder="Buscar..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        className="w-full px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs font-body focus:outline-none focus:ring-1 focus:ring-teal"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-500 font-body block mb-1">Filtrar por Rol</label>
                      <select
                        value={rolFilter}
                        onChange={e => setRolFilter(e.target.value)}
                        className="w-full px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs font-body focus:outline-none focus:ring-1 focus:ring-teal"
                      >
                        <option value="ALL">Todos los roles</option>
                        {Object.entries(ROL_LABELS).map(([k, v]) => (
                          <option key={k} value={k}>{v}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-slate-500 font-body block mb-1">Filtrar por Estado de Cuenta</label>
                      <select
                        value={estadoFilter}
                        onChange={e => setEstadoFilter(e.target.value)}
                        className="w-full px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs font-body focus:outline-none focus:ring-1 focus:ring-teal"
                      >
                        <option value="ALL">Todos los estados</option>
                        {Object.entries(ESTADO_CUENTA_LABELS).map(([k, v]) => (
                          <option key={k} value={k}>{v}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {loadingUsuarios ? (
                    <LoadingIndicator message="Cargando usuarios..." />
                  ) : errorUsuarios ? (
                    <ErrorDisplay code={errorUsuarios} onRetry={fetchUsuarios} />
                  ) : usuariosFiltrados.length === 0 ? (
                    <EmptyState
                      title="Sin usuarios coincidentes"
                      description="No hay registros que coincidan con los filtros aplicados."
                    />
                  ) : (
                    <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-850">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead className="bg-slate-800 text-slate-400 font-body border-b border-slate-800">
                          <tr>
                            <th className="px-4 py-3 font-semibold">Usuario ID</th>
                            <th className="px-4 py-3 font-semibold">Nombre</th>
                            <th className="px-4 py-3 font-semibold">Email</th>
                            <th className="px-4 py-3 font-semibold">Rol</th>
                            <th className="px-4 py-3 font-semibold">Estado</th>
                            <th className="px-4 py-3 font-semibold">Variante Tema</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {usuariosFiltrados.map(u => (
                            <tr key={u.usuario_id} className="hover:bg-slate-800/40">
                              <td className="px-4 py-2.5 font-mono text-slate-300 truncate max-w-[140px]">{u.usuario_id}</td>
                              <td className="px-4 py-2.5 text-slate-200 font-semibold">{u.nombre}</td>
                              <td className="px-4 py-2.5 text-slate-400">{u.email}</td>
                              <td className="px-4 py-2.5 text-slate-300 font-body">
                                <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">
                                  {ROL_LABELS[u.rol] || u.rol}
                                </span>
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
                              </td>
                              <td className="px-4 py-2.5 font-mono text-[10px] text-slate-500">{u.variante_tema || '-'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* B: Tab Cuentas Pendientes (EP-ADM-06, 07, 08) */}
              {adminTab === 'pendientes' && (
                <div className="space-y-4">
                  {actionSuccessMsg && (
                    <div className="p-3 bg-teal/15 border border-teal/40 rounded-lg text-teal text-xs font-body">
                      {actionSuccessMsg}
                    </div>
                  )}
                  {actionErrorMsg && (
                    <div className="p-3 bg-red-500/15 border border-red-500/40 rounded-lg text-red-400 text-xs font-body">
                      Ocurrió un error: {actionErrorMsg}
                    </div>
                  )}

                  {loadingPendientes ? (
                    <LoadingIndicator message="Obteniendo cuentas en revisión..." />
                  ) : errorPendientes ? (
                    <ErrorDisplay code={errorPendientes} onRetry={fetchPendientes} />
                  ) : pendientes.length === 0 ? (
                    <EmptyState
                      title="Sin revisiones pendientes"
                      description="No hay cuentas en estado PENDIENTE_DOCUMENTOS o EN_REVISION."
                    />
                  ) : (
                    <div className="grid grid-cols-1 gap-4">
                      {pendientes.map(u => (
                        <div key={u.usuario_id} className="rounded-xl bg-slate-800 border border-slate-700/80 p-5 shadow space-y-4">
                          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                            <div>
                              <p className="text-xs text-slate-500 font-mono mb-0.5">{u.usuario_id}</p>
                              <h3 className="text-slate-100 font-semibold text-base">{u.nombre}</h3>
                              <p className="text-sm text-slate-400 font-body mb-2">{u.email}</p>
                              <span className="px-2.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-xs text-slate-300">
                                Rol solicitado: {ROL_LABELS[u.rol] || u.rol}
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleAprobar(u.usuario_id)}
                                className="px-4 py-2 rounded-lg bg-teal hover:bg-teal/95 text-white font-body text-xs font-semibold transition-colors"
                              >
                                Aprobar cuenta
                              </button>
                              <button
                                onClick={() => {
                                  setRejectingUserId(u.usuario_id)
                                  setMotivoRechazo('')
                                  setActionErrorMsg(null)
                                }}
                                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-body text-xs font-semibold transition-colors"
                              >
                                Rechazar cuenta
                              </button>
                            </div>
                          </div>

                          {/* Sección de documentos adjuntos */}
                          {u.documentos && u.documentos.length > 0 && (
                            <div className="bg-slate-900/30 p-3 rounded-lg border border-slate-700/60">
                              <p className="text-xs text-slate-400 font-semibold mb-2">Documentos adjuntos:</p>
                              <div className="flex flex-wrap gap-2">
                                {u.documentos.map((doc, idx) => (
                                  <a
                                    key={idx}
                                    href={doc.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="px-2.5 py-1.5 rounded bg-slate-800 border border-slate-750 text-[11px] text-teal font-body hover:bg-slate-750 transition-colors flex items-center gap-1.5"
                                  >
                                    <span className="font-semibold uppercase">{doc.tipo.replace(/_/g, ' ')}</span>
                                    <span className="text-slate-500 font-mono">(abrir)</span>
                                  </a>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Formulario inline de motivo de rechazo */}
                          {rejectingUserId === u.usuario_id && (
                            <form onSubmit={handleRechazarSubmit} className="bg-slate-900/50 p-4 rounded-lg border border-red-500/30 space-y-3">
                              <p className="text-xs text-red-400 font-body font-semibold">Motivo del rechazo de registro:</p>
                              <textarea
                                value={motivoRechazo}
                                onChange={e => setMotivoRechazo(e.target.value)}
                                placeholder="Indica detalladamente por qué se rechaza la solicitud (mínimo 10 caracteres)..."
                                className="w-full h-20 p-2.5 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs font-body focus:outline-none focus:ring-1 focus:ring-red-500"
                                required
                              />
                              <div className="flex justify-end gap-2">
                                <button
                                  type="button"
                                  onClick={() => setRejectingUserId(null)}
                                  className="px-3 py-1.5 rounded border border-slate-700 text-slate-400 hover:text-slate-200 text-xs font-body"
                                >
                                  Cancelar
                                </button>
                                <button
                                  type="submit"
                                  className="px-4 py-1.5 rounded bg-red-600 hover:bg-red-500 text-white font-body text-xs font-semibold transition-colors"
                                >
                                  Confirmar Rechazo
                                </button>
                              </div>
                            </form>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* C: Tab Parámetros del Sistema (EP-ADM-01, 02) */}
              {adminTab === 'parametros' && (
                <div className="space-y-4">
                  {loadingParametros ? (
                    <LoadingIndicator message="Consultando parámetros del sistema..." />
                  ) : errorParametros ? (
                    <ErrorDisplay code={errorParametros} onRetry={fetchParametros} />
                  ) : parametros.length === 0 ? (
                    <EmptyState title="Sin parámetros" description="No hay parámetros de sistema configurados." />
                  ) : (
                    <div className="space-y-3">
                      {parametros.map(p => {
                        const isEditing = editingClave === p.clave
                        const canEdit = user.rol === 'SUPERADMIN' || p.modificable_por === 'ADMINISTRADOR'
                        const info = PARAM_INFO[p.clave] || { title: p.clave, desc: 'Sin descripción detallada.' }

                        return (
                          <div key={p.clave} className="rounded-xl bg-slate-800 border border-slate-700/80 p-4 space-y-2">
                            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                              <div>
                                <h3 className="text-sm font-semibold text-slate-200">{info.title}</h3>
                                <p className="text-xs text-slate-500 font-mono">{p.clave}</p>
                              </div>

                              <div className="flex items-center gap-2">
                                <span className={`px-2 py-0.5 rounded text-[9px] font-semibold uppercase ${
                                  p.modificable_por === 'SUPERADMIN' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-slate-700 text-slate-300'
                                }`}>
                                  Modificable por: {p.modificable_por}
                                </span>

                                {!isEditing && canEdit && (
                                  <button
                                    onClick={() => {
                                      setEditingClave(p.clave)
                                      setEditingValor(String(p.valor))
                                    }}
                                    className="px-2.5 py-1 rounded bg-slate-900 border border-slate-750 text-xs text-teal hover:bg-slate-750"
                                  >
                                    Editar
                                  </button>
                                )}
                              </div>
                            </div>

                            <p className="text-xs text-slate-400 font-body">{info.desc}</p>

                            <div className="mt-2 pt-2 border-t border-slate-750 flex items-center justify-between">
                              <span className="text-xs text-slate-500 font-body">Valor actual:</span>
                              {isEditing ? (
                                <div className="flex items-center gap-2 w-full max-w-md justify-end">
                                  <input
                                    type="text"
                                    value={editingValor}
                                    onChange={e => setEditingValor(e.target.value)}
                                    className="px-3 py-1 rounded bg-slate-900 border border-slate-700 text-xs font-mono text-slate-200 focus:outline-none focus:ring-1 focus:ring-teal w-44 text-right"
                                  />
                                  <button
                                    disabled={savingParametro}
                                    onClick={() => handleGuardarParametro(p.clave)}
                                    className="px-3 py-1 rounded bg-teal text-white text-xs font-semibold hover:bg-teal/95 font-body"
                                  >
                                    {savingParametro ? 'Guardando...' : 'Guardar'}
                                  </button>
                                  <button
                                    disabled={savingParametro}
                                    onClick={() => setEditingClave(null)}
                                    className="px-2.5 py-1 rounded border border-slate-700 text-slate-400 hover:text-slate-200 text-xs font-body"
                                  >
                                    Cancelar
                                  </button>
                                </div>
                              ) : (
                                <span className="text-sm font-mono text-teal font-semibold">{String(p.valor)}</span>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 3. SECCIÓN: CATÁLOGO (Consulta) */}
          {seccion === 'Catálogo' && (
            <div className="space-y-6">
              <div>
                <h1 className="font-display text-2xl font-bold text-slate-100">Catálogo de Repuestos</h1>
                <p className="text-sm text-slate-400 font-body">Consulta y verificación de repuestos.</p>
              </div>

              <form onSubmit={fetchCatalogo} className="flex gap-2 max-w-lg">
                <input
                  type="search"
                  placeholder="Código o nombre del repuesto..."
                  value={catalogoSearch}
                  onChange={e => setCatalogoSearch(e.target.value)}
                  className="flex-1 px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 text-sm font-body focus:outline-none focus:ring-2 focus:ring-teal"
                />
                <button
                  type="submit"
                  className="px-4 py-2.5 rounded-xl bg-teal text-white text-sm font-semibold hover:bg-teal/95 transition-colors font-body"
                >
                  Buscar
                </button>
              </form>

              {loadingCatalogo ? (
                <LoadingIndicator message="Buscando repuestos..." />
              ) : errorCatalogo ? (
                <ErrorDisplay code={errorCatalogo} onRetry={() => fetchCatalogo()} />
              ) : catalogoRepuestos.length === 0 ? (
                <EmptyState title="Catálogo vacío" description="Utiliza el buscador para encontrar repuestos de mototaxis." />
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {catalogoRepuestos.map(r => (
                    <div key={r.codigo} className="rounded-xl bg-slate-800 border border-slate-700 p-4 space-y-3">
                      <div>
                        <p className="text-xs text-slate-500 font-mono">{r.codigo}</p>
                        <h3 className="text-sm font-semibold text-slate-100 truncate">{r.nombre}</h3>
                        <p className="text-xs text-slate-400 font-body mt-1">
                          Categoría: <span className="font-semibold text-slate-300">{r.categoria?.replace(/_/g, ' ') || 'Sin categoría'}</span>
                        </p>
                      </div>
                      <div className="flex items-center justify-between border-t border-slate-750 pt-2">
                        <span className="text-xs text-slate-500 font-body">Precio Venta:</span>
                        <span className="text-sm font-mono text-teal font-semibold">S/ {r.precio_venta?.toFixed(2) || '0.00'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {seccion === 'Categorías' && <CategoriasManager />}

          {/* 4. SECCIÓN: STOCK */}
          {seccion === 'Stock' && (
            <div className="space-y-6">
              <div>
                <h1 className="font-display text-2xl font-bold text-slate-100">Control de Stock</h1>
                <p className="text-sm text-slate-400 font-body">Estado actual de inventario y alertas por debajo del umbral.</p>
              </div>

              {loadingStock ? (
                <LoadingIndicator message="Cargando existencias..." />
              ) : errorStock ? (
                <ErrorDisplay code={errorStock} onRetry={fetchStock} />
              ) : stockItems.length === 0 ? (
                <EmptyState title="Sin registros de stock" description="Registra repuestos en el catálogo para ver niveles de stock." />
              ) : (
                <div className="space-y-6">
                  {/* Alertas */}
                  {stockItems.some(s => s.esta_bajo_umbral) && (
                    <div className="space-y-2">
                      <h2 className="text-sm font-semibold text-red-400 font-body">Alertas Críticas de Stock</h2>
                      <div className="rounded-xl border border-red-500/25 bg-red-950/5 overflow-hidden divide-y divide-slate-800">
                        {stockItems.filter(s => s.esta_bajo_umbral).map(s => (
                          <div key={s.codigo} className="flex justify-between items-center px-4 py-3">
                            <span className="font-mono text-sm text-slate-200">{s.codigo}</span>
                            <div className="text-right">
                              <span className="text-sm font-mono text-red-400 font-semibold">{s.cantidad_disponible} unidades</span>
                              <p className="text-[10px] text-slate-500 font-body">mínimo: {s.umbral_minimo}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Tabla General */}
                  <div className="space-y-2">
                    <h2 className="text-sm font-semibold text-slate-300 font-body">Inventario General</h2>
                    <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-855">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead className="bg-slate-800 text-slate-400 font-body border-b border-slate-800">
                          <tr>
                            <th className="px-4 py-3 font-semibold">Código</th>
                            <th className="px-4 py-3 font-semibold text-right">Disponible</th>
                            <th className="px-4 py-3 font-semibold text-right">Apartada</th>
                            <th className="px-4 py-3 font-semibold text-right">Umbral Mínimo</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {stockItems.map(s => (
                            <tr key={s.codigo} className={`hover:bg-slate-800/30 ${s.esta_bajo_umbral ? 'bg-red-500/5' : ''}`}>
                              <td className="px-4 py-2.5 font-mono text-slate-200">{s.codigo}</td>
                              <td className="px-4 py-2.5 text-right font-mono font-semibold text-slate-200">{s.cantidad_disponible}</td>
                              <td className="px-4 py-2.5 text-right font-mono text-slate-400">{s.cantidad_apartada}</td>
                              <td className="px-4 py-2.5 text-right font-mono text-slate-400">{s.umbral_minimo}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 5. SECCIÓN: PEDIDOS */}
          {seccion === 'Pedidos' && (
            <div className="space-y-6">
              <div>
                <h1 className="font-display text-2xl font-bold text-slate-100">Bandeja de Pedidos</h1>
                <p className="text-sm text-slate-400 font-body">Monitoreo de pedidos y transiciones de compra.</p>
              </div>

              {loadingPedidos ? (
                <LoadingIndicator message="Recuperando pedidos..." />
              ) : errorPedidos ? (
                <ErrorDisplay code={errorPedidos} onRetry={fetchPedidos} />
              ) : pedidosItems.length === 0 ? (
                <EmptyState title="Sin pedidos" description="No hay pedidos registrados en el sistema." />
              ) : (
                <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-855">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-800 text-slate-400 font-body border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-3 font-semibold">ID Pedido</th>
                        <th className="px-4 py-3 font-semibold">Canal</th>
                        <th className="px-4 py-3 font-semibold">Estado</th>
                        <th className="px-4 py-3 font-semibold text-right">Monto Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {pedidosItems.map(p => (
                        <tr key={p.pedido_id} className="hover:bg-slate-800/40">
                          <td className="px-4 py-2.5 font-mono text-slate-200">{p.pedido_id}</td>
                          <td className="px-4 py-2.5 text-slate-400 uppercase font-mono text-[10px]">{p.canal_origen || '-'}</td>
                          <td className="px-4 py-2.5">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-body ${
                              p.estado === 'CONFIRMADO' ? 'bg-teal/20 text-teal' :
                              p.estado === 'BORRADOR' ? 'bg-slate-700 text-slate-400' :
                              'bg-electric/20 text-electric'
                            }`}>
                              {p.estado?.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-right font-mono font-semibold text-slate-200">
                            {p.monto_total != null ? `S/ ${p.monto_total.toFixed(2)}` : 'En revisión'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* 6. SECCIÓN: TALLER */}
          {seccion === 'Taller' && (
            <div className="space-y-6">
              <div>
                <h1 className="font-display text-2xl font-bold text-slate-100">Bandeja de Taller</h1>
                <p className="text-sm text-slate-400 font-body">Supervisión del estado de las ordenes de trabajo.</p>
              </div>

              <section className="rounded-xl bg-slate-800/50 border border-slate-800 p-8 text-center">
                <p className="text-slate-400 font-body text-sm">
                  Módulo de Taller — disponible próximamente para visualización masiva.
                </p>
              </section>
            </div>
          )}

        </main>
      </div>
    </div>
  )
}

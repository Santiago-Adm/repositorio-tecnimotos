'use client'

import { useEffect, useState, FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/src/context/AuthContext'
import { apiClient } from '@/src/lib/api-client'
import { ApiCallError, Rol } from '@/src/lib/types'
import DashboardHeader from '@/src/components/dashboard/DashboardHeader'
import CategoriasManager from '@/src/components/dashboard/CategoriasManager'
import SuperadminResumenTab from '@/src/components/dashboard/SuperadminResumenTab'
import BiPanel from '@/src/components/dashboard/BiPanel'
import UsuariosManager from '@/src/components/dashboard/UsuariosManager'
import CatalogoConsultaTab from '@/src/components/dashboard/CatalogoConsultaTab'
import StockConsultaTab from '@/src/components/dashboard/StockConsultaTab'
import PedidosBandejaTab from '@/src/components/dashboard/PedidosBandejaTab'
import LoadingIndicator from '@/src/components/LoadingIndicator'
import ErrorDisplay from '@/src/components/ErrorDisplay'
import EmptyState from '@/src/components/EmptyState'
import SessionExpiredHandler from '@/src/components/SessionExpiredHandler'
import AppSidebarNav from '@/src/components/dashboard/AppSidebarNav'

type Seccion = 'Resumen' | 'Panel BI' | 'Catálogo' | 'Categorías' | 'Stock' | 'Pedidos' | 'Taller' | 'Admin' | 'Logs y config'

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
  comprobantes_emitidos_periodo: number
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
  const [seccion, setSeccion] = useState<Seccion>('Resumen')
  const [adminTab, setAdminTab] = useState<'usuarios' | 'pendientes' | 'parametros'>('usuarios')

  // Sincronizar sección con URL query params para navegación y persistencia (evita pérdida de estado en refresco)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const secParam = params.get('seccion')
      const validSections: Array<Seccion> = [
        'Resumen', 'Panel BI', 'Catálogo', 'Categorías', 'Stock', 'Pedidos', 'Taller', 'Admin', 'Logs y config'
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

  // Nota: el estado de "Usuarios Generales" (listado/filtros/búsqueda) ahora
  // vive en UsuariosManager.tsx (componente compartido, ADR-016).

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

  // Efecto desencadenado al cambiar de Sección
  useEffect(() => {
    if (seccion === 'Admin') {
      if (adminTab === 'pendientes') fetchPendientes()
      if (adminTab === 'parametros') fetchParametros()
    } else if (seccion === 'Logs y config') {
      fetchMetrics()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seccion, adminTab])

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
        {/* Navegación (Pieza F: sidebar+drawer compartido, reemplaza el
            <select> de respaldo mobile y el <nav> hidden md:flex previos) */}
        <AppSidebarNav
          secciones={['Resumen', 'Panel BI', 'Catálogo', 'Categorías', 'Stock', 'Pedidos', 'Taller', 'Admin', 'Logs y config']}
          activa={seccion}
          onSeleccionar={s => handleSetSeccion(s as Seccion)}
        />

        {/* CONTENEDOR PRINCIPAL */}
        <main className="flex-1 min-w-0 p-6 space-y-6 max-w-7xl">

          {/* 0. SECCIÓN: RESUMEN (Referencia 1 — sesión dashboards deterministas) */}
          {seccion === 'Resumen' && <SuperadminResumenTab />}

          {/* 0.1 SECCIÓN: PANEL BI (ADR-015 — filtros premium, mismo nivel que ADMINISTRADOR) */}
          {seccion === 'Panel BI' && <BiPanel />}

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
                            S/ {bizMetrics.comprobantes_emitidos_periodo.toLocaleString('es-PE', { minimumFractionDigits: 2 })}
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
                    if (adminTab === 'pendientes') fetchPendientes()
                    if (adminTab === 'parametros') fetchParametros()
                  }}
                  className="text-xs text-teal font-body hover:underline self-start sm:self-center"
                >
                  Actualizar Datos
                </button>
              </div>

              {/* A: Tab Usuarios Generales (EP-ADM-09 + EP-ADM-14/15/16, ADR-016) */}
              {adminTab === 'usuarios' && <UsuariosManager />}

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
          {seccion === 'Catálogo' && <CatalogoConsultaTab />}

          {seccion === 'Categorías' && <CategoriasManager />}

          {/* 4. SECCIÓN: STOCK */}
          {seccion === 'Stock' && <StockConsultaTab />}

          {/* 5. SECCIÓN: PEDIDOS */}
          {seccion === 'Pedidos' && <PedidosBandejaTab />}

          {/* 6. SECCIÓN: TALLER */}
          {seccion === 'Taller' && (
            <div className="space-y-6">
              <div>
                <h1 className="font-display text-2xl font-bold text-slate-100">Bandeja de Taller</h1>
                <p className="text-sm text-slate-400 font-body">Supervisión del estado de las ordenes de trabajo.</p>
              </div>

              <section className="rounded-xl bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-slate-800/60 shadow-[0_4px_20px_-8px_rgba(0,0,0,0.3)] p-8 text-center">
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

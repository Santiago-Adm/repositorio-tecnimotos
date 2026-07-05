'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useAuth } from '@/src/context/AuthContext'
import { ApiCallError, ImagenResumen, isClienteRol } from '@/src/lib/types'
import { consultarPrecio, PrecioResult } from '@/src/lib/precio'
import { useReservar } from '@/src/lib/useReservar'

interface RepuestoCardProps {
  codigo: string
  nombre: string
  imagenUrl?: string | null
  /** Galería completa ordenada (ADR-012) — cuando está presente y tiene más de
   *  una imagen, GridCard muestra un carrusel en vez de la imagen única. */
  imagenes?: ImagenResumen[]
  disponible?: boolean
  extra?: React.ReactNode
  /** 'compact' = fila angosta para dashboards (default, comportamiento sin cambios).
   *  'grid' = tarjeta grande para landings/catálogo público — precio oculto (2.1)
   *  y flujo de reserva con auth (2.2) embebidos. */
  variant?: 'compact' | 'grid'
  /** Requerido en variant='grid' para poder llamar POST /v1/reservas. */
  repuestoId?: string
  universo?: string
  modelo?: string
  /** Superficie del contenedor donde vive la tarjeta (03 §3.3.1) — landings/catálogo
   *  son surface-light, el escaparate de home es surface-dark. */
  surface?: 'light' | 'dark'
  /** Payload mínimo S4/rural (10 §2.3/§6.6): sin imagen, sin consulta de precio. */
  minimal?: boolean
}

export default function RepuestoCard(props: RepuestoCardProps) {
  const { variant = 'compact' } = props
  return variant === 'grid' ? <GridCard {...props} /> : <CompactCard {...props} />
}

function CompactCard({ codigo, nombre, imagenUrl, disponible, extra }: RepuestoCardProps) {
  const [imgError, setImgError] = useState(false)
  const showImage = imagenUrl && !imgError

  return (
    <div className="rounded-xl bg-slate-800 border border-slate-700 overflow-hidden flex items-center gap-3 p-3">
      <div className="w-12 h-12 shrink-0 rounded-lg overflow-hidden bg-gradient-to-br from-teal/20 to-electric/20 flex items-center justify-center">
        {showImage ? (
          <img
            src={imagenUrl}
            alt={nombre}
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
          />
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-teal/60" aria-hidden="true">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-xs font-mono text-slate-300 truncate">{codigo}</p>
        <p className="text-xs font-body text-slate-400 truncate mt-0.5">{nombre}</p>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {disponible !== undefined && (
          <span className={`text-xs px-2 py-1 rounded-full font-body ${
            disponible ? 'bg-teal/20 text-teal' : 'bg-red-900/30 text-red-400'
          }`}>
            {disponible ? 'Disponible' : 'Sin stock'}
          </span>
        )}
        {extra}
      </div>
    </div>
  )
}

function GridCard({
  codigo, nombre, imagenUrl, imagenes, disponible, repuestoId, universo, modelo, surface = 'light', minimal = false
}: RepuestoCardProps) {
  const { user } = useAuth()
  const [imgError, setImgError] = useState(false)
  const [indice, setIndice] = useState(0)

  const galeria = imagenes && imagenes.length > 0
    ? [...imagenes].sort((a, b) => a.orden - b.orden)
    : null
  const urlActual = galeria ? galeria[Math.min(indice, galeria.length - 1)].url : imagenUrl
  const showImage = !!urlActual && !imgError

  function irAnterior(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    if (galeria) setIndice(i => (i - 1 + galeria.length) % galeria.length)
  }

  function irSiguiente(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    if (galeria) setIndice(i => (i + 1) % galeria.length)
  }

  const [precio, setPrecio] = useState<PrecioResult | null>(null)
  const [cargandoPrecio, setCargandoPrecio] = useState(false)
  const [errorPrecio, setErrorPrecio] = useState<string | null>(null)
  const { reservar, reservandoCodigo, confirmacion, error: errorReserva } = useReservar()

  async function verPrecio() {
    setCargandoPrecio(true)
    setErrorPrecio(null)
    try {
      setPrecio(await consultarPrecio(codigo, user ? isClienteRol(user.rol) : false))
    } catch (err) {
      setErrorPrecio(err instanceof ApiCallError ? err.message : 'No se pudo consultar el precio.')
    } finally {
      setCargandoPrecio(false)
    }
  }

  const isDark = surface === 'dark'

  const containerClasses = isDark
    ? "bg-[#0b0f19]/40 border border-slate-800/80 rounded-xl overflow-hidden hover:border-teal/50 hover:shadow-[0_0_20px_rgba(13,148,136,0.15)] transition-all duration-350 group flex flex-col justify-between h-full"
    : "bg-slate-50 border border-slate-200/60 rounded-xl overflow-hidden hover:shadow-lg transition-all duration-300 group flex flex-col justify-between h-full"

  const imageContainerClasses = isDark
    ? "aspect-square w-full bg-slate-950/20 relative overflow-hidden flex items-center justify-center p-6 group border-b border-slate-800/40"
    : "aspect-square w-full bg-slate-100/80 relative overflow-hidden flex items-center justify-center p-6 group"

  const infoContainerClasses = isDark
    ? "p-4 bg-transparent rounded-b-xl flex flex-col space-y-1"
    : "p-4 bg-white rounded-b-xl flex flex-col space-y-1"

  const titleClasses = isDark
    ? "text-slate-100 font-display text-sm font-semibold tracking-wide hover:text-teal transition-colors capitalize truncate"
    : "text-slate-900 font-semibold text-sm tracking-tight capitalize truncate"

  const metaClasses = isDark
    ? "text-slate-500 text-[10px] font-mono tracking-wider uppercase mt-1"
    : "text-slate-400 text-[11px] font-mono"

  const actionContainerClasses = isDark
    ? "px-4 pb-4 bg-transparent border-t border-slate-800/30 pt-3"
    : "px-4 pb-4 bg-white border-t border-slate-100 pt-3"

  return (
    <div className={containerClasses}>
      <div>
        {/* ZONA SUPERIOR: CONTENEDOR FOTOGRÁFICO DE PRODUCTO */}
        <div className={imageContainerClasses}>
          {showImage ? (
            <>
              <Image
                src={urlActual!}
                alt={nombre}
                fill
                sizes="(max-width: 768px) 100vw, 30vw"
                priority={false}
                className="object-contain p-4 transform group-hover:scale-105 transition-transform duration-500 ease-out"
                onError={() => setImgError(true)}
              />
              {galeria && galeria.length > 1 && (
                <>
                  <button
                    type="button"
                    onClick={irAnterior}
                    aria-label="Imagen anterior"
                    className="absolute left-1 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-black/40 text-white text-xs flex items-center justify-center opacity-60 md:opacity-0 md:group-hover:opacity-100 transition-opacity before:content-[''] before:absolute before:-inset-[10px]"
                  >
                    ‹
                  </button>
                  <button
                    type="button"
                    onClick={irSiguiente}
                    aria-label="Siguiente imagen"
                    className="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-black/40 text-white text-xs flex items-center justify-center opacity-60 md:opacity-0 md:group-hover:opacity-100 transition-opacity before:content-[''] before:absolute before:-inset-[10px]"
                  >
                    ›
                  </button>
                  <div className="absolute top-2 right-2 flex gap-1">
                    {galeria.map((img, i) => (
                      <span
                        key={img.imagen_id}
                        className={`w-1.5 h-1.5 rounded-full ${i === indice ? 'bg-teal' : 'bg-white/50'}`}
                      />
                    ))}
                  </div>
                </>
              )}
            </>
          ) : (
            <div className={`flex items-center justify-center w-full h-full rounded-t-xl ${isDark ? 'bg-slate-950/20' : 'bg-slate-200/50'}`}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={isDark ? "text-slate-600" : "text-slate-400"} aria-hidden="true">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
          )}

          {/* Badges Flotantes Estáticos */}
          {universo && (
            <span className={`absolute bottom-3 left-3 text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded select-none ${isDark ? 'bg-slate-950/90 text-slate-300 border border-slate-800/50' : 'bg-slate-900/90 text-white'}`}>
              {universo}
            </span>
          )}
          {disponible === false && (
            <span className="absolute bottom-3 right-3 bg-electric text-white text-[10px] font-bold px-2 py-0.5 rounded select-none">
              Sin Stock
            </span>
          )}
        </div>

        {/* ZONA INFERIOR: BASE TIPOGRÁFICA DE ALTA FIDELIDAD */}
        <div className={infoContainerClasses}>
          {/* Línea 1 (Identificación) */}
          <h3 className={titleClasses}>
            {nombre}
          </h3>

          {/* Línea 2 (Metadatos Técnicos) */}
          <p className={metaClasses}>
            Código: {codigo} · {modelo || 'Torito/King'}
          </p>

          {/* Línea 3 (Acción Comercial) */}
          <div className="pt-2">
            {(!user || minimal) ? (
              <Link
                href="/login?callbackUrl=/catalogo"
                className="text-teal font-bold text-xs hover:underline cursor-pointer flex items-center space-x-1 mt-1"
              >
                <span>Ver precio e ingresar</span>
                <span>→</span>
              </Link>
            ) : (
              <div className="flex flex-col space-y-1">
                {precio ? (
                  precio.precio_visible ? (
                    <span className="font-mono text-sm font-bold text-teal">
                      S/. {Number(precio.precio_venta).toFixed(2)}
                    </span>
                  ) : (
                    <span className="font-mono text-[10px] text-slate-500">
                      {precio.mensaje ?? 'No disponible'}
                    </span>
                  )
                ) : (
                  <button
                    onClick={verPrecio}
                    disabled={cargandoPrecio}
                    className="text-teal font-bold text-xs hover:underline disabled:opacity-50 text-left flex items-center space-x-1"
                  >
                    {cargandoPrecio ? 'Consultando...' : 'Ver precio'}
                  </button>
                )}
                {errorPrecio && <span className="text-[9px] text-red-500">{errorPrecio}</span>}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Flujo de reserva */}
      {!minimal && user && repuestoId && (
        <div className={actionContainerClasses}>
          {confirmacion?.codigo === codigo ? (
            <span className="text-xs font-mono text-teal font-bold block text-center">
              Reservado ✓ {confirmacion.reserva_id.slice(0, 8)}
            </span>
          ) : (
            <button
              onClick={() => reservar(repuestoId, codigo)}
              disabled={reservandoCodigo === codigo || disponible === false}
              className="w-full bg-teal hover:bg-teal/90 text-white font-bold text-xs rounded-lg py-2.5 shadow-sm active:scale-95 transition-all disabled:opacity-50 text-center"
            >
              {reservandoCodigo === codigo ? 'Reservando...' : disponible === false ? 'No disponible' : 'Reservar'}
            </button>
          )}
          {errorReserva && <p className="text-[9px] text-red-500 mt-1 text-center">{errorReserva}</p>}
        </div>
      )}
    </div>
  )
}

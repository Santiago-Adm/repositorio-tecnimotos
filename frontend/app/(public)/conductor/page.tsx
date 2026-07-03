'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import PublicNavbar from '@/src/components/layout/PublicNavbar'
import PublicFooter from '@/src/components/ui/PublicFooter'
import { apiClient } from '@/src/lib/api-client'

interface Repuesto {
  id: string
  codigo: string
  nombre: string
  universo: string
  modelo: string
  activo: boolean
  imagen_principal_url?: string | null
}

export default function LandingConductor() {
  const [repuestos, setRepuestos] = useState<Repuesto[] | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    apiClient.get<{ repuestos: Repuesto[] }>('/v1/repuestos?universo=mototaxi_3r')
      .then(data => {
        setRepuestos(data.repuestos.slice(0, 6))
        setCargando(false)
      })
      .catch(() => {
        // Fallback mockup data matching exactly 6 items for symmetric grid display
        setRepuestos([
          {
            id: '1',
            codigo: 'BAJ-4592',
            nombre: 'Kit de Arrancador Original',
            universo: 'mototaxi',
            modelo: 'Torito Chrome / King FI',
            activo: true,
            imagen_principal_url: null
          },
          {
            id: '2',
            codigo: 'TVS-8832',
            nombre: 'Zapata de Freno Delantera TVS King',
            universo: 'mototaxi',
            modelo: 'King Duramax 200',
            activo: true,
            imagen_principal_url: null
          },
          {
            id: '3',
            codigo: 'BAJ-1024',
            nombre: 'Filtro de Aire Torito Cromado',
            universo: 'mototaxi',
            modelo: 'RE 205',
            activo: true,
            imagen_principal_url: null
          },
          {
            id: '4',
            codigo: 'BAJ-2201',
            nombre: 'Bujía Bajaj RE Autotaxi',
            universo: 'mototaxi',
            modelo: 'Torito 2T / 4S',
            activo: true,
            imagen_principal_url: null
          },
          {
            id: '5',
            codigo: 'TVS-1982',
            nombre: 'Cable de Acelerador Reforzado',
            universo: 'mototaxi',
            modelo: 'King Deluxe FI',
            activo: true,
            imagen_principal_url: null
          },
          {
            id: '6',
            codigo: 'BAJ-6604',
            nombre: 'Amortiguador Hidráulico Posterior',
            universo: 'mototaxi',
            modelo: 'Torito / Universal',
            activo: true,
            imagen_principal_url: null
          }
        ])
        setCargando(false)
      })
  }, [])

  return (
    <div className="flex flex-col min-h-screen bg-surface-dark text-slate-150 selection:bg-teal/30">
      <PublicNavbar />

      {/* SECCIÓN A: HERO PREMIUM CON VIDEO DINÁMICO */}
      <section className="relative w-full h-[55vh] bg-[#0F172A] overflow-hidden flex items-center justify-center border-b border-slate-800/40">
        {/* Video en loop de fondo */}
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover opacity-25 select-none pointer-events-none"
        >
          <source src="/videos/transicion-conductor.webm" type="video/webm" />
        </video>

        {/* Gradiente Overlay de cine */}
        <div className="absolute inset-0 bg-gradient-to-t from-surface-dark via-surface-dark/50 to-surface-dark/90" />

        {/* Contenido flotante */}
        <div className="relative z-10 flex flex-col items-center text-center px-4 max-w-4xl space-y-6">
          <h1 className="font-display text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight max-w-3xl drop-shadow-md">
            Reserva tu repuesto antes de salir. Con el mecánico que ya conoce tu mototaxi.
          </h1>
          <p className="font-body text-slate-300 text-sm sm:text-base md:text-lg max-w-2xl leading-relaxed drop-shadow-sm">
            Confirma stock en tiempo real. Reserva con un día de anticipación. Sin viajes a la tienda para nada.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 pt-4">
            <Link
              href="/login?from=/conductor"
              className="bg-[#0D9488] hover:bg-[#0b7a70] text-white font-bold px-8 py-3.5 rounded-xl transition-all shadow-[0_4px_15px_rgba(13,148,136,0.3)] active:scale-95 text-sm sm:text-base tracking-wide"
            >
              Ingresar a mi cuenta
            </Link>
            <Link
              href="/conductor/registro"
              className="border border-[#0D9488] text-[#0D9488] hover:bg-[#0D9488]/10 font-bold px-8 py-3.5 rounded-xl transition-all active:scale-95 text-sm sm:text-base tracking-wide"
            >
              Crear cuenta
            </Link>
          </div>
        </div>
      </section>

      {/* SECCIÓN B: GRILLA DE UTILIDADES OPERATIVAS */}
      <section className="w-full py-16 bg-[#0c1222]/20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Tarjeta 1 */}
            <div className="bg-slate-800/40 border border-slate-700/50 p-6 rounded-2xl flex flex-col space-y-3 text-white transition-all duration-300 hover:border-slate-650 hover:bg-slate-800/50">
              <div className="w-12 h-12 rounded-xl bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                </svg>
              </div>
              <h3 className="font-display font-bold text-lg text-white">Historial Mecánico en un Toque</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                ¡Tu mototaxi no se detiene! Accede al reporte exacto de tu mantenimiento y dale seguimiento a tu control de calidad en tiempo real.
              </p>
            </div>

            {/* Tarjeta 2 */}
            <div className="bg-slate-800/40 border border-slate-700/50 p-6 rounded-2xl flex flex-col space-y-3 text-white transition-all duration-300 hover:border-slate-650 hover:bg-slate-800/50">
              <div className="w-12 h-12 rounded-xl bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <ellipse cx="12" cy="5" rx="9" ry="3" />
                  <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                  <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" />
                </svg>
              </div>
              <h3 className="font-display font-bold text-lg text-white">Asegura tu Repuesto Al Instante</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                No pierdas tiempo buscando en la calle. Reserva tus piezas originales Bajaj o TVS con fotos reales de nuestro almacén y congela tu stock.
              </p>
            </div>

            {/* Tarjeta 3 */}
            <div className="bg-slate-800/40 border border-slate-700/50 p-6 rounded-2xl flex flex-col space-y-3 text-white transition-all duration-300 hover:border-slate-650 hover:bg-slate-800/50">
              <div className="w-12 h-12 rounded-xl bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              </div>
              <h3 className="font-display font-bold text-lg text-white">Auxilio en Ruta ¡Vamos a tu Rescate!</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                ¿Un imprevisto en plena jornada? Activa una alerta desde tu celular y nuestro equipo técnico certificado saldrá de inmediato a asistirte.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* SECCIÓN C: FLUJO SECUENCIAL DE ABORDAJE */}
      <section className="w-full py-16 border-t border-slate-800/30 bg-[#0c1222]/40">
        <div className="max-w-5xl mx-auto px-4">
          <h2 className="text-center text-2xl font-bold font-display text-white mb-12">Cómo empezar</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Paso 1 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-display font-bold text-lg shadow-[0_0_15px_rgba(13,148,136,0.4)]">
                1
              </div>
              <h3 className="font-display font-semibold text-base text-white">¡Regístrate y Asegura tu Respaldo!</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Crea tu cuenta de conductor en un minuto, ingresando el modelo y año de tu mototaxi para que el sistema sepa con precisión qué piezas necesitas.
              </p>
            </div>

            {/* Paso 2 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-display font-bold text-lg shadow-[0_0_15px_rgba(13,148,136,0.4)]">
                2
              </div>
              <h3 className="font-display font-semibold text-base text-white">¡Explora Piezas con Fotos Reales!</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Navega de forma libre por nuestra lista de repuestos originales con fotografías reales y actualizadas directamente desde los almacenes de nuestra tienda.
              </p>
            </div>

            {/* Paso 3 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-display font-bold text-lg shadow-[0_0_15px_rgba(13,148,136,0.4)]">
                3
              </div>
              <h3 className="font-display font-semibold text-base text-white">¡Congela tu Stock y Gana Tiempo!</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Congela tu repuesto para recogerlo en mostrador o solicita un turno de mantenimiento preventivo con nuestros mecatrónicos listos en el taller.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* SECCIÓN D: PREVIEW DE REPUESTOS MÁS SOLICITADOS */}
      <section className="w-full py-16 bg-[#0c1222]/20 border-t border-slate-800/30">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-center text-2xl font-bold font-display text-white mb-10 tracking-tight">
            Repuestos más solicitados
          </h2>
          {cargando ? (
            <div className="flex justify-center py-10">
              <span className="text-slate-400 font-body text-sm animate-pulse">Cargando repuestos...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto px-4 pb-12">
              {repuestos?.map(r => (
                <div
                  key={r.codigo}
                  className="group relative bg-slate-900/50 border border-slate-800/80 rounded-2xl p-5 flex flex-col space-y-4 overflow-hidden transition-all duration-500 ease-out [perspective:1000px] hover:[transform:rotateX(4deg)_rotateY(-4deg)_translateZ(10px)] hover:bg-slate-50 hover:shadow-[0_20px_40px_rgba(139,92,246,0.2)]"
                >
                  
                  {/* 1. MARCO DE BRILLO LED PERIMETRAL: Neon Morado-Celeste en Hover */}
                  <div className="absolute inset-0 rounded-2xl border border-transparent bg-gradient-to-r from-[#8B5CF6] via-cyan-400 to-[#0D9488] opacity-0 group-hover:opacity-100 transition-opacity duration-500 [mask:linear-gradient(#fff_0_0)_padding-box,linear-gradient(#fff_0_0)] [mask-composite:exclude] -inset-[1px] pointer-events-none" />

                  {/* 2. CONTENEDOR DE IMAGEN (OPTIMIZADO PARA CLOUDFLARE R2) */}
                  <div className="aspect-square w-full bg-slate-950/90 rounded-xl relative overflow-hidden flex items-center justify-center p-6 border border-slate-800/60 transition-colors duration-500 group-hover:bg-slate-200/60 group-hover:border-slate-300">
                    <Image
                      src={r.imagen_principal_url || "/brand/placeholder-repuesto.png"}
                      alt={r.nombre}
                      width={190}
                      height={180}
                      priority
                      className="object-contain max-h-full max-w-full transform group-hover:scale-108 transition-transform duration-500 ease-out drop-shadow-[0_4px_12px_rgba(0,0,0,0.5)] group-hover:drop-shadow-[0_4px_8px_rgba(15,23,42,0.15)]"
                    />
                    
                    {/* Badge de Categoría con Contraste Adaptativo */}
                    <span className="absolute bottom-3 left-3 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-400/40 text-cyan-300 text-[10px] font-black tracking-widest uppercase px-2.5 py-1 rounded-md font-mono transition-all duration-500 group-hover:from-purple-600/10 group-hover:to-cyan-600/10 group-hover:border-purple-600/30 group-hover:text-purple-700 shadow-[0_2px_8px_rgba(34,211,238,0.2)] group-hover:shadow-none">
                      {(r.universo || 'mototaxi').toUpperCase()}
                    </span>
                  </div>

                  {/* 3. BLOQUE DE TEXTO: Transmuta completamente a Cobalto Oscuro (#0F172A) en Hover */}
                  <div className="flex flex-col space-y-2 z-10">
                    {/* Nombre Comercial */}
                    <h4 className="text-white font-bold text-base tracking-tight font-display transition-colors duration-500 group-hover:text-[#0F172A]">
                      {r.nombre}
                    </h4>
                    
                    {/* Ficha Técnica */}
                    <div className="flex flex-col space-y-0.5 text-[11px] font-mono font-medium text-slate-400 transition-colors duration-500 group-hover:text-[#0F172A]/80">
                      <span>CÓDIGO: <span className="text-slate-200 font-semibold transition-colors duration-500 group-hover:text-[#0F172A]">{r.codigo}</span></span>
                      <span>MODELO: <span className="text-slate-200 font-semibold transition-colors duration-500 group-hover:text-[#0F172A]">{r.modelo || 'Torito Chrome / Universal'}</span></span>
                    </div>
                    
                    {/* Enlace Comercial de Conversión Protegido (Nivel 0) */}
                    <Link
                      className="inline-flex items-center text-cyan-400 font-bold text-xs tracking-wide pt-2 transition-all duration-500 group-hover:text-[#0F172A] group-hover:translate-x-1"
                      href="/login?from=/conductor"
                    >
                      Ver precio e ingresar <span className="ml-1 text-sm font-light transition-transform duration-300 group-hover:translate-x-0.5">→</span>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <PublicFooter />
    </div>
  )
}

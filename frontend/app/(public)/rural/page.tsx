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

export default function LandingRural() {
  const [repuestos, setRepuestos] = useState<Repuesto[] | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    apiClient.get<{ repuestos: Repuesto[] }>('/v1/repuestos?universo=mototaxi_3r')
      .then(data => {
        setRepuestos(data.repuestos.slice(0, 6))
        setCargando(false)
      })
      .catch(() => {
        // Fallback rural mockups for districts catalog preview
        setRepuestos([
          {
            id: '1',
            codigo: 'BAJ-4592',
            nombre: 'Kit de Arrancador Original',
            universo: 'mototaxi',
            modelo: 'Torito Chrome / Universal',
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
    <div className="flex flex-col min-h-screen bg-[#0F172A] text-slate-150 selection:bg-teal/30">
      <PublicNavbar />

      {/* SECCIÓN HERO SUPERIOR */}
      <section className="relative w-full min-h-[50vh] bg-[#0F172A] flex items-center justify-center overflow-hidden py-16 px-4 border-b border-slate-800/50">
        
        {/* EFECTO DEFENSOR 3D: Malla radial cinética simulada mediante CSS puro */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(13,148,136,0.08),transparent_50%),radial-gradient(circle_at_70%_70%,rgba(139,92,246,0.08),transparent_50%)] animate-pulse [animation-duration:8s]" />

        <div className="relative max-w-4xl mx-auto text-center flex flex-col items-center space-y-6 z-10">
          
          {/* TITULAR METÁLICO ANIMADO (SHIMMER EFFECT) */}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight font-display text-white leading-tight">
            <span className="inline-block bg-gradient-to-r from-white via-teal-200 via-purple-200 to-white bg-[length:200%_auto] bg-clip-text text-transparent animate-[shimmer_3s_linear_infinite] drop-shadow-[0_4px_12px_rgba(13,148,136,0.25)]">
              Haz tu pedido con anticipación.
            </span>
            <br />
            <span className="inline-block bg-gradient-to-r from-white via-cyan-200 via-purple-300 to-white bg-[length:200%_auto] bg-clip-text text-transparent animate-[shimmer_3s_linear_infinite] [animation-delay:0.5s] drop-shadow-[0_4px_12px_rgba(34,211,238,0.25)]">
              Tu señal puede fallar — tu pedido, no.
            </span>
          </h1>

          {/* SUBTEXTO REPARADO: Legibilidad perfecta y tipografía Nunito Sans */}
          <p className="max-w-2xl text-base md:text-lg text-slate-200/90 font-medium leading-relaxed font-sans tracking-wide p-1">
            Reserva con 2 a 3 días de antelación. Si pierdes la conexión a mitad del proceso, 
            nuestro sistema guarda todo lo que ingresaste de forma automática. 
            Asegura tus repuestos con total tranquilidad antes de iniciar tu viaje.
          </p>

          {/* BOTONERA INTERACTIVA PREMIUM */}
          <div className="flex flex-col sm:flex-row items-center gap-4 pt-4 w-full sm:w-auto">
            <Link className="w-full sm:w-auto inline-flex items-center justify-center bg-[#0D9488] hover:bg-[#0b7a70] text-white font-bold px-8 py-3.5 rounded-xl shadow-[0_4px_20px_rgba(13,148,136,0.3)] hover:shadow-[0_4px_25px_rgba(13,148,136,0.5)] transition-all duration-300 hover:-translate-y-0.5 text-sm" href="/login?from=/rural">
              Ingresar a mi cuenta
            </Link>
            <Link className="w-full sm:w-auto inline-flex items-center justify-center bg-slate-900/40 hover:bg-[#8B5CF6]/10 border border-slate-700/80 hover:border-[#8B5CF6]/50 text-slate-300 hover:text-[#8B5CF6] font-bold px-8 py-3.5 rounded-xl transition-all duration-300 hover:-translate-y-0.5 text-sm" href="/rural/registro">
              Crear cuenta
            </Link>
          </div>

        </div>
      </section>

      {/* SECCIÓN B: UTILIDADES ESTRATÉGICAS PARA TRABAJO EN CAMPO */}
      <section className="w-full py-16 bg-[#0c1222]/20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Tarjeta 1 */}
            <div className="bg-slate-800/40 border border-slate-700/50 p-6 rounded-2xl flex flex-col space-y-3 text-white transition-all duration-300 hover:border-slate-650 hover:bg-slate-800/50">
              <div className="w-12 h-12 rounded-xl bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M18.84 12.2a2.24 2.24 0 0 0-2.63-2.63l-1.04.26a2.24 2.24 0 0 1-2.64-2.64l.26-1.04a2.24 2.24 0 0 0-2.63-2.63l-1.04.26a2.24 2.24 0 0 1-2.64-2.64l.26-1.04a2.24 2.24 0 0 0-2.63-2.63" />
                  <path d="M2 20h20" />
                  <path d="M5 17h14" />
                  <path d="M9 14h6" />
                  <path d="M12 11v3" />
                </svg>
              </div>
              <h3 className="font-display font-bold text-lg text-white">Guardado Automático Offline</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Arma tu lista de repuestos incluso sin señal de internet en la ruta. Tus solicitudes se quedan protegidas en tu celular y se envían solas apenas recuperes cobertura.
              </p>
            </div>

            {/* Tarjeta 2 */}
            <div className="bg-slate-800/40 border border-slate-700/50 p-6 rounded-2xl flex flex-col space-y-3 text-white transition-all duration-300 hover:border-slate-650 hover:bg-slate-800/50">
              <div className="w-12 h-12 rounded-xl bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <line x1="9" y1="3" x2="9" y2="21" />
                  <line x1="15" y1="3" x2="15" y2="21" />
                  <line x1="3" y1="9" x2="21" y2="9" />
                  <line x1="3" y1="15" x2="21" y2="15" />
                </svg>
              </div>
              <h3 className="font-display font-bold text-lg text-white">Abastecimiento Rural Planificado</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Evita viajar al centro de la ciudad en vano. Congela el stock de tus piezas originales Bajaj o TVS y recoge tu pedido listo en mostrador apenas llegues a la tienda.
              </p>
            </div>

            {/* Tarjeta 3 */}
            <div className="bg-slate-800/40 border border-slate-700/50 p-6 rounded-2xl flex flex-col space-y-3 text-white transition-all duration-300 hover:border-slate-650 hover:bg-slate-800/50">
              <div className="w-12 h-12 rounded-xl bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </svg>
              </div>
              <h3 className="font-display font-bold text-lg text-white">Respaldo y Asistencia Técnica</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Nuestros mecatrónicos autorizados SENATI conocen las exigencias de las rutas más duras de la región. Recibe asesoría remota para mantener tu mototaxi en perfecto estado.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* SECCIÓN "CÓMO EMPEZAR" */}
      <section className="w-full py-16 border-t border-slate-850 bg-[#0c1222]/40">
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
                Crea tu cuenta de conductor rural indicando el modelo y año de tu mototaxi.
              </p>
            </div>

            {/* Paso 2 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-display font-bold text-lg shadow-[0_0_15px_rgba(13,148,136,0.4)]">
                2
              </div>
              <h3 className="font-display font-semibold text-base text-white">¡Explora Piezas con Fotos Reales!</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Navega por las categorías con imágenes de despiece real directamente sincronizadas.
              </p>
            </div>

            {/* Paso 3 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-display font-bold text-lg shadow-[0_0_15px_rgba(13,148,136,0.4)]">
                3
              </div>
              <h3 className="font-display font-semibold text-base text-white">¡Congela tu Stock y Gana Tiempo!</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Congela tu repuesto para recogerlo en mostrador o solicita un turno de mantenimiento preventivo.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* SECCIÓN DE PREVIEW DE REPUESTOS RURALES */}
      <section className="w-full py-16 bg-[#0c1222]/20 border-t border-slate-850">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-center text-2xl font-bold font-display text-white mb-10 tracking-tight">
            Repuestos rurales más solicitados
          </h2>
          {cargando ? (
            <div className="flex justify-center py-10">
              <span className="text-slate-400 font-body text-sm animate-pulse">Cargando catálogo rural...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto px-4 pb-12">
              {repuestos?.map(r => (
                <div
                  key={r.codigo}
                  className="group relative bg-slate-900/50 border border-slate-800/80 rounded-2xl p-5 flex flex-col space-y-4 overflow-hidden transition-all duration-500 ease-out [perspective:1000px] hover:[transform:rotateX(4deg)_rotateY(-4deg)_translateZ(10px)] hover:bg-slate-50 hover:shadow-[0_20px_40px_rgba(13,148,136,0.25)]"
                >
                  
                  {/* MARCO LED PERIMETRAL: Enciende en hover fusionando la paleta de la marca */}
                  <div className="absolute inset-0 rounded-2xl border border-transparent bg-gradient-to-r from-[#8B5CF6] via-cyan-400 to-[#0D9488] opacity-0 group-hover:opacity-100 transition-opacity duration-500 [mask:linear-gradient(#fff_0_0)_padding-box,linear-gradient(#fff_0_0)] [mask-composite:exclude] -inset-[1px] pointer-events-none" />

                  {/* Contenedor de Imagen de Repuesto (Cloudflare R2 Integrado) */}
                  <div className="aspect-square w-full bg-slate-950/90 rounded-xl relative overflow-hidden flex items-center justify-center p-6 border border-slate-800/60 transition-colors duration-500 group-hover:bg-slate-200/60 group-hover:border-slate-300">
                    <Image
                      src={r.imagen_principal_url || "/brand/placeholder-repuesto.png"}
                      alt="Repuesto Rural Garantizado"
                      width={190}
                      height={180}
                      priority
                      className="object-contain max-h-full max-w-full transform group-hover:scale-108 transition-transform duration-500 ease-out drop-shadow-[0_4px_12px_rgba(0,0,0,0.5)] group-hover:drop-shadow-[0_4px_8px_rgba(15,23,42,0.15)]"
                    />
                    
                    {/* Badge de Categoría con Contraste Adaptativo Nítido */}
                    <span className="absolute bottom-3 left-3 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-400/40 text-cyan-300 text-[10px] font-black tracking-widest uppercase px-2.5 py-1 rounded-md font-mono transition-all duration-500 group-hover:from-purple-600/10 group-hover:to-cyan-600/10 group-hover:border-purple-600/30 group-hover:text-purple-700 shadow-[0_2px_8px_rgba(34,211,238,0.2)] group-hover:shadow-none">
                      RURAL
                    </span>
                  </div>

                  {/* Bloque Informativo: Mutación Sincronizada a Cobalto Oscuro (#0F172A) */}
                  <div className="flex flex-col space-y-2 z-10">
                    <h4 className="text-white font-bold text-base tracking-tight font-display transition-colors duration-500 group-hover:text-[#0F172A]">
                      {r.nombre}
                    </h4>
                    <div className="flex flex-col space-y-0.5 text-[11px] font-mono font-medium text-slate-400 transition-colors duration-500 group-hover:text-[#0F172A]/80">
                      <span>CÓDIGO: <span className="text-slate-200 font-semibold transition-colors duration-500 group-hover:text-[#0F172A]">{r.codigo}</span></span>
                      <span>MODELO: <span className="text-slate-200 font-semibold transition-colors duration-500 group-hover:text-[#0F172A]">{r.modelo || 'Torito Universal'}</span></span>
                    </div>
                    
                    {/* Enlace Comercial de Conversión Protegido (Nivel 0 de Privacidad) */}
                    <Link
                      className="inline-flex items-center text-cyan-400 font-bold text-xs tracking-wide pt-2 transition-all duration-500 group-hover:text-[#0F172A] group-hover:translate-x-1"
                      href="/login?from=/rural"
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

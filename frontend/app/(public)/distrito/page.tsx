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

export default function LandingDistrito() {
  const [repuestos, setRepuestos] = useState<Repuesto[] | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    apiClient.get<{ repuestos: Repuesto[] }>('/v1/repuestos?universo=mototaxi_3r&destacado=true&limit=12')
      .then(data => {
        setRepuestos(data.repuestos)
        setCargando(false)
      })
      .catch(() => {
        // Fallback mayorista mockups for districts catalog preview
        setRepuestos([
          {
            id: '1',
            codigo: 'BAJ-4592',
            nombre: 'Kit de Arrancador Original Bajaj',
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
    <div className="flex flex-col min-h-screen bg-[#0F172A] text-slate-150 selection:bg-teal/30">
      <PublicNavbar />      {/* SECCIÓN HERO SUPERIOR */}
      <section className="relative w-full min-h-[50vh] bg-[#0F172A] flex items-center justify-center overflow-hidden py-16 px-4 border-b border-slate-800/50">
        
        {/* EFECTO DEFENSOR 3D: Malla de gradiente profunda en el fondo para dar volumen sin usar imágenes */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(139,92,246,0.08),transparent_50%),radial-gradient(circle_at_70%_70%,rgba(13,148,136,0.08),transparent_50%)] animate-pulse [animation-duration:8s]" />

        <div className="relative max-w-4xl mx-auto text-center flex flex-col items-center space-y-6 z-10">
          
          {/* TITULAR CON BRILLO ANIMADO TRIDIMENSIONAL (SHIMMER EFFECT) */}
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight font-display text-white leading-tight">
            <span className="inline-block bg-gradient-to-r from-white via-cyan-200 via-purple-300 to-white bg-[length:200%_auto] bg-clip-text text-transparent animate-[shimmer_3s_linear_infinite] drop-shadow-[0_4px_12px_rgba(34,211,238,0.15)]">
              Todo tu pedido de repuestos,
            </span>
            <br />
            <span className="inline-block bg-gradient-to-r from-white via-purple-200 via-cyan-300 to-white bg-[length:200%_auto] bg-clip-text text-transparent animate-[shimmer_3s_linear_infinite] [animation-delay:0.5s] drop-shadow-[0_4px_12px_rgba(139,92,246,0.15)]">
              de una sola vez.
            </span>
          </h1>

          {/* SUBTEXTO REPARADO: Legibilidad perfecta y tipografía Nunito Sans */}
          <p className="max-w-2xl text-base md:text-lg text-slate-200/90 font-medium leading-relaxed font-sans tracking-wide p-1">
            Abastece tu negocio o taller en provincias con la lista completa. 
            Olvídate de los viajes en vano por un solo repuesto: gestiona, 
            asegura tu stock y recibe en tu localidad con total garantía.
          </p>

          {/* BOTONERA INTERACTIVA PREMIUM */}
          <div className="flex flex-col sm:flex-row items-center gap-4 pt-4 w-full sm:w-auto">
            <Link className="w-full sm:w-auto inline-flex items-center justify-center bg-[#0D9488] hover:bg-[#0b7a70] text-white font-bold px-8 py-3.5 rounded-xl shadow-[0_4px_20px_rgba(13,148,136,0.3)] hover:shadow-[0_4px_25px_rgba(13,148,136,0.5)] transition-all duration-300 hover:-translate-y-0.5 text-sm" href="/login?from=/distrito">
              Ingresar a mi cuenta
            </Link>
            <Link className="w-full sm:w-auto inline-flex items-center justify-center bg-slate-900/40 hover:bg-[#8B5CF6]/10 border border-slate-700/80 hover:border-[#8B5CF6]/50 text-slate-300 hover:text-[#8B5CF6] font-bold px-8 py-3.5 rounded-xl transition-all duration-300 hover:-translate-y-0.5 text-sm" href="/distrito/registro">
              Crear cuenta
            </Link>
          </div>

        </div>
      </section>

      {/* SECCIÓN DE BENEFICIOS POR VOLUMEN */}
      <section className="w-full py-16 bg-[#0c1222]/20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Tarjeta 1 */}
            <div className="bg-slate-800/40 border border-slate-700/50 p-6 rounded-2xl flex flex-col space-y-3 text-white transition-all duration-300 hover:border-slate-650 hover:bg-slate-800/50">
              <div className="w-12 h-12 rounded-xl bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                  <polyline points="10 9 9 9 8 9" />
                </svg>
              </div>
              <h3 className="font-display font-bold text-lg text-white">Pedidos por Lista en un Solo Click</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Sube tu requerimiento masivo directamente desde el celular. Ahorra tiempo cargando toda tu lista y nuestro equipo en tienda preparará tu despacho el mismo día.
              </p>
            </div>

            {/* Tarjeta 2 */}
            <div className="bg-slate-800/40 border border-slate-700/50 p-6 rounded-2xl flex flex-col space-y-3 text-white transition-all duration-300 hover:border-slate-650 hover:bg-slate-800/50">
              <div className="w-12 h-12 rounded-xl bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="12" y1="1" x2="12" y2="23" />
                  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
              </div>
              <h3 className="font-display font-bold text-lg text-white">Precios Mayoristas Asegurados</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Accede a las tarifas de distribuidor autorizado Bajaj y TVS. Congela el stock al por mayor y mantén tu taller de campo siempre abastecido.
              </p>
            </div>

            {/* Tarjeta 3 */}
            <div className="bg-slate-800/40 border border-slate-700/50 p-6 rounded-2xl flex flex-col space-y-3 text-white transition-all duration-300 hover:border-slate-650 hover:bg-slate-800/50">
              <div className="w-12 h-12 rounded-xl bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <rect x="1" y="3" width="15" height="13" />
                  <polygon points="16 8 20 8 23 11 23 16 16 16 16 8" />
                  <circle cx="5.5" cy="18.5" r="2.5" />
                  <circle cx="18.5" cy="18.5" r="2.5" />
                </svg>
              </div>
              <h3 className="font-display font-bold text-lg text-white">Envíos Directos a Tu Distrito</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Coordinamos despachos diarios y seguros desde el Centro de Ayacucho hacia todas las provincias. Tu mercadería viaja protegida y con trazabilidad.
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
                Crea tu cuenta de socio o taller mayorista para que nuestro equipo pueda verificar tu perfil y habilitar tus tarifas especiales.
              </p>
            </div>

            {/* Paso 2 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-display font-bold text-lg shadow-[0_0_15px_rgba(13,148,136,0.4)]">
                2
              </div>
              <h3 className="font-display font-semibold text-base text-white">¡Explora Piezas con Fotos Reales!</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Revisa nuestro catálogo mayorista con despiece de precisión Bajaj y TVS directamente sincronizado de los almacenes.
              </p>
            </div>

            {/* Paso 3 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-[#0D9488] text-white flex items-center justify-center font-display font-bold text-lg shadow-[0_0_15px_rgba(13,148,136,0.4)]">
                3
              </div>
              <h3 className="font-display font-semibold text-base text-white">¡Congela tu Stock y Gana Tiempo!</h3>
              <p className="font-body text-sm text-slate-300 leading-relaxed">
                Envía tu lista, congela el precio de distribuidor y programa el retiro en tienda o el despacho express a tu distrito.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* SECCIÓN DE PREVIEW DE REPUESTOS AL POR MAYOR */}
      <section className="w-full py-16 bg-[#0c1222]/20 border-t border-slate-850">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-center text-2xl font-bold font-display text-white mb-10 tracking-tight">
            Repuestos al por mayor destacados
          </h2>
          {cargando ? (
            <div className="flex justify-center py-10">
              <span className="text-slate-400 font-body text-sm animate-pulse">Cargando catálogo mayorista...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto px-4 pb-12">
              {repuestos?.map(r => (
                <div
                  key={r.codigo}
                  className="group relative bg-slate-900/50 border border-slate-800/80 rounded-2xl p-5 flex flex-col space-y-4 overflow-hidden transition-all duration-500 ease-out [perspective:1000px] hover:[transform:rotateX(4deg)_rotateY(-4deg)_translateZ(10px)] hover:bg-slate-50 hover:shadow-[0_20px_40px_rgba(139,92,246,0.2)]"
                >
                  
                  {/* MARCO LED DE ALTA GAMA: Gradiente perimetral morado-celeste en Hover */}
                  <div className="absolute inset-0 rounded-2xl border border-transparent bg-gradient-to-r from-[#8B5CF6] via-cyan-400 to-[#0D9488] opacity-0 group-hover:opacity-100 transition-opacity duration-500 [mask:linear-gradient(#fff_0_0)_padding-box,linear-gradient(#fff_0_0)] [mask-composite:exclude] -inset-[1px] pointer-events-none" />

                  {/* Contenedor de Imagen (Cloudflare R2 Ready) */}
                  <div className="aspect-square w-full bg-slate-950/90 rounded-xl relative overflow-hidden flex items-center justify-center p-6 border border-slate-800/60 transition-colors duration-500 group-hover:bg-slate-200/60 group-hover:border-slate-300">
                    <Image
                      src={r.imagen_principal_url || "/brand/placeholder-repuesto.png"}
                      alt="Repuesto Mayorista"
                      width={190}
                      height={180}
                      priority
                      className="object-contain max-h-full max-w-full transform group-hover:scale-108 transition-transform duration-500 ease-out drop-shadow-[0_4px_12px_rgba(0,0,0,0.5)] group-hover:drop-shadow-[0_4px_8px_rgba(15,23,42,0.15)]"
                    />
                    
                    {/* Badge de Categoría con Contraste Nítido Adaptativo */}
                    <span className="absolute bottom-3 left-3 bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-400/40 text-cyan-300 text-[10px] font-black tracking-widest uppercase px-2.5 py-1 rounded-md font-mono transition-all duration-500 group-hover:from-purple-600/10 group-hover:to-cyan-600/10 group-hover:border-purple-600/30 group-hover:text-purple-700 shadow-[0_2px_8px_rgba(34,211,238,0.2)] group-hover:shadow-none">
                      MAYORISTA
                    </span>
                  </div>

                  {/* Base de Texto: Transmuta completamente a Cobalto Oscuro en Hover */}
                  <div className="flex flex-col space-y-2 z-10">
                    <h4 className="text-white font-bold text-base tracking-tight font-display transition-colors duration-500 group-hover:text-[#0F172A]">
                      {r.nombre}
                    </h4>
                    <div className="flex flex-col space-y-0.5 text-[11px] font-mono font-medium text-slate-400 transition-colors duration-500 group-hover:text-[#0F172A]/80">
                      <span>CÓDIGO: <span className="text-slate-200 font-semibold transition-colors duration-500 group-hover:text-[#0F172A]">{r.codigo}</span></span>
                      <span>MODELO: <span className="text-slate-200 font-semibold transition-colors duration-500 group-hover:text-[#0F172A]">{r.modelo || 'Universal Torito'}</span></span>
                    </div>
                    
                    {/* Enlace Comercial de Conversión Protegido (Nivel 0 de Privacidad) */}
                    <Link
                      className="inline-flex items-center text-cyan-400 font-bold text-xs tracking-wide pt-2 transition-all duration-500 group-hover:text-[#0F172A] group-hover:translate-x-1"
                      href="/login?from=/distrito"
                    >
                      Ver precio mayorista e ingresar <span className="ml-1 text-sm font-light transition-transform duration-300 group-hover:translate-x-0.5">→</span>
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

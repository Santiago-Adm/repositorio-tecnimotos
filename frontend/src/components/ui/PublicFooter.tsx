'use client'

import Link from 'next/link'
import { LogoSanti } from '@/src/components/ui/LogoSanti'

/** Cuadrado decorativo con gradiente — mismo lenguaje visual que el isotipo, antepuesto a cada título de columna. */
function TituloColumna({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="flex items-center gap-2 text-slate-400 font-bold text-xs uppercase tracking-wider mb-4">
      <span className="w-2 h-2 rounded-[3px] bg-gradient-to-br from-teal to-electric shrink-0" aria-hidden="true" />
      {children}
    </h3>
  )
}

/** Link con punto que crece y brilla electric al hover (sesión 2026-07-05, rediseño de footer). */
function LinkFooter({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="group/link flex items-center gap-2 text-sm font-medium text-slate-300 hover:text-teal transition-colors">
      <span className="w-1 h-1 rounded-full bg-slate-600 group-hover/link:w-1.5 group-hover/link:h-1.5 group-hover/link:bg-electric group-hover/link:shadow-[0_0_6px_rgba(139,92,246,0.8)] transition-all duration-200 shrink-0" aria-hidden="true" />
      {children}
    </Link>
  )
}

export default function PublicFooter() {
  return (
    <footer className="relative bg-slate-950 pt-8 pb-8 px-4 lg:px-8">
      {/* Glows ambientales — contenedor propio con overflow-hidden: el <footer>
          NO puede tener overflow-hidden, porque rompería el margen negativo de
          la tarjeta flotante (deja de "colapsar" con el padre y la recorta —
          bug real encontrado en verificación, Sant lo reportó como el link
          "Ver catálogo completo" superpuesto sobre la tarjeta). */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
        <div className="absolute top-0 right-0 w-[420px] h-[420px] bg-electric/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-1/4 w-[500px] h-[500px] bg-teal/10 rounded-full blur-[140px]" />
      </div>

      <div className="relative">
        {/* Tarjeta flotante glassmorphism — el fondo se adapta al ancho real del
          navegador (antes tenía max-w-7xl aquí mismo, dejaba margen abierto en
          pantallas anchas, reportado por Sant); el contenido interno sí
          mantiene max-w-7xl para no estirarse demasiado en monitores ultra-anchos. */}
        <div className="relative -mt-4 mb-8 rounded-[24px] bg-slate-900/70 backdrop-blur-2xl backdrop-saturate-150 border border-slate-800/60 shadow-[0_24px_60px_-24px_rgba(0,0,0,0.6)] p-8 lg:p-10">
          <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
            <div>
              <TituloColumna>Segmentos</TituloColumna>
              <ul className="space-y-2.5">
                <li><LinkFooter href="/conductor">Conductor Individual</LinkFooter></li>
                <li><LinkFooter href="/distrito">Mecánico de Distrito</LinkFooter></li>
                <li><LinkFooter href="/rural">Operación Rural</LinkFooter></li>
              </ul>
            </div>

            <div>
              <TituloColumna>Plataforma</TituloColumna>
              <ul className="space-y-2.5">
                <li><LinkFooter href="/catalogo">Catálogo Digital</LinkFooter></li>
                <li><LinkFooter href="/catalogo">Separación de Repuestos</LinkFooter></li>
                <li><LinkFooter href="/login">Estado de Taller</LinkFooter></li>
              </ul>
            </div>

            <div>
              <TituloColumna>Soporte Técnico</TituloColumna>
              <ul className="space-y-2.5">
                <li><LinkFooter href="/soporte">Centro de Ayuda (FAQ)</LinkFooter></li>
                <li><LinkFooter href="/convenio">Convenio SENATI</LinkFooter></li>
                <li><LinkFooter href="/guias">Guías de Despiece Bajaj/TVS</LinkFooter></li>
              </ul>
            </div>

            <div>
              <TituloColumna>Legal y Garantías</TituloColumna>
              <ul className="space-y-2.5">
                <li><LinkFooter href="/privacidad">Política de Privacidad</LinkFooter></li>
                <li><LinkFooter href="/terminos">Términos del Servicio</LinkFooter></li>
                <li><LinkFooter href="/retencion">Políticas de Retención</LinkFooter></li>
              </ul>
            </div>

            <div>
              <span className="block text-2xl font-extrabold tracking-tight font-display bg-gradient-to-r from-teal to-electric bg-clip-text text-transparent mb-2">
                SANTI
              </span>
              <p className="text-slate-400 text-xs leading-relaxed font-body mb-1">
                Sistema de Asistencia y Núcleo Técnico Integral.
              </p>
              <p className="text-slate-500 text-xs leading-relaxed font-body">
                Distribuidor Autorizado Bajaj &amp; TVS en la región de Ayacucho.
              </p>
            </div>
          </div>
        </div>

        {/* Barra inferior flotante — panel independiente, ya no una franja repetida */}
        <div className="rounded-2xl bg-slate-900/60 backdrop-blur-md border border-slate-800/50 px-6 py-4">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 md:gap-0">

            <div className="flex flex-col items-center md:items-start space-y-2 order-2 md:order-1">
              <p className="text-xs text-slate-500 font-medium tracking-wide">
                Ecosistema Digital SANTI &copy; 2026. Todos los derechos reservados.
              </p>
              <div className="flex flex-wrap justify-center md:justify-start gap-2">
                <span className="bg-slate-800/40 text-slate-400 px-2.5 py-0.5 rounded-full border border-slate-800 text-[10px] font-semibold tracking-wide">
                  Distribuidor Autorizado
                </span>
                <span className="bg-electric/10 text-electric px-2.5 py-0.5 rounded-full border border-electric/20 text-[10px] font-semibold tracking-wide">
                  Convenio SENATI
                </span>
              </div>
            </div>

            <div className="flex flex-col items-center justify-center order-1 md:order-2 my-1 md:my-0 gap-1">
              <LogoSanti sizeClassName="w-10 h-10" />
              <p className="text-[9px] font-mono tracking-wide text-slate-500 text-center max-w-[220px] leading-tight">
                SANTI — Sistema de Asistencia y Núcleo Técnico Integral
              </p>
            </div>

            <div className="flex flex-col items-center md:items-end space-y-3 order-3">
              <div className="flex items-center space-x-4 text-slate-400">
                <Link className="hover:text-teal transition-colors p-1" href="https://facebook.com" target="_blank" aria-label="Facebook"><FacebookIcon className="w-4 h-4"/></Link>
                <Link className="hover:text-teal transition-colors p-1" href="https://tiktok.com" target="_blank" aria-label="TikTok"><TikTokIcon className="w-4 h-4"/></Link>
                <Link className="hover:text-teal transition-colors p-1" href="https://instagram.com" target="_blank" aria-label="Instagram"><InstagramIcon className="w-4 h-4"/></Link>
                <Link className="hover:text-teal transition-colors p-1" href="https://youtube.com" target="_blank" aria-label="YouTube"><YouTubeIcon className="w-4 h-4"/></Link>
              </div>
              <Link
                className="border border-slate-800 bg-slate-900/30 hover:bg-slate-800/50 text-slate-300 hover:text-white px-5 py-2 rounded-xl text-xs font-semibold font-mono tracking-wide shadow-[0_0_20px_rgba(13,148,136,0.15)] hover:shadow-[0_0_24px_rgba(13,148,136,0.3)] active:scale-95 transition-all duration-300"
                href="/admin/login"
              >
                Ingreso Personal
              </Link>
            </div>

          </div>
        </div>
      </div>
    </footer>
  )
}

function FacebookIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path fillRule="evenodd" d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z" clipRule="evenodd" />
    </svg>
  )
}

function TikTokIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.01 1.7 4.14 1.15 1.13 2.72 1.77 4.36 1.83v3.86c-1.78-.03-3.52-.61-4.99-1.68-.04 2.53-.02 5.06-.04 7.59-.06 1.94-.78 3.84-2.11 5.21-1.45 1.48-3.54 2.3-5.63 2.24-2.55-.07-4.96-1.5-6.19-3.73-1.25-2.22-1.29-4.98-.11-7.24 1.18-2.26 3.59-3.7 6.13-3.74.88-.01 1.76.13 2.59.43v3.91c-.84-.33-1.77-.38-2.64-.13-1.12.31-2.07 1.15-2.53 2.22-.47 1.09-.43 2.37.12 3.42.54 1.02 1.63 1.69 2.78 1.76 1.34.09 2.69-.74 3.19-1.98.24-.61.32-1.28.3-1.94-.01-3.21-.01-6.42-.01-9.63z"/>
    </svg>
  )
}

function InstagramIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path fillRule="evenodd" d="M12.315 2c2.43 0 2.784.01 3.74.054 2.1.096 3.148 1.156 3.242 3.242.044.956.054 1.31.054 3.74 0 2.43-.01 2.784-.054 3.74-.094 2.084-1.144 3.146-3.242 3.242-.956.044-1.31.054-3.74.054-2.43 0-2.784-.01-3.74-.054-2.09-.096-3.148-1.156-3.242-3.242-.044-.956-.054-1.31-.054-3.74 0-2.43.01-2.784.054-3.74.094-2.084 1.144-3.146 3.242-3.242.956-.044 1.31-.054 3.74-.054zM12 5.75A6.25 6.25 0 1018.25 12 6.25 6.25 0 0012 5.75zm0 10A3.75 3.75 0 1115.75 12 3.75 3.75 0 0112 15.75zm5.5-8a1.25 1.25 0 102.5 0 1.25 1.25 0 00-2.5 0z" clipRule="evenodd" />
    </svg>
  )
}

function YouTubeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path fillRule="evenodd" d="M23.498 6.163a3.003 3.003 0 00-2.11-2.11C19.518 3.545 12 3.545 12 3.545s-7.518 0-9.388.508a3.003 3.003 0 00-2.11 2.11C0 8.033 0 12 0 12s0 3.967.502 5.837a3.003 3.003 0 002.11 2.11c1.87.508 9.388.508 9.388.508s7.518 0 9.388-.508a3.003 3.003 0 002.11-2.11C24 15.967 24 12 24 12s0-3.967-.502-5.837zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" clipRule="evenodd" />
    </svg>
  )
}

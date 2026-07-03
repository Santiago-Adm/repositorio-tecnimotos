'use client'

import Link from 'next/link'
import Image from 'next/image'
import { LogoSanti } from '@/src/components/ui/LogoSanti'

export default function PublicFooter() {
  return (
    <footer className="bg-slate-900 text-slate-350 border-t border-slate-800/80 mt-20 pt-16 pb-8 px-4 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* BLOQUE SUPERIOR: GRILLA DE ENLACES */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Columna 1: Segmentos */}
          <div>
            <h3 className="text-slate-400 font-bold text-xs uppercase tracking-wider mb-4">
              Segmentos
            </h3>
            <ul className="space-y-2.5">
              <li>
                <Link href="/conductor" className="hover:text-teal text-sm font-medium transition-colors">
                  Conductor Individual
                </Link>
              </li>
              <li>
                <Link href="/distrito" className="hover:text-teal text-sm font-medium transition-colors">
                  Mecánico de Distrito
                </Link>
              </li>
              <li>
                <Link href="/rural" className="hover:text-teal text-sm font-medium transition-colors">
                  Operación Rural
                </Link>
              </li>
            </ul>
          </div>

          {/* Columna 2: Plataforma */}
          <div>
            <h3 className="text-slate-400 font-bold text-xs uppercase tracking-wider mb-4">
              Plataforma
            </h3>
            <ul className="space-y-2.5">
              <li>
                <Link href="/catalogo" className="hover:text-teal text-sm font-medium transition-colors">
                  Catálogo Digital
                </Link>
              </li>
              <li>
                <Link href="/catalogo" className="hover:text-teal text-sm font-medium transition-colors">
                  Separación de Repuestos
                </Link>
              </li>
              <li>
                <Link href="/login" className="hover:text-teal text-sm font-medium transition-colors">
                  Estado de Taller
                </Link>
              </li>
            </ul>
          </div>

          {/* Columna 3: Soporte Técnico */}
          <div>
            <h3 className="text-slate-400 font-bold text-xs uppercase tracking-wider mb-4">
              Soporte Técnico
            </h3>
            <ul className="space-y-2.5">
              <li>
                <Link href="/soporte" className="hover:text-teal text-sm font-medium transition-colors">
                  Centro de Ayuda (FAQ)
                </Link>
              </li>
              <li>
                <Link href="/convenio" className="hover:text-teal text-sm font-medium transition-colors">
                  Convenio SENATI
                </Link>
              </li>
              <li>
                <Link href="/guias" className="hover:text-teal text-sm font-medium transition-colors">
                  Guías de Despiece Bajaj/TVS
                </Link>
              </li>
            </ul>
          </div>

          {/* Columna 4: Legal y Garantías */}
          <div>
            <h3 className="text-slate-400 font-bold text-xs uppercase tracking-wider mb-4">
              Legal y Garantías
            </h3>
            <ul className="space-y-2.5">
              <li>
                <Link href="/privacidad" className="hover:text-teal text-sm font-medium transition-colors">
                  Política de Privacidad
                </Link>
              </li>
              <li>
                <Link href="/terminos" className="hover:text-teal text-sm font-medium transition-colors">
                  Términos del Servicio
                </Link>
              </li>
              <li>
                <Link href="/retencion" className="hover:text-teal text-sm font-medium transition-colors">
                  Políticas de Retención (R30)
                </Link>
              </li>
            </ul>
          </div>

          {/* Columna 5: Identidad de Marca */}
          <div>
            <span className="block text-2xl font-extrabold tracking-tight font-display bg-gradient-to-r from-teal to-purple-500 bg-clip-text text-transparent mb-2">
              SANTI
            </span>
            <p className="text-slate-400 text-xs leading-relaxed font-body">
              Distribuidor Autorizado Bajaj & TVS en la región de Ayacucho.
            </p>
          </div>
        </div>
      </div>

      {/* BLOQUE INFERIOR: ACCIONES Y DERECHOS DE AUTOR */}
      <hr className="border-slate-800 my-8" />
      
      <div className="w-full bg-slate-900 border-t border-slate-800/60 transition-all">
          <div className="max-w-7xl mx-auto py-4 md:py-3 flex flex-col md:flex-row items-center justify-between gap-4 md:gap-0">
            
            {/* BLOQUE ALINEADO A LA IZQUIERDA: LEGAL Y CREDENCIALES */}
            <div className="flex flex-col items-center md:items-start space-y-2 order-2 md:order-1">
              <p className="text-xs text-slate-500 font-medium tracking-wide">
                Ecosistema Digital SANTI &copy; 2026. Todos los derechos reservados.
              </p>
              <div className="flex flex-wrap justify-center md:justify-start gap-2">
                <span className="bg-slate-800/40 text-slate-400 px-2.5 py-0.5 rounded-full border border-slate-800 text-[10px] font-semibold tracking-wide">
                  Distribuidor Autorizado
                </span>
                <span className="bg-purple-500/10 text-purple-400 px-2.5 py-0.5 rounded-full border border-purple-500/20 text-[10px] font-semibold tracking-wide">
                  Convenio SENATI
                </span>
              </div>
            </div>

            {/* BLOQUE CENTRAL ABSOLUTO: ISOTIPO AGIGANTADO Y CENTRALIZADO */}
            <div className="flex flex-col items-center justify-center space-y-1 order-1 md:order-2 my-2 md:my-0">
              <LogoSanti sizeClassName="w-16 h-16 md:w-20 md:h-20" />
              <span className="text-[10px] font-bold font-mono tracking-widest text-slate-500 uppercase">
                SANTI
              </span>
            </div>

            {/* BLOQUE ALINEADO A LA DERECHA: HUBS SOCIALES Y ACCESO OPERATIVO */}
            <div className="flex flex-col items-center md:items-end space-y-3 order-3">
              {/* Iconos Sociales con Tono Canónico y Efecto Hover Teal */}
              <div className="flex items-center space-x-4 text-slate-400">
                <Link className="hover:text-teal transition-colors p-1" href="https://facebook.com" target="_blank" aria-label="Facebook"><FacebookIcon className="w-4 h-4"/></Link>
                <Link className="hover:text-teal transition-colors p-1" href="https://tiktok.com" target="_blank" aria-label="TikTok"><TikTokIcon className="w-4 h-4"/></Link>
                <Link className="hover:text-teal transition-colors p-1" href="https://instagram.com" target="_blank" aria-label="Instagram"><InstagramIcon className="w-4 h-4"/></Link>
                <Link className="hover:text-teal transition-colors p-1" href="https://youtube.com" target="_blank" aria-label="YouTube"><YouTubeIcon className="w-4 h-4"/></Link>
              </div>
              {/* Botón de Autenticación de Perfil Bajo Píldora */}
              <Link className="border border-slate-800 bg-slate-900/30 hover:bg-slate-800/50 text-slate-300 hover:text-white px-5 py-2 rounded-xl text-xs font-semibold font-mono tracking-wide transition-all duration-300" href="/admin/login">
                Ingreso Personal
              </Link>
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

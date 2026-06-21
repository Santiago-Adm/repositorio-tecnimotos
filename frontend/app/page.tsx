import React from "react";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-body transition-colors duration-300">
      {/* Premium Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/75 border-b border-slate-200/80 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-electric-500 flex items-center justify-center text-white font-display font-bold text-xl shadow-md shadow-teal-500/20">
            S
          </div>
          <div>
            <h1 className="font-display font-bold text-lg leading-tight tracking-tight text-slate-900">
              Tecnimotos Santi
            </h1>
            <p className="text-[10px] uppercase font-mono tracking-widest text-teal-600 font-semibold leading-none mt-0.5">
              Núcleo Técnico Integral
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Backend Conectado
          </span>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-12 flex flex-col gap-12">
        {/* Hero Section */}
        <section className="text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-8 py-4">
          <div className="flex-1 space-y-4">
            <div className="inline-block bg-teal-50 border border-teal-200/60 rounded-lg px-3 py-1 text-xs font-medium text-teal-800">
              Sistema de Asistencia SANTI • MVP Fase 1
            </div>
            <h2 className="text-4xl md:text-5xl font-display font-extrabold text-slate-950 tracking-tight leading-none">
              Gestión Inteligente de <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-600 to-electric-600">Taller y Repuestos</span>
            </h2>
            <p className="text-slate-600 max-w-2xl text-base leading-relaxed">
              Plataforma unificada para clientes y mecánicos de Tecnimotos Santi (Ayacucho, Perú). 
              Consulta stock en tiempo real, solicita reservas y gestiona órdenes de trabajo al instante.
            </p>
          </div>
        </section>

        {/* Dual-surface Portal Selection */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Public Portal (Light Interface) */}
          <div className="bg-white border border-slate-200 rounded-3xl p-8 flex flex-col justify-between shadow-xl shadow-slate-100 hover:shadow-2xl hover:shadow-slate-200/80 transition-all duration-300 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-teal-500/5 rounded-full -mr-8 -mt-8 group-hover:scale-125 transition-transform duration-500"></div>
            
            <div className="space-y-6 z-10">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-teal-50 border border-teal-100 text-teal-800">
                  Acceso Cliente / Público
                </span>
                <div className="w-10 h-10 rounded-full bg-teal-50 flex items-center justify-center text-teal-600 font-bold">
                  →
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="text-2xl font-display font-bold text-slate-900">
                  Portal Público y Catálogo
                </h3>
                <p className="text-slate-600 text-sm">
                  Optimizado para clientes conductores (S1), mecánicos de distrito (S2) y zonas rurales (S4) con conectividad reducida.
                </p>
              </div>

              {/* Action Buttons / Routes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-teal-300 hover:bg-teal-50/20 transition-all duration-200 cursor-pointer group/card">
                  <h4 className="font-display font-semibold text-slate-800 group-hover/card:text-teal-700 text-sm">
                    🔍 Búsqueda de Repuestos
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">Consultar disponibilidad y precios por modelo o año.</p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-teal-300 hover:bg-teal-50/20 transition-all duration-200 cursor-pointer group/card">
                  <h4 className="font-display font-semibold text-slate-800 group-hover/card:text-teal-700 text-sm">
                    📅 Reservas Express
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">Separa tu repuesto con TTL automático antes de viajar.</p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-teal-300 hover:bg-teal-50/20 transition-all duration-200 cursor-pointer group/card">
                  <h4 className="font-display font-semibold text-slate-800 group-hover/card:text-teal-700 text-sm">
                    📦 Pedidos por Lote
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">Lista de reserva progresiva y despacho a distritos.</p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-teal-300 hover:bg-teal-50/20 transition-all duration-200 cursor-pointer group/card">
                  <h4 className="font-display font-semibold text-slate-800 group-hover/card:text-teal-700 text-sm">
                    📄 Proformas Digitales
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">Generar cotizaciones descargables en formato PDF.</p>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-between">
              <div className="text-xs text-slate-500">
                Rol: <span className="font-mono bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px]">CLIENTE_*</span>
              </div>
              <button className="bg-teal-600 hover:bg-teal-700 text-white font-medium px-5 py-2.5 rounded-xl transition-all duration-200 shadow-md shadow-teal-500/10 text-sm">
                Ingresar al Catálogo
              </button>
            </div>
          </div>

          {/* Internal Portal (Dark Interface - Modo Taller) */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 flex flex-col justify-between shadow-xl shadow-slate-950/20 hover:shadow-2xl hover:shadow-slate-950/50 transition-all duration-300 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-electric-500/5 rounded-full -mr-8 -mt-8 group-hover:scale-125 transition-transform duration-500"></div>

            <div className="space-y-6 z-10">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-electric-950/50 border border-electric-900/60 text-electric-400">
                  Acceso Personal / Interno
                </span>
                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-electric-400 font-bold border border-slate-700">
                  ⚙️
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="text-2xl font-display font-bold text-white">
                  Consola Operativa SANTI
                </h3>
                <p className="text-slate-400 text-sm">
                  Espacio de trabajo interno en "Modo Taller" para mecánicos, administradores y vendedores. Diseñado para reducir fatiga visual.
                </p>
              </div>

              {/* Action Buttons / Routes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
                <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-800 hover:border-electric-500/50 hover:bg-electric-950/15 transition-all duration-200 cursor-pointer group/card">
                  <h4 className="font-display font-semibold text-slate-200 group-hover/card:text-electric-400 text-sm">
                    🛠️ Control de Taller (OT)
                  </h4>
                  <p className="text-xs text-slate-400 mt-1">Apertura, consumo de repuestos y cierre de órdenes.</p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-800 hover:border-electric-500/50 hover:bg-electric-950/15 transition-all duration-200 cursor-pointer group/card">
                  <h4 className="font-display font-semibold text-slate-200 group-hover/card:text-electric-400 text-sm">
                    📈 Gestión de Stock
                  </h4>
                  <p className="text-xs text-slate-400 mt-1">Control de movimientos, alertas y reabastecimiento.</p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-800 hover:border-electric-500/50 hover:bg-electric-950/15 transition-all duration-200 cursor-pointer group/card">
                  <h4 className="font-display font-semibold text-slate-200 group-hover/card:text-electric-400 text-sm">
                    🧾 Emisión de Comprobantes
                  </h4>
                  <p className="text-xs text-slate-400 mt-1">Validación tributaria de boletas/facturas y notas de crédito.</p>
                </div>

                <div className="p-4 rounded-2xl bg-slate-800/60 border border-slate-800 hover:border-electric-500/50 hover:bg-electric-950/15 transition-all duration-200 cursor-pointer group/card">
                  <h4 className="font-display font-semibold text-slate-200 group-hover/card:text-electric-400 text-sm">
                    👥 Control de Usuarios
                  </h4>
                  <p className="text-xs text-slate-400 mt-1">Configuración ABAC/RBAC, MFA y perfiles de mecánicos.</p>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-800/80 flex items-center justify-between">
              <div className="text-xs text-slate-400">
                Roles: <span className="font-mono bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded text-[10px]">ADMIN, MECANICO_*, VENDEDOR</span>
              </div>
              <button className="bg-gradient-to-r from-teal-600 to-electric-600 hover:from-teal-500 hover:to-electric-500 text-white font-medium px-5 py-2.5 rounded-xl transition-all duration-200 shadow-md shadow-electric-900/20 text-sm">
                Consola Taller
              </button>
            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white/50 px-6 py-6 text-center text-xs text-slate-500">
        <p>© 2026 Tecnimotos Santi. Todos los derechos reservados. Desarrollado bajo protocolo de conformidad de marca SANTI.</p>
      </footer>
    </div>
  );
}

import Link from 'next/link'

export const metadata = { title: 'Tecnimotos — Acceso por segmento' }

const segmentos = [
  {
    href: '/conductor',
    titulo: 'Conductores de mototaxi',
    descripcion: 'Reserva repuestos antes de viajar y trabaja siempre con tu mecánico de confianza.',
    etiqueta: 'CLIENTE_CONDUCTOR',
  },
  {
    href: '/distrito',
    titulo: 'Distribuidores y talleres',
    descripcion: 'Arma tu pedido completo de una sola vez. Sin ir y venir para cada repuesto.',
    etiqueta: 'CLIENTE_DISTRITO',
  },
  {
    href: '/rural',
    titulo: 'Zonas rurales',
    descripcion: 'Tu pedido no se pierde aunque la señal sea mala. Confirma antes de hacer el viaje.',
    etiqueta: 'CLIENTE_RURAL',
  },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-surface-light flex flex-col">
      <header className="px-6 py-5 flex items-center justify-between border-b border-slate-100">
        <img src="/brand/logo-positivo.svg" alt="Tecnimotos" className="h-8" />
        <Link
          href="/login"
          className="text-sm font-body font-semibold text-teal hover:underline"
        >
          Acceso personal interno →
        </Link>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="max-w-2xl w-full text-center mb-10">
          <h1 className="font-display text-3xl md:text-4xl font-bold text-slate-800 mb-3">
            ¿Quién eres?
          </h1>
          <p className="font-body text-slate-500 text-base">
            Selecciona tu segmento para entrar al portal que corresponde a tu tipo de cuenta.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-3xl w-full">
          {segmentos.map((s) => (
            <Link
              key={s.href}
              href={s.href}
              className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-6 hover:border-teal hover:shadow-md transition-all duration-150"
            >
              <span className="inline-block mb-3 px-2 py-0.5 rounded text-xs font-mono bg-slate-100 text-slate-500 self-start">
                {s.etiqueta}
              </span>
              <h2 className="font-display font-bold text-slate-800 text-lg mb-2 group-hover:text-teal transition-colors">
                {s.titulo}
              </h2>
              <p className="font-body text-sm text-slate-500 leading-relaxed flex-1">
                {s.descripcion}
              </p>
              <span className="mt-4 text-sm font-body font-semibold text-teal group-hover:underline">
                Ver mi portal →
              </span>
            </Link>
          ))}
        </div>

        <p className="mt-10 font-body text-xs text-slate-400">
          Personal interno:{' '}
          <Link href="/login" className="underline hover:text-slate-600">
            ingresar con usuario y contraseña
          </Link>
        </p>
      </main>

      <footer className="py-4 text-center">
        <Link href="/privacidad" className="text-xs text-slate-400 underline hover:text-slate-600 font-body">
          Política de privacidad
        </Link>
      </footer>
    </div>
  )
}

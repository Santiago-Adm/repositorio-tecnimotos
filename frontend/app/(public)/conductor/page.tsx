import Link from 'next/link'

export const metadata = { title: 'Tecnimotos — Para conductores de mototaxi' }

export default function LandingConductor() {
  return (
    <div className="flex flex-col min-h-screen bg-surface-light">
      {/* Cabecera con privacidad visible sin scroll (10 §2.1 elemento 4 — RNL-04) */}
      <header className="flex items-center justify-between px-6 py-4">
        {/* Requiere /brand/logo-positivo.svg — provisto por Sant (10 §3.5) */}
        <img src="/brand/logo-positivo.svg" alt="Tecnimotos" className="h-8" />
        <Link
          href="/privacidad"
          className="text-xs text-slate-500 underline hover:text-slate-700 font-body"
        >
          Política de privacidad
        </Link>
      </header>

      {/* Hero con gancho anclado a 10 §2.2 fila S1 */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12 text-center">
        <div className="max-w-lg">
          <h1 className="font-display text-3xl md:text-4xl font-bold text-slate-800 mb-4 leading-tight">
            Reserva antes de viajar.<br />
            Trabaja siempre con el mecánico que ya conoce tu mototaxi.
          </h1>
          <p className="font-body text-base text-slate-600 mb-8">
            Confirma stock en tiempo real y asegura tu repuesto con un día de anticipación.
            Sin viajes en vano.
          </p>

          {/* Imagen hero — requiere /brand/hero-s1-2d.jpg o hero-s1-3d.webp (10 §2.3) */}
          <div className="mx-auto mb-10 rounded-2xl overflow-hidden bg-slate-100 w-full max-w-sm aspect-video">
            {/* Requiere /brand/hero-s1-2d.jpg — provisto por Sant (10 §2.3) */}
            <img
              src="/brand/hero-s1-2d.jpg"
              alt="Conductor de mototaxi con repuesto en mano"
              className="object-cover w-full h-full"
            />
          </div>

          {/* CTA único hacia login (10 §2.1 elemento 2) */}
          <Link
            href="/login"
            className="inline-block px-8 py-3 rounded-xl bg-teal text-white font-body font-semibold text-base hover:bg-teal/90 transition-colors"
          >
            Ingresar a mi cuenta
          </Link>
        </div>
      </main>

      <footer className="py-4 text-center">
        <Link href="/privacidad" className="text-xs text-slate-400 underline hover:text-slate-600 font-body">
          Política de privacidad
        </Link>
      </footer>
    </div>
  )
}

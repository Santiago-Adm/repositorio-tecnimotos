import Link from 'next/link'

export const metadata = { title: 'Tecnimotos Santi — Cómo funciona nuestro servicio' }

export default function TerminosPage() {
  return (
    <div className="min-h-screen bg-surface-light px-6 py-12">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <Link href="/" className="text-sm text-teal font-body hover:underline">
            ← Volver
          </Link>
        </div>

        <h1 className="font-display text-2xl font-bold text-slate-800 mb-3">
          Cómo funciona nuestro servicio
        </h1>
        <p className="text-slate-500 font-body text-sm mb-10">
          Estas son las reglas simples que seguimos con todos nuestros clientes.
        </p>

        <div className="space-y-10">
          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-2">¿Qué es Tecnimotos Santi?</h2>
            <p className="font-body text-sm text-slate-600 leading-relaxed">
              Somos distribuidor autorizado de repuestos Bajaj y TVS en Ayacucho. Con esta plataforma puedes
              ver si tenemos el repuesto que necesitas, reservarlo, y seguir el avance de tu pedido o de tu
              vehículo en el taller.
            </p>
          </section>

          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-2">Tu cuenta</h2>
            <p className="font-body text-sm text-slate-600 leading-relaxed">
              Para reservar un repuesto o ver el estado de tu pedido, necesitas crear una cuenta con tus
              datos reales. Al registrarte, nos das tu autorización para usar tu información como lo explicamos
              en nuestra <Link href="/privacidad" className="text-teal hover:underline">página de privacidad</Link>.
            </p>
          </section>

          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-2">Precios y pagos</h2>
            <div className="font-body text-sm text-slate-600 leading-relaxed space-y-2">
              <p>
                Nuestros precios los revisa siempre una persona — nunca cambian solos ni de manera automática.
              </p>
              <p>
                Si dejas tu vehículo en el taller, necesitamos que pagues al menos el 80% del costo antes de
                que puedas retirarlo, salvo que hayamos acordado algo distinto contigo.
              </p>
            </div>
          </section>

          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-2">Boletas y facturas</h2>
            <ul className="font-body text-sm text-slate-600 leading-relaxed list-disc list-inside space-y-1">
              <li>Si tu compra pasa de S/ 20, te damos boleta.</li>
              <li>Si tu compra pasa de S/ 60 y tienes RUC, te damos factura.</li>
              <li>Si necesitas anular una boleta o factura ya emitida, lo hacemos con una nota de crédito — nunca la borramos.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-2">Reservas y pedidos</h2>
            <p className="font-body text-sm text-slate-600 leading-relaxed">
              Cuando reservas un repuesto, lo apartamos para ti por un tiempo — todavía no es una compra
              hecha. Puedes ver en qué va tu pedido desde tu cuenta en cualquier momento.
            </p>
          </section>

          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-2">Si cambiamos estas reglas</h2>
            <p className="font-body text-sm text-slate-600 leading-relaxed">
              Si alguna vez cambiamos algo importante aquí, lo vas a ver reflejado en esta misma página.
            </p>
          </section>

          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-2">¿Alguna pregunta?</h2>
            <p className="font-body text-sm text-slate-600 leading-relaxed">
              Escríbenos a{' '}
              <a href="mailto:gsant3279@gmail.com" className="text-teal hover:underline">gsant3279@gmail.com</a> y te ayudamos con gusto.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}

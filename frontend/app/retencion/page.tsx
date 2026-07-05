import Link from 'next/link'

export const metadata = { title: 'Tecnimotos Santi — Cuánto tiempo guardamos tu información' }

// Fuente: .doc3/07-criterios-seguridad-ejecutables.md §6.1 — los plazos son
// los ya definidos ahí, solo se redactan aquí en lenguaje simple para el cliente.
const RETENCION_DETALLE: { dato: string; plazo: string }[] = [
  { dato: 'Tu nombre y tu teléfono', plazo: '5 años desde tu última compra' },
  { dato: 'Tu DNI (si te dimos una boleta o factura)', plazo: '5 años, por obligación tributaria' },
  { dato: 'Tu RUC (si compraste con factura)', plazo: '7 años, por obligación con SUNAT' },
  { dato: 'El historial de tus pedidos', plazo: '5 años desde tu última compra' },
  { dato: 'El historial de tu vehículo en el taller', plazo: '5 años desde tu última visita' },
  { dato: 'La placa y tarjeta de propiedad de tu vehículo', plazo: '5 años desde tu última visita' },
  { dato: 'Si tienes una deuda pendiente con nosotros', plazo: 'Hasta que la pagues, más 2 años' },
  { dato: 'Registros internos del sistema (seguridad)', plazo: '5 años' },
  { dato: 'Datos técnicos de tu sesión al conectarte', plazo: '90 días desde que cierras sesión' },
]

export default function RetencionPage() {
  return (
    <div className="min-h-screen bg-surface-light px-6 py-12">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <Link href="/" className="text-sm text-teal font-body hover:underline">
            ← Volver
          </Link>
        </div>

        <h1 className="font-display text-2xl font-bold text-slate-800 mb-3">
          Cuánto tiempo guardamos tu información
        </h1>
        <p className="text-slate-500 font-body text-sm mb-10">
          Aquí te explicamos cuánto tiempo conservamos cada tipo de dato, y por qué. Esto complementa
          nuestra <Link href="/privacidad" className="text-teal hover:underline">página de privacidad</Link>.
        </p>

        <div className="space-y-10">
          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-3">Tiempo de conservación</h2>
            <div className="divide-y divide-slate-200">
              {RETENCION_DETALLE.map((r) => (
                <div key={r.dato} className="py-3">
                  <p className="font-body text-sm text-slate-800 font-semibold">{r.dato}</p>
                  <p className="font-body text-sm text-slate-500">{r.plazo}</p>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-2">¿Puedes pedir que borremos tus datos?</h2>
            <p className="font-body text-sm text-slate-600 leading-relaxed">
              Sí, casi siempre. La única excepción es cuando la ley nos obliga a conservar algo — por ejemplo,
              tu RUC si compraste con factura, una deuda mientras esté pendiente, o nuestros registros de
              seguridad. Todo lo demás lo podemos eliminar si nos lo pides.
            </p>
          </section>

          <section>
            <h2 className="font-display text-lg font-bold text-slate-800 mb-2">¿Cómo lo pides?</h2>
            <ol className="font-body text-sm text-slate-600 leading-relaxed list-decimal list-inside space-y-2">
              <li>Escríbenos a <a href="mailto:gsant3279@gmail.com" className="text-teal hover:underline">gsant3279@gmail.com</a> o pásate por la tienda.</li>
              <li>Anotamos tu pedido con la fecha.</li>
              <li>Quitamos tu nombre, teléfono, DNI, placa y correo de nuestros registros.</li>
              <li>Lo que quede de tus compras o trabajos en taller se conserva, pero ya sin tus datos — es lo único que la ley tributaria nos obliga a mantener.</li>
              <li>Tu cuenta queda desactivada, sin poder usarse más.</li>
            </ol>
            <p className="text-slate-500 font-body text-xs mt-2">Hacemos todo esto en un máximo de 72 horas desde que nos escribes.</p>
          </section>
        </div>
      </div>
    </div>
  )
}

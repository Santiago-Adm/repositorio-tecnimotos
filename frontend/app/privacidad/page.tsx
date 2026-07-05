import Link from 'next/link'

export const metadata = { title: 'Tecnimotos Santi — Tu privacidad' }

interface PoliticaPrivacidad {
  responsable: {
    nombre: string
    ruc: string
    direccion: string
    contacto_arco: string
    registro_anpdp: string
  }
  finalidad: string[]
  derechos_arco: {
    canal: string
    plazo_respuesta_dias: number
  }
  retencion_datos: Record<string, string>
  transferencias_terceros: { receptor: string; finalidad: string }[]
  consentimiento: {
    revocable: boolean
    canal_revocacion: string
  }
}

async function obtenerPolitica(): Promise<PoliticaPrivacidad | null> {
  try {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8010'
    const res = await fetch(`${API_BASE}/v1/privacidad`, { next: { revalidate: 3600 } })
    if (!res.ok) return null
    const body = await res.json()
    return (body?.data ?? body) as PoliticaPrivacidad
  } catch {
    return null
  }
}

const RETENCION_LABEL: Record<string, string> = {
  datos_transaccionales: 'Tus pedidos y comprobantes',
  datos_personales_cliente: 'Tus datos personales',
  registros_taller: 'El historial de tu vehículo en el taller',
}

export default async function PrivacidadPage() {
  const politica = await obtenerPolitica()

  return (
    <div className="min-h-screen bg-surface-light px-6 py-12">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <Link href="/" className="text-sm text-teal font-body hover:underline">
            ← Volver
          </Link>
        </div>

        <h1 className="font-display text-2xl font-bold text-slate-800 mb-3">
          Tu privacidad
        </h1>
        <p className="text-slate-500 font-body text-sm mb-10">
          Aquí te explicamos, en palabras simples, qué información tuya guardamos y para qué la usamos.
        </p>

        {!politica ? (
          <p className="text-slate-500 font-body text-sm">
            No pudimos cargar esta información en este momento. Escríbenos a{' '}
            <a href="mailto:gsant3279@gmail.com" className="text-teal hover:underline">gsant3279@gmail.com</a> y te respondemos directamente.
          </p>
        ) : (
          <div className="space-y-10">
            <section>
              <h2 className="font-display text-lg font-bold text-slate-800 mb-2">¿Quiénes somos?</h2>
              <div className="font-body text-sm text-slate-600 leading-relaxed space-y-1">
                <p><strong className="text-slate-800">{politica.responsable.nombre}</strong>, en {politica.responsable.direccion}.</p>
                <p>
                  Si tienes cualquier duda sobre tus datos, escríbenos a{' '}
                  <a href={`mailto:${politica.responsable.contacto_arco}`} className="text-teal hover:underline">{politica.responsable.contacto_arco}</a>.
                </p>
                <p className="text-slate-400 text-xs pt-1">
                  RUC: {politica.responsable.ruc} · Registro ante la autoridad de protección de datos (ANPDP): {politica.responsable.registro_anpdp}
                </p>
              </div>
            </section>

            <section>
              <h2 className="font-display text-lg font-bold text-slate-800 mb-2">¿Para qué usamos tu información?</h2>
              <ul className="font-body text-sm text-slate-600 leading-relaxed list-disc list-inside space-y-1">
                {politica.finalidad.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </section>

            <section>
              <h2 className="font-display text-lg font-bold text-slate-800 mb-2">Tus derechos sobre tu información</h2>
              <div className="font-body text-sm text-slate-600 leading-relaxed space-y-2">
                <p>En cualquier momento puedes pedirnos que:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>te mostremos qué información tenemos de ti,</li>
                  <li>corrijamos algo que esté mal,</li>
                  <li>o borremos tu información por completo.</li>
                </ul>
                <p>
                  Solo escríbenos a{' '}
                  <a href={`mailto:${politica.derechos_arco.canal}`} className="text-teal hover:underline">{politica.derechos_arco.canal}</a>{' '}
                  y te respondemos en máximo {politica.derechos_arco.plazo_respuesta_dias} días.
                </p>
                <p className="text-slate-500 text-xs">
                  Para saber exactamente cuánto tiempo guardamos cada dato, mira nuestra{' '}
                  <Link href="/retencion" className="text-teal hover:underline">página de conservación de datos</Link>.
                </p>
              </div>
            </section>

            <section>
              <h2 className="font-display text-lg font-bold text-slate-800 mb-2">¿Compartimos tu información?</h2>
              <div className="font-body text-sm text-slate-600 leading-relaxed space-y-1">
                <p>Solo la compartimos cuando es necesario, y nunca la vendemos:</p>
                <ul className="list-disc list-inside space-y-1">
                  {politica.transferencias_terceros.map((t, i) => (
                    <li key={i}>Con <strong className="text-slate-800">{t.receptor}</strong>, para {t.finalidad.toLowerCase()}.</li>
                  ))}
                </ul>
              </div>
            </section>

            <section>
              <h2 className="font-display text-lg font-bold text-slate-800 mb-2">Tu autorización</h2>
              <div className="font-body text-sm text-slate-600 leading-relaxed space-y-1">
                <p>
                  Antes de guardar tus datos, te pedimos tu autorización de forma clara — nunca marcada por
                  defecto, siempre es tu decisión.
                </p>
                {politica.consentimiento.revocable && (
                  <p>
                    Puedes retirar tu autorización cuando quieras, escribiendo a{' '}
                    <a href={`mailto:${politica.consentimiento.canal_revocacion}`} className="text-teal hover:underline">{politica.consentimiento.canal_revocacion}</a>.
                  </p>
                )}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}

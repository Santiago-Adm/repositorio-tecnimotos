import Link from 'next/link'

export const metadata = { title: 'Tecnimotos — Política de privacidad' }

export default async function PrivacidadPage() {
  let texto = ''
  try {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
    const res = await fetch(`${API_BASE}/v1/privacidad`, { next: { revalidate: 3600 } })
    if (res.ok) {
      const body = await res.json()
      texto = body?.data?.texto ?? ''
    }
  } catch {
    texto = ''
  }

  return (
    <div className="min-h-screen bg-surface-light px-6 py-12">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <Link href="/" className="text-sm text-teal font-body hover:underline">
            Volver
          </Link>
        </div>
        <h1 className="font-display text-2xl font-bold text-slate-800 mb-6">
          Política de privacidad
        </h1>
        {texto ? (
          <div className="prose prose-slate font-body text-sm text-slate-700 whitespace-pre-wrap">
            {texto}
          </div>
        ) : (
          <p className="text-slate-500 font-body text-sm">
            Política de privacidad de Tecnimotos Santi. Contacta al administrador para más información.
          </p>
        )}
      </div>
    </div>
  )
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      // Cloudflare R2 — bucket público de imágenes de repuesto (repuestos/{codigo}/... y galería,
      // ADR-010/ADR-012). Sin esto, next/image bloquea el host y cae siempre al fallback.
      { protocol: 'https', hostname: '**.r2.dev' },
      { protocol: 'https', hostname: '**.r2.cloudflarestorage.com' },
    ],
  },
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8010'
    return [
      {
        source: '/v1/:path*',
        destination: `${apiBase}/v1/:path*`,
      },
    ]
  },
  async redirects() {
    return [
      {
        source: '/admin/login',
        destination: '/login',
        permanent: true,
      },
    ]
  },
}

export default nextConfig

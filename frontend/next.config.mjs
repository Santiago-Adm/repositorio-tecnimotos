/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api-proxy/:path*",
        destination: "http://localhost:8010/:path*",
      },
    ];
  },
};

export default nextConfig;

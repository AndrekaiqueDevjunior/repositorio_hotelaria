/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  output: 'standalone',
  images: {
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
      },
      {
        protocol: 'http',
        hostname: 'backend',
      },
    ],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || ''
  },

  async rewrites() {
    // Detecta se está rodando no Docker
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`
      },
      {
        source: '/media/:path*',
        destination: `${backendUrl}/media/:path*`
      },
      {
        source: '/health',
        destination: `${backendUrl}/health`
      },
      {
        source: '/docs',
        destination: `${backendUrl}/docs`
      }
    ]
  }
}
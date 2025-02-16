/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    serverMinification: true
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 
      (process.env.NODE_ENV === 'development' ? 'http://localhost:8080' : 'https://backend-service-273148242685.us-central1.run.app')
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Connection",
            value: "keep-alive",
          },
          {
            key: "Keep-Alive",
            value: "timeout=600",
          },
        ],
      },
    ];
  },
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8080';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        minSize: 20000,
        maxSize: 244000,
        minChunks: 1,
        maxAsyncRequests: 30,
        maxInitialRequests: 30,
      };
    }
    return config;
  },
  // Cloud Run用の設定
  distDir: '.next',
  generateBuildId: async () => {
    return 'build'
  }
};

module.exports = nextConfig;

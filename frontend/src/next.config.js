/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    serverMinification: true,
    serverTimeout: 600000, // 10分
  },
  httpAgentOptions: {
    keepAlive: true,
    timeout: 600000, // 10分
    scheduling: 'fifo',
    maxSockets: 100,
    maxFreeSockets: 10,
    socketTimeout: 610000, // timeout + 10秒
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
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.BACKEND_URL}/api/:path*`,
      },
    ];
  },
  serverOptions: {
    maxHeaderSize: 65536, // 64KB
    keepAliveTimeout: 600000, // 10分
    headersTimeout: 610000, // keepAliveTimeout + 10秒
    maxRequestsPerSocket: 0, // 無制限
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
};

module.exports = nextConfig;

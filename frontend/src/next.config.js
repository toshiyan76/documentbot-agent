/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    serverMinification: true,
    serverTimeout: 300000, // 300秒
  },
  httpAgentOptions: {
    keepAlive: true,
    timeout: 300000, // 300秒
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
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://backend:8081/api/:path*",
        has: [
          {
            type: 'header',
            key: 'connection',
            value: '(.*?)',
          },
        ],
      },
    ];
  },
  serverOptions: {
    maxHeaderSize: 32768, // 32KB
    keepAliveTimeout: 300000, // 300秒
    headersTimeout: 305000, // keepAliveTimeout + 5000 ms
  },
};

module.exports = nextConfig;

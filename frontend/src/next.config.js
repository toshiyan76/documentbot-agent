/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  poweredByHeader: false,
  experimental: {
    serverMinification: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "http://127.0.0.1:8000/api/:path*"
            : "/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;

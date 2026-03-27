// next.config.ts
import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'; // Ojo: antes dijiste que el backend estaba en 8001
const API_VERSION = process.env.API_VERSION || 'v1';

const nextConfig: NextConfig = {
  env: {
    API_VERSION,
  },

  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "Cross-Origin-Opener-Policy",
            value: "same-origin-allow-popups", // ✅ Cambio clave para Google OAuth
          },
          {
            key: "Cross-Origin-Embedder-Policy",
            value: "unsafe-none", // O mantenlo en unsafe-none si tienes problemas con imágenes externas
          },
        ],
      },
    ];
  },

  reactCompiler: true,
};

export default nextConfig;
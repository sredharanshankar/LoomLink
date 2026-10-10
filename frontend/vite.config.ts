import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import basicSsl from "@vitejs/plugin-basic-ssl";
import { VitePWA } from "vite-plugin-pwa";
import path from "path";

const proxyTarget = process.env.VITE_PROXY_TARGET ?? "http://backend:8000";

export default defineConfig({
  plugins: [
    react(),
    basicSsl(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico", "icons/*.png"],
      workbox: {
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            // Never cache API responses
            urlPattern: /^https?:\/\/[^/]+\/api\//,
            handler: "NetworkOnly",
          },
        ],
      },
      manifest: {
        name: "LoomLink",
        short_name: "LoomLink",
        description: "Textile Mill Operations Platform",
        theme_color: "#1E3A8A",
        start_url: "/w",
        display: "standalone",
        icons: [
          { src: "icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icons/icon-512.png", sizes: "512x512", type: "image/png" },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
    https: true,
    proxy: {
      "/api": {
        target: proxyTarget,
        changeOrigin: true,
        ws: true,
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test-setup.ts",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});

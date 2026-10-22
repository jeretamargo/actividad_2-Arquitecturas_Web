// @ts-check
import { defineConfig } from "astro/config";
import node from "@astrojs/node";
import react from "@astrojs/react";

// https://astro.build/config
export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),
  integrations: [react()],
  trailingSlash: "always",
  vite: {
    server: {
      proxy: {
        "/api/": {
          target: process.env.BACKEND_URL ?? "http://127.0.0.1:8000",
          changeOrigin: false,
        },
      },
    },
  },
});

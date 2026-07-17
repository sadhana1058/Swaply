import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev we proxy /auth and /health to the FastAPI backend so the SPA and API
// share an origin — cookies "just work" and there's no CORS to configure.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});

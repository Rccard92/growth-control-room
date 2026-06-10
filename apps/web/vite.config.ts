import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const allowedHosts = [
  "web-production-77355.up.railway.app",
  ...(process.env.WEB_ALLOWED_HOSTS?.split(",").map((h) => h.trim()).filter(Boolean) ?? []),
];

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  preview: {
    host: "0.0.0.0",
    allowedHosts,
  },
});

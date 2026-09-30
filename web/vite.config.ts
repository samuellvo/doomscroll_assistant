import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";
import { VitePWA } from "vite-plugin-pwa";

// The app reads the vault's generated app.json. Serve it in dev and emit it into the build,
// so the deployed site always ships the vault as of the deploy commit.
const APP_JSON = resolve(import.meta.dirname, "../vault/app.json");

function vaultData(): Plugin {
  return {
    name: "vault-data",
    configureServer(server) {
      server.middlewares.use("/app.json", (_req, res) => {
        res.setHeader("Content-Type", "application/json");
        res.end(readFileSync(APP_JSON));
      });
    },
    generateBundle() {
      this.emitFile({ type: "asset", fileName: "app.json", source: readFileSync(APP_JSON) });
    },
  };
}

export default defineConfig({
  // Relative base so the same build works at samuellvo.github.io/doomscroll_assistant/.
  base: "./",
  plugins: [
    react(),
    vaultData(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["apple-touch-icon.png"],
      manifest: {
        name: "Doomscroll Vault",
        short_name: "Vault",
        description: "Insights and tools from saved reels, deduplicated and grouped.",
        display: "standalone",
        start_url: "./",
        scope: "./",
        background_color: "#101418",
        theme_color: "#101418",
        icons: [
          { src: "icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png" },
        ],
      },
      workbox: {
        // The app shell is precached; the vault data is fetched network-first so it's fresh
        // when online and still available offline.
        globPatterns: ["**/*.{js,css,html,png,svg}"],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.endsWith("/app.json"),
            handler: "NetworkFirst",
            options: { cacheName: "vault-data", networkTimeoutSeconds: 4 },
          },
        ],
      },
    }),
  ],
});

/**
 * ============================================================
 * ÁREA: Configuração do Vite (bundler + dev server)
 * ------------------------------------------------------------
 * Atualizações que levaram à criação deste arquivo:
 * 1. O frontend-web não tinha build configurado — criamos este
 *    arquivo junto com `tsconfig.json`, `tsconfig.app.json`,
 *    `tsconfig.node.json` e `vite-env.d.ts` para o
 *    `npm run build` (tsc + vite build) passar sem erros.
 * 2. Instalamos `vite`, `@vitejs/plugin-react` e os tipos
 *    `@types/react` / `@types/react-dom`.
 * 3. No PowerShell do Windows usamos `npm.cmd run build/dev`
 *    porque a política de execução bloqueia o `npm.ps1`.
 * ============================================================
 */
import { defineConfig } from "vite"; // helper com tipos p/ o config
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  // Plugin oficial React p/ Vite: compila JSX/TSX e habilita o
  // Fast Refresh no `npm run dev` (edição sem perder o estado da tela).
  plugins: [react()],

  // ÁREA: DEV SERVER ------------------------------------------------
  // Porta fixa (5173) p/ que o backend saiba qual origem permitir no CORS.
  server: {
    port: 5173,
    // Proxy dev: qualquer requisição `/api/...` feita pelo portal é
    // encaminhada ao backend FastAPI (uvicorn na porta 8000). Assim o
    // frontend nunca precisa hardcodar `http://localhost:8000` e não há
    // problema de CORS durante o desenvolvimento.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});

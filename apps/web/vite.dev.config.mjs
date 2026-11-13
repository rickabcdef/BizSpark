/**
 * vite.dev.config.mjs — 开发常驻模式（PM 2026-11-13）
 *
 * 与 B 的 vite.config.ts 分工：
 *   vite.config.ts     —— 正式构建（npm run build / build:cn / build:store），不改动
 *   vite.dev.config.mjs —— 只给老板试玩/联调用：Vite 热更新 + 把 IPC 转发给真 sidecar
 *
 * 关键点：
 *   - 注入物（__TAURI_INTERNALS__ / BIZSPARK_BUILD / BIZSPARK_PRICING / 引擎热重载）
 *     不在本文件里，由 bridge 的 GET /__dev/boot.js 动态提供 → 改 locale/价格不用重启 vite
 *   - /__ipc 与 /__dev 全部 proxy 到 bridge（真 Python 引擎）
 */
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const IPC = process.env.BIZSPARK_DEV_IPC || "http://127.0.0.1:5181";
const PORT = Number(process.env.BIZSPARK_DEV_PORT || 5180);

export default defineConfig({
  plugins: [
    vue(),
    {
      name: "bizspark-dev-boot",
      transformIndexHtml() {
        // 必须在 main.ts 之前执行：普通 script（非 module）在 head 里同步执行
        return [
          {
            tag: "script",
            attrs: { src: "/__dev/boot.js" },
            injectTo: "head-prepend",
          },
        ];
      },
    },
  ],
  base: "/",
  envPrefix: ["VITE_", "BIZSPARK_"],
  server: {
    host: "127.0.0.1",
    port: PORT,
    strictPort: true, // 端口被占就报错，绝不偷偷换端口（老板的网址要固定）
    proxy: {
      "/__ipc": { target: IPC, changeOrigin: true },
      "/__dev": { target: IPC, changeOrigin: true },
    },
  },
});

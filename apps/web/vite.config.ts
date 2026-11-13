import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

/**
 * vite.config.ts — B（负责人：B）
 * 构建期把 A 注入的 build-mode.txt / pricing.js 带进 public；
 * hash 路由（file:// 与 Tauri WebView 均可跑）。
 */
export default defineConfig({
  plugins: [vue()],
  base: "./",
  build: { target: "chrome110", outDir: "dist" },
});

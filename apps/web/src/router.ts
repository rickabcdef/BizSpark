/**
 * router.ts — B-04（负责人：B）
 * 主链路：Welcome → Quiz → Results → Detail → Export
 * 侧栏 5 项直达：Saved / Library / Settings（+ Start / Find ideas）
 * 验收：每条链路 ≤8 次点击。
 *
 * 【PM 2026-11-16】老板决定：不做激活功能，激活路由与侧栏入口移除
 * （Activate.vue 与 locales activate.* 保留在库，将来恢复只需加回路由一行）。
 * 直接访问旧激活地址会落到 catch-all 重定向回首页。
 */
import { createRouter, createWebHashHistory, type RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  { path: "/", name: "welcome", component: () => import("./views/Welcome.vue") },
  { path: "/quiz", name: "quiz", component: () => import("./views/Quiz.vue") },
  { path: "/results", name: "results", component: () => import("./views/Results.vue") },
  { path: "/detail/:id", name: "detail", component: () => import("./views/Detail.vue") },
  { path: "/detail", redirect: "/results" },
  { path: "/export", name: "export", component: () => import("./views/Export.vue") },
  { path: "/saved", name: "saved", component: () => import("./views/Saved.vue") },
  { path: "/library", name: "library", component: () => import("./views/Library.vue") },
  { path: "/settings", name: "settings", component: () => import("./views/Settings.vue") },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

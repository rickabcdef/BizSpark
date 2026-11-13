/**
 * router.ts — B-04（负责人：B）
 * 主链路：Welcome → Quiz → Results → Detail → Export
 * 侧栏 6 项直达：Saved / Library / Activate / Settings（+ Start / Find ideas）
 * 验收：每条链路 ≤8 次点击。
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
  { path: "/activate", name: "activate", component: () => import("./views/Activate.vue") },
  { path: "/settings", name: "settings", component: () => import("./views/Settings.vue") },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

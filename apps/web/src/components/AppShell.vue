<!-- AppShell.vue — B-02（负责人：B）
     246px 深色侧栏 + 70px topbar + content，逐值移植 style.css。
     9 页复用；nav 9 项，当前项高亮 .on；B-04 侧栏直达。 -->
<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { t } from "../i18n";
import { STORE_BUILD } from "../router";

const route = useRoute();
const items = [
  { to: "/", ico: "◈", key: "nav.start" },
  { to: "/quiz", ico: "◎", key: "nav.quiz" },
  { to: "/results", ico: "✦", key: "nav.results" },
  { to: "/detail", ico: "▤", key: "nav.detail" },
  { to: "/export", ico: "↓", key: "nav.export" },
  { to: "/saved", ico: "❑", key: "nav.saved" },
  { to: "/library", ico: "↻", key: "nav.library" },
  // D-07 修复（PM）：Store 构建编译期隐藏 Activate 入口
  ...(STORE_BUILD ? [] : [{ to: "/activate", ico: "⚿", key: "nav.activate" }]),
  { to: "/settings", ico: "⚙", key: "nav.settings" },
];
const crumbPage = computed(() => {
  const cur = items.find((i) => (i.to === "/detail" ? route.path.startsWith("/detail") : route.path === i.to));
  return cur ? t(cur.key) : "";
});
</script>

<template>
  <div class="shell">
    <aside class="side">
      <div class="brand"><div class="brand-mark">B</div><div>BizSpark<small>{{ t("brand.tag") }}</small></div></div>
      <nav class="nav">
        <div class="nav-label">Workspace</div>
        <router-link v-for="i in items" :key="i.to" class="nav-i" :to="i.to"
          :class="{ on: i.to === '/detail' ? route.path.startsWith('/detail') : route.path === i.to }">
          <span class="ico">{{ i.ico }}</span>{{ t(i.key) }}
        </router-link>
      </nav>
      <div class="side-foot">
        <div class="badge-line"><span class="dot"></span>{{ t("side.badge") }}</div>
        <div class="side-ver">v1.0.0 · {{ t("side.ver") }}</div>
      </div>
    </aside>
    <div class="main">
      <div class="topbar">
        <div class="crumb">BizSpark&nbsp;&nbsp;/&nbsp;&nbsp;<b>{{ crumbPage }}</b></div>
        <div class="top-right">
          <div class="chip"><span class="dot"></span>{{ t("side.chip") }}</div>
          <div class="avatar">BS</div>
        </div>
      </div>
      <div class="content"><slot /></div>
    </div>
  </div>
</template>


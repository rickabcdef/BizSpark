<!-- AppShell.vue — B-02（负责人：B）
     246px 深色侧栏 + 70px topbar + content，逐值移植 style.css。
     9 页复用；nav 9 项，当前项高亮 .on；B-04 侧栏直达。 -->
<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { t } from "../i18n";

const route = useRoute();
const items = [
  { to: "/", ico: "◈", key: "nav.start" },
  { to: "/quiz", ico: "◎", key: "nav.quiz" },
  { to: "/results", ico: "✦", key: "nav.results" },
  { to: "/detail", ico: "▤", key: "nav.detail" },
  { to: "/export", ico: "↓", key: "nav.export" },
  { to: "/saved", ico: "❑", key: "nav.saved" },
  { to: "/library", ico: "↻", key: "nav.library" },
  { to: "/activate", ico: "⚿", key: "nav.activate" },
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

<style scoped>
.shell{display:flex;min-height:100vh}
.side{width:246px;flex:0 0 246px;background:var(--deep);color:#fff;padding:30px 22px 22px;display:flex;flex-direction:column;position:relative;overflow:hidden}
.side::after{content:"";position:absolute;width:280px;height:280px;border-radius:50%;
  background:radial-gradient(circle,rgba(242,101,58,.22),transparent 70%);right:-150px;bottom:-110px;pointer-events:none}
.brand{display:flex;align-items:center;gap:11px;font-size:19px;font-weight:750;letter-spacing:-.4px}
.brand-mark{width:32px;height:32px;border-radius:10px;background:var(--accent);
  display:grid;place-items:center;font-size:17px;font-weight:800;color:#fff;box-shadow:0 6px 16px rgba(242,101,58,.35)}
.brand small{display:block;font-size:10px;font-weight:500;letter-spacing:1.4px;color:#8FA3B5;text-transform:uppercase;margin-top:2px}
.nav{margin-top:44px;display:flex;flex-direction:column;gap:4px}
.nav-label{font-size:10px;letter-spacing:1.6px;text-transform:uppercase;color:#71879B;margin:0 10px 12px}
.nav a{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:11px;font-size:13.5px;color:#A8BACB;transition:.18s}
.nav a .ico{width:18px;text-align:center;font-size:14px;opacity:.85}
.nav a:hover{background:rgba(255,255,255,.06);color:#fff}
.nav a.on{background:rgba(255,255,255,.11);color:#fff;font-weight:600}
.nav a.on .ico{color:var(--accent)}
.side-foot{margin-top:auto;position:relative;z-index:1;border-top:1px solid rgba(255,255,255,.1);padding-top:16px}
.badge-line{display:flex;align-items:center;gap:8px;font-size:11.5px;color:#8FA3B5}
.side-ver{font-size:10.5px;color:#5F778C;margin-top:7px;letter-spacing:.4px}
.main{flex:1;min-width:0;display:flex;flex-direction:column}
.topbar{height:70px;flex:0 0 70px;border-bottom:1px solid var(--line);background:rgba(255,255,255,.72);
  backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:space-between;padding:0 40px}
.crumb{font-size:12.5px;color:var(--ink-3);letter-spacing:.3px}
.crumb b{color:var(--ink);font-weight:600}
.top-right{display:flex;align-items:center;gap:14px}
.chip{font-size:11.5px;color:var(--ink-2);background:var(--surface);border:1px solid var(--line);
  padding:6px 11px;border-radius:999px;display:flex;align-items:center;gap:7px}
.chip .dot{width:6px;height:6px}
.avatar{width:32px;height:32px;border-radius:50%;background:var(--deep);color:#fff;display:grid;place-items:center;font-size:12px;font-weight:700}
.content{padding:40px 48px 56px;max-width:1180px;width:100%;margin:0 auto;flex:1}
</style>

<!-- AppShell.vue — B-02（负责人：B）
     246px 深色侧栏 + 70px topbar + content，逐值移植 style.css。
     9 页复用；nav 8 项（PM 2026-11-17 去掉「一页方案」项），当前项高亮 .on；B-04 侧栏直达。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { t } from "../i18n";
import { checkLibrary } from "../bridge/cmd";

const route = useRoute();
// 【PM 2026-11-16】F09：侧栏版本行跟随实际库版本（月度合并后自动变化）；check_library 失败静默保留回退值
const libVer = ref<string>("2026.11");
onMounted(async () => {
  const r = await checkLibrary();
  if (r && r.version) libVer.value = String(r.version);
});
const items = [
  { to: "/", ico: "◈", key: "nav.start" },
  { to: "/quiz", ico: "◎", key: "nav.quiz" },
  { to: "/results", ico: "✦", key: "nav.results" },
  // 【PM 2026-11-17】老板决定：侧栏「一页方案」菜单项去掉（点它只是空转到结果页，
  // 真正的方案页必须带点子 id）。Detail 页与 /detail/:id 路由、卡片入口全部保留，
  // 面包屑仍显示「一页方案」。恢复侧栏入口只需加回下面这行：
  // { to: "/detail", ico: "▤", key: "nav.detail" },
  { to: "/export", ico: "↓", key: "nav.export" },
  { to: "/saved", ico: "❑", key: "nav.saved" },
  { to: "/library", ico: "↻", key: "nav.library" },
  // 【PM 2026-11-16】激活功能下线：Activate 入口移除（恢复时加回此行）
  { to: "/settings", ico: "⚙", key: "nav.settings" },
];
const crumbPage = computed(() => {
  // 侧栏已无「一页方案」项，但 /detail/:id 仍在：面包屑单独兜一层，标题不空
  if (route.path.startsWith("/detail")) return t("nav.detail");
  const cur = items.find((i) => route.path === i.to);
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
          :class="{ on: route.path === i.to }">
          <span class="ico">{{ i.ico }}</span>{{ t(i.key) }}
        </router-link>
      </nav>
      <div class="side-foot">
        <div class="badge-line"><span class="dot"></span>{{ t("side.badge") }}</div>
        <div class="side-ver">v1.0.0 · {{ t("side.ver", { ver: libVer }) }}</div>
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


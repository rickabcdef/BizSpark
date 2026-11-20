<!-- AppShell.vue — 对齐最新版静态原型外壳
     手机：导航贴底深墨蓝横条；宽屏：导航转左侧竖向栏。
     四主菜单：首页 / 找点子 / 我的 / 设置；results·detail·export 归「找点子」，
     library 归「我的」。脚本逻辑（库版本检查、方案落点解析、路由监听）全部保留。 -->
<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { t } from "../i18n";
import { checkLibrary, diagnose, getState } from "../bridge/cmd";
import Icon from "./Icon.vue";

const route = useRoute();

// 库版本行跟随实际库版本；check_library 失败静默保留回退值
const libVer = ref<string>("2026.11");
onMounted(async () => {
  const r = await checkLibrary();
  if (r && r.version) libVer.value = String(r.version);
});

/** 「一页方案」菜单落点解析：第 1 名方案 → 现算 diagnose → 回落问卷。逻辑保留。 */
const detailTo = ref<string>("/quiz");
async function resolveDetail(): Promise<void> {
  try {
    const st = await getState();
    const cached = (st?.last_result as { ideas?: Array<{ id?: string }> } | null)?.ideas?.[0]?.id;
    if (cached) { detailTo.value = `/detail/${cached}`; return; }
    const la = (st?.last_answers as Record<string, unknown> | null) || {};
    if (!Object.keys(la).length) { detailTo.value = "/quiz"; return; }
    const r = await diagnose(la);
    const id = (r?.ideas?.[0] as { id?: string } | undefined)?.id;
    detailTo.value = id ? `/detail/${id}` : "/quiz";
  } catch { /* 静默：保留当前落点，不阻断其它入口 */ }
}
onMounted(resolveDetail);
watch(
  () => route.path,
  (p) => { if (p === "/results" || p === "/quiz") void resolveDetail(); },
);

type Tab = { to: string; ico: string; key: string; match: (p: string) => boolean };
const tabs: Tab[] = [
  { to: "/", ico: "home", key: "nav.start", match: (p) => p === "/" },
  { to: "/quiz", ico: "search", key: "nav.quiz", match: (p) => ["/quiz", "/results", "/detail"].includes(p) },
  { to: "/saved", ico: "bookmark", key: "nav.saved", match: (p) => ["/saved", "/library", "/export"].includes(p) },
  { to: "/settings", ico: "gear", key: "nav.settings", match: (p) => p === "/settings" },
];

defineProps<{ pageClass?: string }>();

const activeKey = computed(() => tabs.find((x) => x.match(route.path))?.key ?? "");
const crumbPage = computed(() => (route.path.startsWith("/detail") ? t("nav.detail") : t(activeKey.value)));
void crumbPage;
void detailTo;
</script>

<template>
  <div class="page" :class="pageClass">
    <main class="main">
      <slot />
    </main>
    <nav class="tabbar">
      <div class="side-brand">
        <span class="sb-badge">B</span>
        <span class="sb-name">BizSpark</span>
      </div>
      <router-link
        v-for="tab in tabs"
        :key="tab.key"
        class="tab"
        :class="{ active: activeKey === tab.key }"
        :to="tab.to"
      >
        <span class="ico"><Icon :name="tab.ico" :size="21" /></span>
        <span>{{ t(tab.key) }}</span>
      </router-link>
    </nav>
  </div>
</template>

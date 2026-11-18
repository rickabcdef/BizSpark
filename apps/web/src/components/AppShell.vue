<!-- AppShell.vue — B-02（负责人：B）
     246px 深色侧栏 + 70px topbar + content，逐值移植 style.css。
     9 页复用；nav 8 项，当前项高亮 .on；B-04 侧栏直达。
     【PM 2026-11-17】侧栏「一页方案」项恢复，且不再是假入口：
     点击直达「最近一次诊断排名第 1」的方案页（/detail/:id）；没有诊断缓存时
     按已存答案现算一次；连答案都没有（首次启动）回落到问卷首题。 -->
<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { t } from "../i18n";
import { checkLibrary, diagnose, getState } from "../bridge/cmd";
import Icon from "./Icon.vue";

const route = useRoute();
// 【PM 2026-11-16】F09：侧栏版本行跟随实际库版本（月度合并后自动变化）；check_library 失败静默保留回退值
const libVer = ref<string>("2026.11");
onMounted(async () => {
  const r = await checkLibrary();
  if (r && r.version) libVer.value = String(r.version);
});
const items = [
  { to: "/", ico: "home", key: "nav.start" },
  { to: "/quiz", ico: "search", key: "nav.quiz" },
  { to: "/results", ico: "cards", key: "nav.results" },
  // 【PM 2026-11-17】老板要求保留「一页方案」菜单项：落点由 detailTo 动态解析，不再空转
  { to: "/detail", ico: "▤", key: "nav.detail" },
  { to: "/export", ico: "download", key: "nav.export" },
  { to: "/saved", ico: "bookmark", key: "nav.saved" },
  { to: "/library", ico: "refresh", key: "nav.library" },
  // 【PM 2026-11-16】激活功能下线：Activate 入口移除（恢复时加回此行）
  { to: "/settings", ico: "gear", key: "nav.settings" },
];
/**
 * 「一页方案」菜单的落点：方案页必须带点子 id（3 个点子 3 份方案），
 * 侧栏自己给不出，所以按优先级解析——① 最近一次诊断的第 1 名（state.last_result）
 * ② 用已存答案现算一次 diagnose ③ 都没有就直接进问卷（先答题才有方案可看）。
 */
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
  } catch { /* 静默：保留当前落点，不阻断侧栏其它入口 */ }
}
onMounted(resolveDetail);
// 答案可能刚改过：回到结果页/问卷时重新对齐一次，避免点进去还是旧点子
watch(
  () => route.path,
  (p) => { if (p === "/results" || p === "/quiz") void resolveDetail(); },
);
const crumbPage = computed(() => {
  // /detail/:id 不匹配菜单项的精确路径，面包屑单独兜一层，标题不空
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
        <router-link v-for="i in items" :key="i.to" class="nav-i"
          :to="i.to === '/detail' ? detailTo : i.to"
          :class="{ on: i.to === '/detail' ? route.path.startsWith('/detail') : route.path === i.to }">
          <span class="ico"><Icon :name="i.ico" :size="17" /></span>{{ t(i.key) }}
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
        </div>
      </div>
      <div class="content"><slot /></div>
    </div>
  </div>
</template>

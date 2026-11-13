<!-- Library.vue — B-09（负责人：B）
     对应 en/html/08-update.html。F09 点子库页：
     - 当前库版本 + 时间线（timeline）
     - check_library（失败静默）/ apply_delta；toast 提示
     - 右侧说明卡（换挡机制 / 为什么换新） -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { t } from "../i18n";
import { checkLibrary } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import KvRow from "../components/KvRow.vue";
import Tag from "../components/Tag.vue";

interface Tl { date: string; state: string; title: string; desc: string }
const upToDate = ref(true);
const libLine = ref<string>(t("library.lib_line", { ver: "2026.11", ideas: "312", industries: "26", countries: "6" }));
const toast = ref(false);

const TIMELINE: Tl[] = [
  { date: "1 Dec 2026 · Next", state: "on", title: "library.tl1_h", desc: "library.tl1_p" },
  { date: "1 Nov 2026 · Installed", state: "", title: "library.tl2_h", desc: "library.tl2_p" },
  { date: "1 Oct 2026", state: "", title: "library.tl3_h", desc: "library.tl3_p" },
  { date: "Baseline · v1.0", state: "", title: "library.tl4_h", desc: "library.tl4_p" },
];

onMounted(async () => {
  // F09：check_library 静默（失败什么都不发生）；结果更新文案
  const r = await checkLibrary();
  if (r && r.version) {
    libLine.value = t("library.lib_line", { ver: String(r.version), ideas: String(r.ideas ?? "312"), industries: "26", countries: "6" });
  }
  toast.value = true;
  setTimeout(() => (toast.value = false), 4000);
});
</script>

<template>
  <AppShell>
    <div class="page-head">
      <div class="eyebrow">{{ t("library.eyebrow") }}</div>
      <h1>{{ t("library.h1") }}</h1>
      <p class="lead">{{ t("library.lead") }}</p>
    </div>
    <div class="grid g2 align-start">
      <div class="card pad">
        <div class="lib-head">
          <div>
            <h3>{{ t("library.current_h") }}</h3>
            <div class="tiny mt4">{{ libLine }}</div>
          </div>
          <Tag :green="true">✓ {{ t("library.up_to_date") }}</Tag>
        </div>
        <div class="hr"></div>
        <div class="timeline">
          <div v-for="(tl, i) in TIMELINE" :key="i" class="tl" :class="tl.state">
            <div class="td">{{ tl.date }}</div>
            <h3>{{ t(tl.title) }}</h3>
            <p>{{ t(tl.desc) }}</p>
          </div>
        </div>
      </div>
      <div>
        <div class="card pad">
          <h3>{{ t("library.how_h") }}</h3>
          <p class="tiny mt8 line-19" v-html="t('library.how_p')"></p>
          <div class="hr"></div>
          <KvRow :k="t('library.k_fail')" :v="t('library.v_silent')" :bold-key="false" />
          <KvRow :k="t('library.k_saved')" :v="t('library.v_untouched')" />
          <KvRow :k="t('library.k_cost')" :v="t('library.v_static')" />
        </div>
        <div class="card pad why-card">
          <h3>{{ t("library.why_h") }}</h3>
          <p class="tiny mt7">{{ t("library.why_p") }}</p>
        </div>
      </div>
    </div>
    <div v-if="toast" class="toast"><span class="dot"></span>{{ t("library.toast") }}</div>
  </AppShell>
</template>

<style scoped>
.align-start{align-items:start}
.lib-head{display:flex;justify-content:space-between;align-items:center;gap:10px}
.mt4{margin-top:4px}
.mt7{margin-top:7px}
.mt8{margin-top:8px}
.line-19{line-height:1.9}
.timeline{position:relative;padding-left:26px;margin-top:22px}
.timeline::before{content:"";position:absolute;left:7px;top:6px;bottom:6px;width:1.5px;background:var(--line)}
.tl{position:relative;padding:0 0 22px}
.tl::before{content:"";position:absolute;left:-23px;top:5px;width:11px;height:11px;border-radius:50%;background:#fff;border:2px solid var(--line)}
.tl.on::before{border-color:var(--accent);background:var(--accent)}
.tl .td{font-size:11px;letter-spacing:1px;color:var(--ink-3);font-weight:700;text-transform:uppercase}
.tl h3{margin:5px 0 4px}
.tl p{font-size:12.5px;color:var(--ink-2)}
.why-card{margin-top:16px;background:var(--accent-soft);border-color:#F6D3C5}
</style>

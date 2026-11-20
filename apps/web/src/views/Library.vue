<!-- Library.vue — 对齐最新版原型 07-library。
     脚本（checkLibrary 静默检查、libLine 版本行、toast 计时）全部保留。
     基线：当前库卡（状态徽章 + meta + 时间线）；换挡卡三条 swap-row；为什么换新卡；toast。 -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { t } from "../i18n";
import { checkLibrary } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import Icon from "../components/Icon.vue";

const upToDate = ref(true);
const libLine = ref<string>(t("library.lib_line", { ver: "2026.11", ideas: "312", industries: "26", countries: "6" }));
const toast = ref(false);

interface Tl { dateKey: string; cls: string; title: string; desc: string }
const TIMELINE: Tl[] = [
  { dateKey: "library.tl1_date", cls: "tl-green", title: "library.tl1_h", desc: "library.tl1_p" },
  { dateKey: "library.tl2_date", cls: "tl-blue", title: "library.tl2_h", desc: "library.tl2_p" },
  { dateKey: "library.tl3_date", cls: "tl-orange", title: "library.tl3_h", desc: "library.tl3_p" },
  { dateKey: "library.tl4_date", cls: "", title: "library.tl4_h", desc: "library.tl4_p" },
];

const SWAPS = [
  { ico: "refresh", k: "library.k_fail", v: "library.v_silent" },
  { ico: "wifi", k: "library.k_saved", v: "library.v_untouched" },
  { ico: "card", k: "library.k_cost", v: "library.v_static" },
];

onMounted(async () => {
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
    <div class="lib-head">
      <div class="eyebrow">{{ t("library.eyebrow") }}</div>
      <h1>{{ t("library.h1") }}</h1>
      <p class="lead">{{ t("library.lead") }}</p>
    </div>

    <div class="content" style="padding-top:0">
      <div class="card">
        <div class="lib-status">
          <h3>{{ t("library.current_h") }}</h3>
          <span class="badge-green">
            <span style="width:7px;height:7px;border-radius:50%;background:var(--success);display:inline-block;"></span>
            {{ t("library.up_to_date") }}
          </span>
        </div>
        <div class="lib-meta">{{ libLine }}</div>
        <div class="timeline">
          <div v-for="(tl, i) in TIMELINE" :key="i" class="tl-item" :class="tl.cls">
            <span class="tl-dot"></span>
            <div class="tl-date">{{ t(tl.dateKey) }}</div>
            <div class="tl-title">{{ t(tl.title) }}</div>
            <div class="tl-desc">{{ t(tl.desc) }}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">{{ t("library.how_h") }}</div>
        <div v-for="s in SWAPS" :key="s.k" class="swap-row">
          <span class="ico"><Icon :name="s.ico" :size="18" /></span>
          <span>{{ t(s.k) }}</span>
          <span class="arrow">→</span>
          <strong>{{ t(s.v) }}</strong>
        </div>
      </div>

      <div class="card">
        <div class="card-title">{{ t("library.why_h") }}</div>
        <p style="color:var(--ink-2);font-size:15px">{{ t("library.why_p") }}</p>
      </div>

      <div v-if="toast" class="toast">
        <span class="check"><Icon name="check-circle" :size="18" /></span>{{ t("library.toast") }}
      </div>
    </div>
  </AppShell>
</template>

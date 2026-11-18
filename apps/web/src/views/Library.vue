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
import Icon from "../components/Icon.vue";

const upToDate = ref(true);
const libLine = ref<string>(t("library.lib_line", { ver: "2026.11", ideas: "312", industries: "26", countries: "6" }));
const toast = ref(false);

// 【POL-08】日期/状态文案进语言包（写死英文清出模板），条目数据结构不动
interface Tl { dateKey: string; state: string; title: string; desc: string }
const TIMELINE: Tl[] = [
  { dateKey: "library.tl1_date", state: "on", title: "library.tl1_h", desc: "library.tl1_p" },
  { dateKey: "library.tl2_date", state: "", title: "library.tl2_h", desc: "library.tl2_p" },
  { dateKey: "library.tl3_date", state: "", title: "library.tl3_h", desc: "library.tl3_p" },
  { dateKey: "library.tl4_date", state: "", title: "library.tl4_h", desc: "library.tl4_p" },
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
    <div class="grid g2 g2-start">
      <div class="card pad">
        <div class="row-between">
          <div>
            <h3>{{ t("library.current_h") }}</h3>
            <div class="tiny mt4">{{ libLine }}</div>
          </div>
          <Tag :green="true"><Icon name="check" :size="12" />{{ t("library.up_to_date") }}</Tag>
        </div>
        <div class="hr"></div>
        <div class="timeline">
          <div v-for="(tl, i) in TIMELINE" :key="i" class="tl" :class="tl.state">
            <div class="td">{{ t(tl.dateKey) }}</div>
            <h3>{{ t(tl.title) }}</h3>
            <p>{{ t(tl.desc) }}</p>
          </div>
        </div>
      </div>
      <div>
        <div class="card pad">
          <h3>{{ t("library.how_h") }}</h3>
          <p class="tiny how-p" v-html="t('library.how_p')"></p>
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


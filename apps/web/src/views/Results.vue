<!-- Results.vue — 对齐最新版原型 03-results。
     脚本（diagnose 重放、答案复述、saveAll 循环落库、空态降级、fx 货币）全部保留。
     基线：顶栏页名 + 显示器 chip；头部无眉题；三张 idea-card；改答案 / 全部保存堆叠；统计三卡。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { diagnose, getState, saveIdea } from "../bridge/cmd";
import { currencyOf, fmtAmount } from "../money";
import AppShell from "../components/AppShell.vue";
import Icon from "../components/Icon.vue";

interface Idea {
  id?: string; rank?: number; match_pct?: number; title?: string;
  summary?: string; why?: string; tags?: string[];
}
const router = useRouter();
const ideas = ref<Idea[]>([]);
const checked = ref<number | null>(null);
const filtered = ref<number | null>(null);
const saved = ref(false);
const answers = ref<Record<string, string | string[]>>({});
/** 复述句金额按所选国家货币展示（fx 来自 get_state.fx） */
const fxMap = ref<Record<string, number>>({});

const CAP_LABEL: Record<string, string> = {
  "<500": "results.ans_cap1", "500-2k": "results.ans_cap2", "2k-10k": "results.ans_cap3", "10k+": "results.ans_cap4",
};
const HOURS_LABEL: Record<string, string> = { "<10": "results.ans_h1", "10-25": "results.ans_h2", full: "results.ans_h3" };

const COUNTRY_KEY: Record<string, string> = {
  US: "results.country_us", CA: "results.country_ca", UK: "results.country_uk",
  AU: "results.country_au", SG: "results.country_sg", PH: "results.country_ph",
};

const CAP_TIER_USD: Record<string, [number, number | null]> = {
  "<500": [500, null], "500-2k": [500, 2000], "2k-10k": [2000, 10000], "10k+": [10000, null],
};

const recap = computed(() => {
  const a = answers.value;
  const cur = currencyOf(String(a.country || "US"));
  const tier = CAP_TIER_USD[String(a.capital)];
  const cap = CAP_LABEL[String(a.capital)]
    ? t(CAP_LABEL[String(a.capital)], tier
        ? { amt: fmtAmount(tier[0], cur, fxMap.value), lo: fmtAmount(tier[0], cur, fxMap.value),
            hi: tier[1] ? fmtAmount(tier[1], cur, fxMap.value) : "" }
        : undefined)
    : "";
  const hrs = HOURS_LABEL[String(a.hours)] ? t(HOURS_LABEL[String(a.hours)]) : "";
  const code = String(a.country || "US");
  const country = COUNTRY_KEY[code] ? t(COUNTRY_KEY[code]) : code;
  return t("results.recap", { capital: cap, hours: hrs, country });
});

/** 三张轮换插画（基线线稿） */
const ILLUS = [
  '<path d="M20 55 L80 30 L140 55"/><path d="M28 55 h104 v55 H28 z"/><path d="M28 55 q13 12 26 0 q13 12 26 0 q13 12 26 0 q13 12 26 0"/><rect x="62" y="78" width="36" height="32"/>',
  '<rect x="34" y="28" width="92" height="70" rx="3"/><path d="M46 44h68M46 58h68M46 72h44"/><path d="M104 96l18 18-18 0z"/>',
  '<rect x="40" y="24" width="80" height="86" rx="3"/><path d="M40 46h80M64 24v86M96 24v86"/><path d="M50 60h10M74 60h10M102 60h10"/>',
];

onMounted(async () => {
  try {
    const st = await getState();
    const la = (st && (st.last_answers as Record<string, string | string[]>)) || null;
    if (la && Object.keys(la).length) answers.value = la;
    fxMap.value = ((st && (st.fx as Record<string, number>)) || {});
  } catch { /* 状态读不到时保持空 answers */ }
  const r = await diagnose(answers.value);
  if (r) {
    ideas.value = (r.ideas as Idea[]) || [];
    checked.value = r.checked ?? null;
    filtered.value = r.filtered ?? null;
  }
});

async function saveAll(): Promise<void> {
  for (const i of ideas.value) if (i.id) void saveIdea(i.id);
  saved.value = true;
}
</script>

<template>
  <AppShell>
    <div class="topbar">
      <div class="side"><span style="width:8px;height:8px;border-radius:50%;background:var(--success);display:inline-block;"></span>{{ t("side.chip") }}</div>
    </div>

    <div class="result-head">
      <h1>{{ t("results.h1") }}</h1>
      <p class="lead">{{ recap }}</p>
    </div>

    <div class="content" style="padding-top:0">
      <template v-for="(i, ix) in ideas" :key="i.id || ix">
        <div class="idea-card">
          <div class="idea-illu" aria-hidden="true">
            <svg viewBox="0 0 160 130" fill="none" stroke="#56616E" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
              v-html="ILLUS[ix % 3]"></svg>
          </div>
          <div class="idea-body">
            <div class="idea-num">{{ String(ix + 1).padStart(2, "0") }} <small>/ {{ String(ideas.length).padStart(2, "0") }}</small></div>
            <div class="idea-title">{{ i.title || "" }}</div>
            <div class="idea-desc">{{ i.summary || "" }}</div>
            <div class="idea-tags">
              <span v-for="tag in i.tags" :key="tag" class="tag accent">{{ tag }}</span>
            </div>
            <router-link class="idea-btn" :to="`/detail/${i.id || ix}`">{{ t("results.cta") }}&nbsp;→</router-link>
          </div>
        </div>
      </template>

      <div v-if="ideas.length === 0" class="empty card">
        <Icon name="cards" :size="34" />
        <p>{{ t("results.empty") }}</p>
        <router-link class="btn btn-ghost mt18" to="/quiz">← {{ t("results.change") }}</router-link>
      </div>

      <template v-if="ideas.length">
        <div class="result-actions">
          <router-link class="btn btn-secondary" to="/quiz">← {{ t("results.change") }}</router-link>
          <button class="btn btn-primary" type="button" style="margin-top:12px" :disabled="saved" @click="saveAll">
            {{ saved ? t("results.saved_all") : t("results.save_all") }}</button>
        </div>
        <p class="result-note">{{ t("results.note") }}</p>
        <div class="stats">
          <div class="stat"><div class="stat-num">{{ checked ?? "—" }}</div><div class="stat-label">{{ t("results.stat_checked") }}</div></div>
          <div class="stat"><div class="stat-num">{{ filtered ?? "—" }}</div><div class="stat-label">{{ t("results.stat_filtered") }}</div></div>
          <div class="stat"><div class="stat-num">{{ ideas.length }}</div><div class="stat-label">{{ t("results.stat_kept") }}</div></div>
        </div>
      </template>
    </div>
  </AppShell>
</template>

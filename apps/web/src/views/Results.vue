<!-- Results.vue — B-07（负责人：B）
     对应 en/html/03-results.html。F04 结果页：
     - 3 卡 7 元素固定（色条/序号+匹配/标题/简介/why/标签/CTA）
     - 降级 1–2 卡自适应（diagnose 返回不足 3 条）
     - 答案复述句（lead 按 §2.4 answers 拼接）+ 统计行 checked/filtered/3
     - save_idea ×N（Save all three）；Change my answers → Quiz（Back 带预选）
     - 数据全部来自 diagnose；静默失败走空态（本页无 loading >1s） -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { diagnose, getState, saveIdea } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import IdeaCard from "../components/IdeaCard.vue";

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

const CAP_LABEL: Record<string, string> = {
  "<500": "results.ans_cap1", "500-2k": "results.ans_cap2", "2k-10k": "results.ans_cap3", "10k+": "results.ans_cap4",
};
const HOURS_LABEL: Record<string, string> = { "<10": "results.ans_h1", "10-25": "results.ans_h2", full: "results.ans_h3" };

// 国家码 → 英文全名（T-20 复述句要求国家全名展示；枚举与 engine/quiz.py COUNTRIES 一致）
const COUNTRY_NAME: Record<string, string> = {
  US: "United States", CA: "Canada", UK: "United Kingdom", AU: "Australia", SG: "Singapore", PH: "Philippines",
};

const recap = computed(() => {
  const a = answers.value;
  const cap = CAP_LABEL[String(a.capital)] ? t(CAP_LABEL[String(a.capital)]) : "";
  const hrs = HOURS_LABEL[String(a.hours)] ? t(HOURS_LABEL[String(a.hours)]) : "";
  const code = String(a.country || "US");
  const country = COUNTRY_NAME[code] || code;
  return t("results.recap", { capital: cap, hours: hrs, country });
});

onMounted(async () => {
  // D-01 修复（PM）：答案复述句数据源取 get_state.last_answers（Quiz 每题已 saveAnswers 落库），
  // 并用真实答案重放 diagnose——空 payload 会被引擎归一成默认值，导致复述句与推荐都不对
  try {
    const st = await getState();
    const la = (st && (st.last_answers as Record<string, string | string[]>)) || null;
    if (la && Object.keys(la).length) answers.value = la;
  } catch { /* 状态读不到时保持空 answers（recap 退化为默认国家句） */ }
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
    <div class="page-head">
      <div class="eyebrow">{{ t("results.eyebrow") }}</div>
      <h1>{{ t("results.h1") }}</h1>
      <p class="lead">{{ recap }}</p>
    </div>
    <div class="grid" :class="ideas.length === 3 ? 'g3' : ideas.length === 2 ? 'g2' : ''">
      <IdeaCard v-for="(i, ix) in ideas" :key="i.id || ix"
        :no="`${String(ix + 1).padStart(2, '0')} / ${String(ideas.length).padStart(2, '0')}`"
        :match="i.match_pct ? `${i.match_pct}% ${t('common.match')}` : undefined"
        :title="i.title || ''" :desc="i.summary || ''" :why="i.why || undefined" :tags="i.tags">
        <router-link class="btn btn-primary card-cta" :to="`/detail/${i.id || ix}`">{{ t("results.cta") }}&nbsp;→</router-link>
      </IdeaCard>
    </div>
    <div v-if="ideas.length === 0" class="empty card">
      <div class="ico">✦</div>
      <p>{{ t("results.empty") }}</p>
      <button class="btn btn-ghost" type="button" @click="router.push('/quiz')">{{ t("results.change") }}</button>
    </div>
    <template v-if="ideas.length">
      <div class="hr"></div>
      <div class="btn-row">
        <button class="btn btn-ghost" type="button" @click="router.push('/quiz')">← {{ t("results.change") }}</button>
        <button class="btn btn-quiet" type="button" @click="saveAll" :disabled="saved">
          {{ saved ? t("results.saved_all") : t("results.save_all") }}</button>
        <span class="tiny spacer">{{ t("results.note") }}</span>
      </div>
      <div class="stat">
        <div><div class="sv">{{ checked ?? "—" }}</div><div class="sl">{{ t("results.stat_checked") }}</div></div>
        <div><div class="sv">{{ filtered ?? "—" }}</div><div class="sl">{{ t("results.stat_filtered") }}</div></div>
        <div><div class="sv">{{ ideas.length }}</div><div class="sl">{{ t("results.stat_kept") }}</div></div>
      </div>
    </template>
  </AppShell>
</template>

<style scoped>
.card-cta{width:100%}
.spacer{margin-left:auto}
.stat{display:flex;gap:34px;margin-top:30px}
.stat .sv{font-size:24px;font-weight:750;letter-spacing:-.8px}
.stat .sl{font-size:11px;color:var(--ink-3);margin-top:2px}
.empty .btn{margin-top:18px}
/* 降级 1 卡时保持与稿一致的卡片宽度观感 */
.grid:not(.g3):not(.g2){grid-template-columns:1fr}
</style>

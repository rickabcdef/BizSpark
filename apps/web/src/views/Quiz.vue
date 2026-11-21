<!-- Quiz.vue — 对齐最新版原型 02-quiz。
     交互脚本（题目表、答案预选、多选清空、落库、Q5 直跳结果并并行 diagnose）全部保留不改。
     模板按基线：顶栏返回 + 页名 + 本机 chip；q-head 眉题 / 步骤点 / 标题 / 引导；
     题卡标题 + 选项 + 并排按钮；两条 notice。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { diagnose, getState, saveAnswers } from "../bridge/cmd";
import { currencyOf, fmtAmount } from "../money";
import AppShell from "../components/AppShell.vue";
import OptionCard from "../components/OptionCard.vue";
import Icon from "../components/Icon.vue";

const router = useRouter();

/* ---- 题目表（写死，不许加题/改序/自由文本） ---- */
interface Opt { value: string; icon?: string; iconName?: string; title: string; desc?: string }
interface Q { key: string; step: number; titleKey: string; hintKey: string; multi: boolean; titleIcon?: string; opts: Opt[] }
const QUIZ: Q[] = [
  { key: "country", step: 1, titleKey: "quiz.q1.title", hintKey: "quiz.q1.hint", multi: false, opts: [
    { value: "US", icon: "🇺🇸", title: "quiz.q1.o_us", desc: "USD" },
    { value: "CA", icon: "🇨🇦", title: "quiz.q1.o_ca", desc: "CAD" },
    { value: "UK", icon: "🇬🇧", title: "quiz.q1.o_uk", desc: "GBP" },
    { value: "AU", icon: "🇦🇺", title: "quiz.q1.o_au", desc: "AUD" },
    { value: "SG", icon: "🇸🇬", title: "quiz.q1.o_sg", desc: "SGD" },
    { value: "PH", icon: "🇵🇭", title: "quiz.q1.o_ph", desc: "PHP" },
  ] },
  { key: "capital", step: 2, titleKey: "quiz.q2.title", hintKey: "quiz.q2.hint", multi: false, titleIcon: "bag", opts: [
    { value: "<500", iconName: "wallet", title: "quiz.q2.o1", desc: "quiz.q2.o1d" },
    { value: "500-2k", iconName: "cash", title: "quiz.q2.o2", desc: "quiz.q2.o2d" },
    { value: "2k-10k", iconName: "card", title: "quiz.q2.o3", desc: "quiz.q2.o3d" },
    { value: "10k+", iconName: "bank", title: "quiz.q2.o4", desc: "quiz.q2.o4d" },
  ] },
  { key: "hours", step: 3, titleKey: "quiz.q3.title", hintKey: "quiz.q3.hint", multi: false, opts: [
    { value: "<10", iconName: "clock", title: "quiz.q3.o1", desc: "quiz.q3.o1d" },
    { value: "10-25", iconName: "clock2", title: "quiz.q3.o2", desc: "quiz.q3.o2d" },
    { value: "full", iconName: "sun", title: "quiz.q3.o3", desc: "quiz.q3.o3d" },
  ] },
  { key: "assets", step: 4, titleKey: "quiz.q4.title", hintKey: "quiz.q4.hint", multi: true, opts: [
    { value: "car", iconName: "car", title: "quiz.q4.o_car" },
    { value: "kitchen", iconName: "pot", title: "quiz.q4.o_kitchen" },
    { value: "laptop", iconName: "laptop", title: "quiz.q4.o_laptop" },
    { value: "design", iconName: "palette", title: "quiz.q4.o_design" },
    { value: "coding", iconName: "keyboard", title: "quiz.q4.o_coding" },
    { value: "spare_room", iconName: "door", title: "quiz.q4.o_spare" },
    { value: "local_network", iconName: "handshake", title: "quiz.q4.o_network" },
  ] },
  { key: "risk", step: 5, titleKey: "quiz.q5.title", hintKey: "quiz.q5.hint", multi: false, opts: [
    { value: "no_impact", iconName: "shield", title: "quiz.q5.o1", desc: "quiz.q5.o1d" },
    { value: "small_loss", iconName: "scale", title: "quiz.q5.o2", desc: "quiz.q5.o2d" },
    { value: "can_absorb", iconName: "flame", title: "quiz.q5.o3", desc: "quiz.q5.o3d" },
  ] },
];
const STEPS = ["quiz.s1", "quiz.s2", "quiz.s3", "quiz.s4", "quiz.s5"];

const idx = ref(0);
const answers = ref<Record<string, string | string[]>>({});
const q = computed(() => QUIZ[idx.value]);
const picked = computed(() => answers.value[q.value.key]);
/** 多选页：点过任意选项（含 Nothing yet）后才允许 Next */
const touched = ref(false);
/** 资金档金额按所选国家货币展示（fx 来自 get_state.fx） */
const fxMap = ref<Record<string, number>>({});

onMounted(async () => {
  const st = await getState();
  const last = (st && (st.last_answers as Record<string, string | string[]>)) || null;
  if (last) answers.value = { ...last };
  fxMap.value = ((st && (st.fx as Record<string, number>)) || {});
});

/** 资金档 USD 边界（与引擎 CAPITAL_TIERS 同口径） */
const CAP_TIER_USD: Record<string, [number, number | null]> = {
  "<500": [500, null], "500-2k": [500, 2000], "2k-10k": [2000, 10000], "10k+": [10000, null],
};

function optTitle(o: Opt): string {
  if (!o.title.startsWith("quiz.")) return o.title;
  const tier = CAP_TIER_USD[o.value];
  if (!tier) return t(o.title);
  const [lo, hi] = tier;
  const cur = currencyOf(String(answers.value.country || "US"));
  return t(o.title, { amt: fmtAmount(lo, cur, fxMap.value), lo: fmtAmount(lo, cur, fxMap.value),
                      hi: hi ? fmtAmount(hi, cur, fxMap.value) : "" });
}

function selOf(o: Opt): boolean {
  const p = picked.value;
  return Array.isArray(p) ? p.includes(o.value) : p === o.value;
}

function pick(o: Opt): void {
  const k = q.value.key;
  if (q.value.multi) {
    if (o.value === "nothing") {
      answers.value[k] = [];
    } else {
      const cur = Array.isArray(answers.value[k]) ? [...(answers.value[k] as string[])] : [];
      const i = cur.indexOf(o.value);
      if (i >= 0) cur.splice(i, 1);
      else cur.push(o.value);
      answers.value[k] = cur;
    }
    touched.value = true;
    void saveAnswers({ [k]: answers.value[k] });
  } else {
    answers.value[k] = o.value;
    void saveAnswers({ [k]: o.value });
  }
}

function advance(): void {
  touched.value = false;
  if (idx.value < QUIZ.length - 1) {
    idx.value += 1;
    return;
  }
  const all = { ...answers.value };
  void diagnose(all);
  router.push("/results");
}

function back(): void {
  touched.value = false;
  if (idx.value === 0) {
    router.push("/");
    return;
  }
  idx.value = Math.max(0, idx.value - 1);
}

const canNext = computed(() => {
  const p = picked.value;
  if (q.value.multi) return touched.value;
  return p !== undefined && p !== "";
});
const titleIcon = computed(() => q.value.titleIcon || q.value.opts[0]?.iconName || "pin");
</script>

<template>
  <AppShell>
    <div class="topbar">
      <button class="icon-btn" type="button" aria-label="返回" @click="back">
        <Icon name="chevron" :size="22" />
      </button>
      <div class="side">
        <span style="width:8px;height:8px;border-radius:50%;background:var(--success);display:inline-block;"></span>
        {{ t("side.chip") }}
      </div>
    </div>

    <div class="q-head">
      <div class="eyebrow">{{ t("quiz.eyebrow") }}</div>
      <div class="steps">
        <span v-for="(s, i) in STEPS" :key="s" class="step-dot"
          :class="{ done: i < idx, current: i === idx }">
          <Icon v-if="i <= idx" name="check" :size="13" />
        </span>
      </div>
      <h1>{{ t("quiz.h1") }}</h1>
      <p class="lead">{{ t("quiz.lead") }}</p>
    </div>

    <div class="content" style="padding-top:0">
      <div class="q-card">
        <div class="q-title">
          <span class="ico" style="color:var(--accent)"><Icon :name="titleIcon" :size="22" /></span>
          {{ t(q.titleKey) }}
        </div>
        <p class="q-sub">{{ t(q.hintKey) }}</p>
      </div>

      <template v-for="o in q.opts" :key="o.value">
        <OptionCard :icon="o.icon" :icon-name="o.iconName" :title="optTitle(o)"
          :desc="o.desc ? (o.desc.startsWith('quiz.') ? t(o.desc) : o.desc) : undefined"
          :selected="selOf(o)" :radio="!q.multi" @pick="pick(o)" />
      </template>
      <OptionCard v-if="q.multi" icon-name="box" :title="t('quiz.q4.nothing')"
        :selected="Array.isArray(picked) && picked.length === 0 && touched" :radio="false"
        @pick="pick({ value: 'nothing', title: '' })" />

      <div class="btn-row" style="margin-top:4px">
        <button class="btn btn-secondary" type="button" @click="back">← {{ t("common.back") }}</button>
        <button class="btn btn-primary" type="button" :disabled="!canNext" @click="advance">
          {{ idx === QUIZ.length - 1 ? t("quiz.finish") : t("quiz.next") }}&nbsp;→</button>
      </div>

      <div class="notice" style="margin-top:18px">
        <span class="ico"><Icon name="lock" :size="20" /></span>
        <div><strong style="color:var(--ink)">{{ t("quiz.note1_h") }}</strong><br>{{ t("quiz.note1_p") }}</div>
      </div>
      <div class="notice" style="margin-top:12px">
        <span class="ico"><Icon name="bulb" :size="20" /></span>
        <div><strong style="color:var(--ink)">{{ t("quiz.note2_h") }}</strong><br>{{ t("quiz.note2_p") }}</div>
      </div>
    </div>
  </AppShell>
</template>

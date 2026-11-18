<!-- Quiz.vue — B-03/B-06（负责人：B）
     对应 en/html/02-quiz.html。F02 问卷交互（§3.1 题目表，写死不改序）：
     - 基线是两个按钮：← Back 与 Next question（AL-B 卡第 6 条：不要自动跳题）
     - Q4 多选；Nothing yet 清空其余，选其他项自动取消它
     - Back 返回上一题不丢答案；从 Results 回来带上次答案预选
     - 每题选择后 save_answers 静默落库；未选时主推进置灰、不弹校验
     - Q5 完成不发请求不显示 loading，直接路由 Results 并并行 diagnose
     样式全部来自 assets/style.css。 -->
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

/* ---- 题目表（§3.1：写死，不许加题/改序/自由文本） ---- */
interface Opt { value: string; icon?: string; iconName?: string; title: string; desc?: string }
interface Q { key: string; step: number; titleKey: string; hintKey: string; multi: boolean; opts: Opt[] }
const QUIZ: Q[] = [
  { key: "country", step: 1, titleKey: "quiz.q1.title", hintKey: "quiz.q1.hint", multi: false, opts: [
    { value: "US", icon: "🇺🇸", title: "quiz.q1.o_us", desc: "USD" },
    { value: "CA", icon: "🇨🇦", title: "quiz.q1.o_ca", desc: "CAD" },
    { value: "UK", icon: "🇬🇧", title: "quiz.q1.o_uk", desc: "GBP" },
    { value: "AU", icon: "🇦🇺", title: "quiz.q1.o_au", desc: "AUD" },
    { value: "SG", icon: "🇸🇬", title: "quiz.q1.o_sg", desc: "SGD" },
    { value: "PH", icon: "🇵🇭", title: "quiz.q1.o_ph", desc: "PHP" },
  ] },
  { key: "capital", step: 2, titleKey: "quiz.q2.title", hintKey: "quiz.q2.hint", multi: false, opts: [
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
/** PM 2026-11-14：资金档金额按所选国家货币展示（fx 来自 get_state.fx） */
const fxMap = ref<Record<string, number>>({});

onMounted(async () => {
  // Back/Change answers 预选：读上次答案（损坏则默认重来，不弹窗）
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
      answers.value[k] = []; // Nothing yet 清掉其余
    } else {
      const cur = Array.isArray(answers.value[k]) ? [...(answers.value[k] as string[])] : [];
      const i = cur.indexOf(o.value);
      if (i >= 0) cur.splice(i, 1); // 再点别的选项自动取消它
      else cur.push(o.value);
      answers.value[k] = cur;
    }
    touched.value = true;
    void saveAnswers({ [k]: answers.value[k] });
  } else {
    answers.value[k] = o.value;
    void saveAnswers({ [k]: o.value }); // F：每题落库（静默）
  }
}

function advance(): void {
  touched.value = false;
  if (idx.value < QUIZ.length - 1) {
    idx.value += 1;
    return;
  }
  // Q5 完成：不发"计算中"请求、不显示 loading，直接路由并并行 diagnose
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
</script>

<template>
  <AppShell>
    <div class="page-head">
      <div class="eyebrow">{{ t("quiz.eyebrow") }}</div>
      <h1>{{ t("quiz.h1") }}</h1>
      <p class="lead">{{ t("quiz.lead") }}</p>
    </div>
    <div class="stepper">
      <template v-for="(s, i) in STEPS" :key="i">
        <div class="step" :class="{ done: i < idx, on: i === idx }">
          <span class="num"><template v-if="i < idx"><Icon name="check" :size="12" /></template><template v-else>{{ i + 1 }}</template></span>{{ t(s) }}
        </div>
        <div v-if="i < STEPS.length - 1" class="step-line" :class="{ done: i < idx }"></div>
      </template>
    </div>
    <div class="quiz-wrap">
      <div class="card q-card">
        <div class="q-count">{{ t("quiz.count", { n: String(idx + 1).padStart(2, "0"), name: t(STEPS[idx]) }) }}</div>
        <div class="q-title">{{ t(q.titleKey) }}</div>
        <div class="muted tiny">{{ t(q.hintKey) }}</div>
        <div class="opts">
          <template v-for="o in q.opts" :key="o.value">
            <OptionCard :icon="o.icon" :icon-name="o.iconName" :title="optTitle(o)"
              :desc="o.desc ? (o.desc.startsWith('quiz.') ? t(o.desc) : o.desc) : undefined"
              :selected="selOf(o)" :radio="!q.multi" @pick="pick(o)" />
          </template>
          <OptionCard v-if="q.multi" icon-name="box" :title="t('quiz.q4.nothing')"
            :selected="Array.isArray(picked) && picked.length === 0 && touched" :radio="false"
            @pick="pick({ value: 'nothing', title: '' })" />
        </div>
        <div class="hr"></div>
        <div class="btn-row">
          <button class="btn btn-ghost" type="button" @click="back">← {{ t("common.back") }}</button>
          <button class="btn btn-primary" type="button" :disabled="!canNext" @click="advance">
            {{ idx === QUIZ.length - 1 ? t("quiz.finish") : t("quiz.next") }}&nbsp;→</button>
          </div>
      </div>
      <div>
        <div class="card aside-note"><div class="ico"><Icon name="lock" :size="22" /></div><h3>{{ t("quiz.note1_h") }}</h3>
          <p>{{ t("quiz.note1_p") }}</p></div>
        <div class="card aside-note deep">
          <div class="ico"><Icon name="bulb" :size="22" /></div><h3>{{ t("quiz.note2_h") }}</h3>
          <p>{{ t("quiz.note2_p") }}</p></div>
      </div>
    </div>
  </AppShell>
</template>

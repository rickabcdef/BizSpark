<!-- Quiz.vue — B-03/B-06（负责人：B）
     对应 en/html/02-quiz.html。F02 问卷交互（§3.1 题目表，写死不改序）：
     - 选中 → 0.35s 自动进下一题；0.35s 内重复点击忽略（连点去重）
     - Q4 多选 + 唯一例外按钮 Done；Nothing yet 清空其余，选其他项自动取消它
     - Back 返回上一题不丢答案；从 Results 回来带上次答案预选
     - 每题选择后 save_answers 静默落库；未选时主推进置灰、不弹校验
     - Q5 完成不发请求不显示 loading，直接路由 Results 并并行 diagnose -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { diagnose, getState, saveAnswers } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import OptionCard from "../components/OptionCard.vue";

const router = useRouter();

/* ---- 题目表（§3.1：写死，不许加题/改序/自由文本） ---- */
interface Opt { value: string; icon: string; title: string; desc?: string }
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
    { value: "<500", icon: "🪙", title: "quiz.q2.o1", desc: "quiz.q2.o1d" },
    { value: "500-2k", icon: "💵", title: "quiz.q2.o2", desc: "quiz.q2.o2d" },
    { value: "2k-10k", icon: "💳", title: "quiz.q2.o3", desc: "quiz.q2.o3d" },
    { value: "10k+", icon: "🏦", title: "quiz.q2.o4", desc: "quiz.q2.o4d" },
  ] },
  { key: "hours", step: 3, titleKey: "quiz.q3.title", hintKey: "quiz.q3.hint", multi: false, opts: [
    { value: "<10", icon: "🌤", title: "quiz.q3.o1", desc: "quiz.q3.o1d" },
    { value: "10-25", icon: "🌥", title: "quiz.q3.o2", desc: "quiz.q3.o2d" },
    { value: "full", icon: "☀️", title: "quiz.q3.o3", desc: "quiz.q3.o3d" },
  ] },
  { key: "assets", step: 4, titleKey: "quiz.q4.title", hintKey: "quiz.q4.hint", multi: true, opts: [
    { value: "car", icon: "🚗", title: "quiz.q4.o_car" },
    { value: "kitchen", icon: "🍳", title: "quiz.q4.o_kitchen" },
    { value: "laptop", icon: "💻", title: "quiz.q4.o_laptop" },
    { value: "design", icon: "🎨", title: "quiz.q4.o_design" },
    { value: "coding", icon: "⌨️", title: "quiz.q4.o_coding" },
    { value: "spare_room", icon: "🚪", title: "quiz.q4.o_spare" },
    { value: "local_network", icon: "🤝", title: "quiz.q4.o_network" },
  ] },
  { key: "risk", step: 5, titleKey: "quiz.q5.title", hintKey: "quiz.q5.hint", multi: false, opts: [
    { value: "no_impact", icon: "🛡", title: "quiz.q5.o1", desc: "quiz.q5.o1d" },
    { value: "small_loss", icon: "⚖️", title: "quiz.q5.o2", desc: "quiz.q5.o2d" },
    { value: "can_absorb", icon: "🔥", title: "quiz.q5.o3", desc: "quiz.q5.o3d" },
  ] },
];
const STEPS = ["quiz.s1", "quiz.s2", "quiz.s3", "quiz.s4", "quiz.s5"];

const idx = ref(0);
const answers = ref<Record<string, string | string[]>>({});
const q = computed(() => QUIZ[idx.value]);
const picked = computed(() => answers.value[q.value.key]);

/* 连点去重：0.35s 自动进题窗口内忽略后续点击 */
const advancing = ref(false);
const doneShown = ref(false);

onMounted(async () => {
  // Back/Change answers 预选：读上次答案（损坏则默认重来，不弹窗）
  const st = await getState();
  const last = (st && (st.last_answers as Record<string, string | string[]>)) || null;
  if (last) answers.value = { ...last };
});

function selOf(o: Opt): boolean {
  const p = picked.value;
  return Array.isArray(p) ? p.includes(o.value) : p === o.value;
}

function pick(o: Opt): void {
  if (advancing.value) return; // 连点去重
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
    doneShown.value = true;
  } else {
    answers.value[k] = o.value;
    advancing.value = true;
    void saveAnswers({ [k]: o.value }); // F：每题落库（静默）
    setTimeout(() => advance(), 350);   // 0.35s 自动进下一题
  }
}

async function advance(): Promise<void> {
  advancing.value = false;
  doneShown.value = false;
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
  if (advancing.value) return;
  idx.value = Math.max(0, idx.value - 1);
}

const canNext = computed(() => {
  const p = picked.value;
  return q.value.multi ? true : p !== undefined && p !== "" && (!Array.isArray(p) || p.length > 0);
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
          <span class="num">{{ i < idx ? "✓" : i + 1 }}</span>{{ t(s) }}
        </div>
        <div v-if="i < STEPS.length - 1" class="step-line" :class="{ done: i < idx }"></div>
      </template>
    </div>
    <div class="quiz-wrap">
      <div class="card q-card">
        <div class="q-count">{{ t("quiz.count", { n: String(idx + 1).padStart(2, "0"), name: t(q.step === 1 ? "quiz.s1" : q.step === 2 ? "quiz.s2" : q.step === 3 ? "quiz.s3" : q.step === 4 ? "quiz.s4" : "quiz.s5") }) }}</div>
        <div class="q-title">{{ t(q.titleKey) }}</div>
        <div class="muted tiny">{{ t(q.hintKey) }}</div>
        <div class="opts">
          <template v-for="o in q.opts" :key="o.value">
            <OptionCard :icon="o.icon" :title="o.title.startsWith('quiz.') ? t(o.title) : o.title"
              :desc="o.desc ? (o.desc.startsWith('quiz.') ? t(o.desc) : o.desc) : undefined"
              :selected="selOf(o)" :radio="!q.multi" @pick="pick(o)" />
          </template>
          <OptionCard v-if="q.multi" icon="🕊" :title="t('quiz.q4.nothing')" :selected="(picked as string[])?.length === 0 && picked !== undefined" :radio="false" @pick="pick({ value: 'nothing', icon: '', title: '' })" />
        </div>
        <div class="hr"></div>
        <div class="btn-row">
          <button class="btn btn-ghost" type="button" @click="back">← {{ t("common.back") }}</button>
          <button v-if="q.multi && doneShown" class="btn btn-primary" type="button" @click="advance">{{ t("quiz.done") }}</button>
          <span class="tiny spacer">{{ t("quiz.time_note") }}</span>
        </div>
      </div>
      <div>
        <div class="card aside-note"><div class="ico">🔒</div><h3>{{ t("quiz.note1_h") }}</h3>
          <p>{{ t("quiz.note1_p") }}</p></div>
        <div class="card aside-note note2"><div class="ico">✦</div><h3>{{ t("quiz.note2_h") }}</h3>
          <p>{{ t("quiz.note2_p") }}</p></div>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.stepper{display:flex;align-items:center;gap:0;margin-bottom:34px}
.step{display:flex;align-items:center;gap:9px;font-size:12px;color:var(--ink-3)}
.step .num{width:25px;height:25px;border-radius:50%;border:1.5px solid var(--line);display:grid;place-items:center;font-size:11px;font-weight:700;background:#fff}
.step.done .num{background:var(--green);border-color:var(--green);color:#fff}
.step.on .num{background:var(--accent);border-color:var(--accent);color:#fff;box-shadow:0 0 0 5px var(--accent-soft)}
.step.on{color:var(--ink);font-weight:650}
.step-line{height:1.5px;width:44px;background:var(--line);margin:0 14px}
.step-line.done{background:var(--green)}
.quiz-wrap{display:grid;grid-template-columns:minmax(0,1fr) 268px;gap:24px;align-items:start}
.q-card{padding:34px 36px}
.q-count{font-size:11px;letter-spacing:1.6px;text-transform:uppercase;color:var(--ink-3);font-weight:700}
.q-title{font-size:26px;font-weight:730;letter-spacing:-.7px;margin:12px 0 6px}
.opts{display:grid;gap:10px;margin-top:26px}
.spacer{margin-left:auto}
.aside-note{padding:22px}
.aside-note .ico{font-size:22px}
.aside-note h3{margin:12px 0 7px}
.aside-note p{font-size:12.5px;color:var(--ink-2)}
.note2{margin-top:16px;background:var(--deep);border-color:var(--deep);color:#fff}
.note2 p{color:#A8BACB}
</style>

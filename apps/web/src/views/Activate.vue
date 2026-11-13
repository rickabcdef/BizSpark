<!-- Activate.vue — B-09（负责人：B）
     对应 en/html/07-activate.html。F10 激活页：
     - 4 段激活码（BZSP-K7Q2-M9XA-XXXX 格式）；G 的 activate / license_status / release_seat
     - 席位显示（3 台设备）；激活成功提示（notice 卡）
     - activate-eyebrow 价格槽（B-13） -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { activate, licenseStatus, releaseSeat } from "../bridge/cmd";
import { renderPriceSlots } from "../bridge/price";
import AppShell from "../components/AppShell.vue";

const router = useRouter();
const segs = ref<string[]>(["", "", "", ""]);
const seatsUsed = ref<number | null>(null);
const seatsMax = ref(3);
const activated = ref(false);
const busy = ref(false);

onMounted(async () => {
  renderPriceSlots();
  const s = await licenseStatus();
  if (s) {
    activated.value = s.activated === true;
    seatsUsed.value = typeof s.seats_used === "number" ? s.seats_used : null;
    if (typeof s.seats_max === "number") seatsMax.value = s.seats_max;
    if (activated.value) segs.value = ["••••", "••••", "••••", "••••"];
  }
});

async function doActivate(): Promise<void> {
  if (busy.value) return;
  const code = segs.value.map((s) => s.trim().toUpperCase()).filter(Boolean).join("-");
  if (!code) return; // 未输入不推进，不弹校验
  busy.value = true;
  const r = await activate(code); // 失败静默（G 端错误码不弹窗）
  busy.value = false;
  if (r && r.activated === true) {
    activated.value = true;
    if (typeof r.seats_used === "number") seatsUsed.value = r.seats_used;
    setTimeout(() => router.push("/"), 600);
  }
}

async function doRelease(): Promise<void> {
  await releaseSeat(); // 静默
  const s = await licenseStatus();
  if (s) seatsUsed.value = typeof s.seats_used === "number" ? s.seats_used : null;
}
</script>

<template>
  <AppShell>
    <div class="page-head">
      <div class="eyebrow">{{ t("activate.eyebrow") }}</div>
      <h1>{{ t("activate.h1") }}</h1>
      <p class="lead">{{ t("activate.lead") }}</p>
    </div>
    <div class="grid g2 align-start">
      <div class="card pad">
        <h3>{{ t("activate.code_h") }}</h3>
        <div class="tiny mt5">{{ t("activate.code_hint") }}</div>
        <div class="code-row">
          <input v-for="(s, i) in segs" :key="i" v-model="segs[i]" class="code-in"
            :class="{ f: activated || s }" maxlength="4" :aria-label="t('activate.seg_label', { n: i + 1 })"
            :disabled="activated" @keydown.enter="doActivate" />
        </div>
        <div class="tiny">{{ t("activate.seats_hint") }}</div>
        <div class="devs">
          <div v-for="n in seatsMax" :key="n" class="dev" :class="{ on: seatsUsed !== null && n <= seatsUsed }">
            {{ n <= 2 ? (n === 1 ? "💻" : "🖥") : "＋" }}</div>
          <span class="tiny ml6">{{ seatsUsed === null ? t("activate.seats_unknown") : t("activate.seats_used", { used: seatsUsed, max: seatsMax }) }}</span>
        </div>
        <div class="notice"><span>✓</span><span v-html="t('activate.notice')"></span></div>
        <div class="btn-row mt22">
          <button class="btn btn-primary" type="button" :disabled="busy || activated" @click="doActivate">
            {{ activated ? t("activate.done") : t("activate.cta") }}&nbsp;→</button>
          <button class="btn btn-quiet" type="button" @click="doRelease">{{ t("activate.release") }}</button>
        </div>
      </div>
      <div>
        <div class="card pad dark-card">
          <div class="eyebrow gold" data-price-slot="activate-eyebrow"></div>
          <h2 class="buy-h" v-html="t('activate.buy_h')"></h2>
          <div class="hr hr-dark"></div>
          <div class="buy-list">
            ✓ &nbsp;{{ t("activate.f1") }}<br>✓ &nbsp;{{ t("activate.f2") }}<br>✓ &nbsp;{{ t("activate.f3") }}<br>
            ✓ &nbsp;{{ t("activate.f4") }}<br>✓ &nbsp;{{ t("activate.f5") }}</div>
        </div>
        <div class="card pad mt16">
          <h3>{{ t("activate.why_h") }}</h3>
          <p class="tiny mt7">{{ t("activate.why_p") }}</p>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.align-start{align-items:start}
.mt5{margin-top:5px}
.mt16{margin-top:16px}
.mt22{margin-top:22px}
.ml6{margin-left:6px}
.mt7{margin-top:7px}
.code-row{display:flex;gap:9px;margin:20px 0 8px}
.code-in{flex:1;height:52px;border:1.5px solid var(--line);border-radius:12px;background:var(--surface-2);
  text-align:center;font-size:15px;letter-spacing:3px;font-weight:700;color:var(--ink);min-width:0}
.code-in.f{border-color:var(--accent);background:var(--accent-soft)}
.devs{display:flex;gap:10px;align-items:center;margin-top:18px}
.dev{width:38px;height:38px;border-radius:10px;border:1px solid var(--line);display:grid;place-items:center;font-size:15px;background:var(--surface-2)}
.dev.on{border-color:var(--green);background:var(--green-soft);color:var(--green)}
.notice{display:flex;gap:11px;align-items:flex-start;background:var(--green-soft);border-radius:12px;padding:13px 15px;font-size:12.5px;color:#1B6B58;margin-top:20px}
.dark-card{background:var(--deep);border-color:var(--deep);color:#fff}
.gold{color:var(--gold)}
.buy-h{font-size:24px;line-height:1.3}
.hr-dark{background:rgba(255,255,255,.12)}
.buy-list{font-size:13px;color:#C2D0DC;line-height:2.1}
</style>

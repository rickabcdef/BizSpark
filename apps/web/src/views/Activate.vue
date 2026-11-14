<!-- Activate.vue — B-09（负责人：B）
     对应 en/html/07-activate.html。F10 激活页：
     - 4 段激活码（BZSP-K7Q2-M9XA-XXXX 格式）；G 的 activate / license_status
     - 席位显示（3 台设备）；激活成功提示（notice 卡）
     - AL-G2：第一版「换电脑释放席位」走人工邮件，界面不摆按钮（本轮已移除）
     - activate-eyebrow 价格槽（B-13）
     样式全部来自 assets/style.css。 -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { activate, licenseStatus } from "../bridge/cmd";
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
</script>

<template>
  <AppShell>
    <div class="page-head">
      <div class="eyebrow">{{ t("activate.eyebrow") }}</div>
      <h1>{{ t("activate.h1") }}</h1>
      <p class="lead">{{ t("activate.lead") }}</p>
    </div>
    <div class="grid g2" style="align-items:start;grid-template-columns:repeat(2,minmax(0,1fr))">
      <div class="card pad">
        <h3>{{ t("activate.code_h") }}</h3>
        <div class="tiny" style="margin-top:5px">{{ t("activate.code_hint") }}</div>
        <div class="code-row">
          <!-- 样例码 BZSP-K7Q2-M9XA 是占位引导（基线原文），真输入后即被覆盖 -->
          <input v-for="(s, i) in segs" :key="i" v-model="segs[i]" class="code-in"
            :class="{ f: activated || s }" maxlength="4" :aria-label="t('activate.seg_label', { n: i + 1 })"
            :placeholder="['BZSP', 'K7Q2', 'M9XA', '••••'][i]"
            style="text-align:center;min-width:0"
            :disabled="activated" @keydown.enter="doActivate" />
        </div>
        <div class="tiny">{{ t("activate.seats_hint") }}</div>
        <div class="devs">
          <div v-for="n in seatsMax" :key="n" class="dev" :class="{ on: seatsUsed !== null && n <= seatsUsed }">
            {{ n <= 2 ? (n === 1 ? "💻" : "🖥") : "＋" }}</div>
          <span class="tiny" style="margin-left:6px">{{ seatsUsed === null ? t("activate.seats_unknown") : t("activate.seats_used", { used: seatsUsed, max: seatsMax }) }}</span>
        </div>
        <div class="notice"><span>✓</span><span v-html="t('activate.notice')"></span></div>
        <div class="btn-row" style="margin-top:22px">
          <button class="btn btn-primary" type="button" :disabled="busy || activated" @click="doActivate">
            {{ activated ? t("activate.done") : t("activate.cta") }}&nbsp;→</button>
        </div>
      </div>
      <div>
        <div class="card pad" style="background:var(--deep);border-color:var(--deep);color:#fff">
          <div class="eyebrow" style="color:var(--gold)" data-price-slot="activate-eyebrow"></div>
          <h2 style="font-size:24px;line-height:1.3" v-html="t('activate.buy_h')"></h2>
          <div class="hr" style="background:rgba(255,255,255,.12)"></div>
          <div style="font-size:13px;color:#C2D0DC;line-height:2.1">
            ✓ &nbsp;{{ t("activate.f1") }}<br>✓ &nbsp;{{ t("activate.f2") }}<br>✓ &nbsp;{{ t("activate.f3") }}<br>
            ✓ &nbsp;{{ t("activate.f4") }}<br>✓ &nbsp;{{ t("activate.f5") }}</div>
        </div>
        <div class="card pad" style="margin-top:16px">
          <h3>{{ t("activate.why_h") }}</h3>
          <p class="tiny" style="margin-top:7px">{{ t("activate.why_p") }}</p>
        </div>
      </div>
    </div>
  </AppShell>
</template>

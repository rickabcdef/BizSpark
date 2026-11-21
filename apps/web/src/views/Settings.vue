<!-- Settings.vue — 对齐最新版原型 08-settings。
     脚本（getSettings 读取、各设置变量、国家标签计算）全部保留；界面按基线裁剪为三卡。
     基线：顶栏右侧隐私标注；方案存哪卡；隐私卡（标题 / 短句 / 盾形脚注）；关于卡（版本 + 稳定版徽章同行）。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { t } from "../i18n";
import { getSettings } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import Icon from "../components/Icon.vue";

const country = ref("US");
const savePath = ref("Documents / BizSpark");
const libCheck = ref(true);
const followSystem = ref(true);
const crashNotes = ref(false);
const ver = ref("1.0.0");

const FLAG: Record<string, string> = { US: "🇺🇸", CA: "🇨🇦", UK: "🇬🇧", AU: "🇦🇺", SG: "🇸🇬", PH: "🇵🇭" };
const countryLabel = computed(() => {
  const code = String(country.value || "US");
  const name = t("quiz.q1.o_" + code.toLowerCase());
  return `${FLAG[code] || ""} ${name !== "quiz.q1.o_" + code.toLowerCase() ? name : code}`.trim();
});

onMounted(async () => {
  const s = await getSettings();
  if (s) {
    if (s.country) country.value = String(s.country);
    if (s.export_dir) savePath.value = String(s.export_dir);
    if (typeof s.library_check === "boolean") libCheck.value = s.library_check;
    if (typeof s.follow_system_appearance === "boolean") followSystem.value = s.follow_system_appearance;
    if (typeof s.crash_notes === "boolean") crashNotes.value = s.crash_notes;
  }
});
void countryLabel; void savePath; void libCheck; void followSystem; void crashNotes;
</script>

<template>
  <AppShell>
    <div class="topbar">
      <div class="side"><span style="width:8px;height:8px;border-radius:50%;background:var(--success);display:inline-block;"></span>{{ t("side.chip") }}</div>
    </div>

    <div class="set-head">
      <h1>{{ t("settings.h1") }}</h1>
      <p class="lead">{{ t("settings.lead") }}</p>
    </div>

    <div class="content" style="padding-top:0">
      <div class="card set-row">
        <span class="ico"><Icon name="folder" :size="22" /></span>
        <div><h3>{{ t("settings.path") }}</h3><p>{{ t("settings.path_desc") }}</p></div>
      </div>

      <div class="card">
        <div class="set-row">
          <span class="ico"><Icon name="shield-check" :size="22" /></span>
          <div><h3>{{ t("settings.privacy_eyebrow") }}</h3></div>
        </div>
        <div class="privacy-title">{{ t("settings.privacy_h") }}</div>
        <p class="privacy-desc">{{ t("settings.privacy_short") }}</p>
        <div class="privacy-foot">
          <Icon name="shield-check" :size="18" />{{ t("settings.privacy_foot") }}
        </div>
      </div>

      <div class="card">
        <h3 style="font-size:18px;font-weight:700;margin-bottom:14px">{{ t("settings.about_h") }}</h3>
        <div class="about-row">
          <span>{{ t("settings.about_ver") }}</span>
          <span class="about-val"><span class="val">{{ ver }}</span><span class="badge-stable">{{ t("settings.stable") }}</span></span>
        </div>
        <p class="about-desc">{{ t("settings.about_foot") }}</p>
      </div>
    </div>
  </AppShell>
</template>

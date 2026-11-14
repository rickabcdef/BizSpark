<!-- Settings.vue — B-09/B-10（负责人：B）
     对应 en/html/09-settings.html。F11 设置页（本轮按基线改为「只读状态一览」）：
     - eyebrow: Everything local, at a glance
     - 恰好 5 行，右侧一律 .state-pill 只读（国家 / 路径 / 每月检查 / 跟随外观 / 崩溃记录）
     - AL-B2：语言行、Change…、Check for updates、View licence 全部删除
     - 数据只从 get_settings 读，界面不提供任何修改入口（AL-F1）
     样式全部来自 assets/style.css。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { t } from "../i18n";
import { getSettings, licenseStatus } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import KvRow from "../components/KvRow.vue";

const country = ref("US");
const savePath = ref("Documents / BizSpark");
const libCheck = ref(true);
const followSystem = ref(true);
const crashNotes = ref(false);
const lic = ref<string>("");
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
  const l = await licenseStatus();
  if (l && typeof l.status === "string") {
    lic.value = l.status === "activated" ? t("settings.lic_ok") : t("settings.lic_none");
  }
});
</script>

<template>
  <AppShell>
    <div class="page-head">
      <div class="eyebrow">{{ t("settings.eyebrow") }}</div>
      <h1>{{ t("settings.h1") }}</h1>
      <p class="lead">{{ t("settings.lead") }}</p>
    </div>
    <div class="grid g2" style="align-items:start">
      <div class="card pad">
        <div class="set-row">
          <div><div class="st">{{ t("settings.country") }}</div><div class="sd">{{ t("settings.country_d") }}</div></div>
          <span class="state-pill">{{ countryLabel }}</span>
        </div>
        <div class="set-row">
          <div><div class="st">{{ t("settings.path") }}</div><div class="sd">{{ savePath }}</div></div>
          <span class="state-pill">{{ savePath }}</span>
        </div>
        <div class="set-row">
          <div><div class="st">{{ t("settings.libcheck") }}</div><div class="sd">{{ t("settings.libcheck_d") }}</div></div>
          <span class="state-pill">{{ libCheck ? t("settings.v_auto") : t("settings.v_off") }}</span>
        </div>
        <div class="set-row">
          <div><div class="st">{{ t("settings.appearance") }}</div><div class="sd">{{ t("settings.appearance_d") }}</div></div>
          <span class="state-pill">{{ followSystem ? t("settings.v_on") : t("settings.v_off") }}</span>
        </div>
        <div class="set-row">
          <div><div class="st">{{ t("settings.crash") }}</div><div class="sd">{{ t("settings.crash_d") }}</div></div>
          <span class="state-pill">{{ crashNotes ? t("settings.v_on") : t("settings.v_off") }}</span>
        </div>
      </div>
      <div>
        <div class="card pad">
          <div class="eyebrow">{{ t("settings.privacy_eyebrow") }}</div>
          <h2 style="font-size:19px;line-height:1.4">{{ t("settings.privacy_h") }}</h2>
          <p class="tiny" style="margin-top:12px">{{ t("settings.privacy_p") }}</p>
        </div>
        <div class="card pad" style="margin-top:16px">
          <h3>{{ t("settings.about_h") }}</h3>
          <KvRow :k="t('settings.about_ver')" :v="ver" />
          <KvRow :k="t('settings.about_lib')" v="2026.11 (312)" />
          <KvRow :k="t('settings.about_lic')" :v="lic || '—'" :accent="lic !== ''" />
          <KvRow :k="t('settings.about_account')" v="None" />
          <div class="tiny" style="margin-top:14px">{{ t("settings.about_foot") }}</div>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<!-- Settings.vue — B-09/B-10（负责人：B）
     对应 en/html/09-settings.html。F11 设置页：
     - 6 行封顶：Country / Language / Save location / Library check / Appearance / Crash notes
     - get_settings / set_settings（静默）；About 卡（版本/库/授权/账号）
     - F12 轻更新提示只提示不安装 -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { t } from "../i18n";
import { getSettings, licenseStatus, setSettings } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import KvRow from "../components/KvRow.vue";
import Toggle from "../components/Toggle.vue";

const country = ref("US");
const savePath = ref("Documents / BizSpark");
const libCheck = ref(true);
const followSystem = ref(true);
const crashNotes = ref(false);
const lic = ref<string>("");
const ver = ref("1.0.0");

const COUNTRIES: Array<{ v: string; label: string }> = [
  { v: "US", label: "🇺🇸 United States" }, { v: "CA", label: "🇨🇦 Canada" },
  { v: "UK", label: "🇬🇧 United Kingdom" }, { v: "AU", label: "🇦🇺 Australia" },
  { v: "SG", label: "🇸🇬 Singapore" }, { v: "PH", label: "🇵🇭 Philippines" },
];

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

async function patch(k: string, v: unknown): Promise<void> {
  await setSettings({ [k]: v }); // 静默
}
</script>

<template>
  <AppShell>
    <div class="page-head">
      <div class="eyebrow">{{ t("settings.eyebrow") }}</div>
      <h1>{{ t("settings.h1") }}</h1>
      <p class="lead">{{ t("settings.lead") }}</p>
    </div>
    <div class="grid g2 align-start">
      <div class="card pad">
        <div class="set-row">
          <div><div class="st">{{ t("settings.country") }}</div><div class="sd">{{ t("settings.country_d") }}</div></div>
          <select class="sel-box" :value="country" @change="country = String(($event.target as HTMLSelectElement).value); patch('country', country)">
            <option v-for="c in COUNTRIES" :key="c.v" :value="c.v">{{ c.label }}</option>
          </select>
        </div>
        <div class="set-row">
          <div><div class="st">{{ t("settings.lang") }}</div><div class="sd">{{ t("settings.lang_d") }}</div></div>
          <div class="sel-box">English</div>
        </div>
        <div class="set-row">
          <div><div class="st">{{ t("settings.path") }}</div><div class="sd">{{ savePath }}</div></div>
          <button class="btn btn-ghost sm-btn" type="button">{{ t("settings.path_change") }}</button>
        </div>
        <div class="set-row">
          <div><div class="st">{{ t("settings.libcheck") }}</div><div class="sd">{{ t("settings.libcheck_d") }}</div></div>
          <Toggle :on="libCheck" @update:on="(v) => { libCheck = v; patch('library_check', v) }" />
        </div>
        <div class="set-row">
          <div><div class="st">{{ t("settings.appearance") }}</div><div class="sd">{{ t("settings.appearance_d") }}</div></div>
          <Toggle :on="followSystem" @update:on="(v) => { followSystem = v; patch('follow_system_appearance', v) }" />
        </div>
        <div class="set-row">
          <div><div class="st">{{ t("settings.crash") }}</div><div class="sd">{{ t("settings.crash_d") }}</div></div>
          <Toggle :on="crashNotes" @update:on="(v) => { crashNotes = v; patch('crash_notes', v) }" />
        </div>
      </div>
      <div>
        <div class="card pad">
          <div class="eyebrow">{{ t("settings.privacy_eyebrow") }}</div>
          <h2 class="priv-h">{{ t("settings.privacy_h") }}</h2>
          <p class="tiny mt12">{{ t("settings.privacy_p") }}</p>
        </div>
        <div class="card pad mt16">
          <h3>{{ t("settings.about_h") }}</h3>
          <KvRow :k="t('settings.about_ver')" :v="ver" />
          <KvRow :k="t('settings.about_lib')" v="2026.11 (312)" />
          <KvRow :k="t('settings.about_lic')" :v="lic || '—'" :accent="lic !== ''" />
          <KvRow :k="t('settings.about_account')" v="None" />
          <div class="btn-row mt18">
            <button class="btn btn-ghost sm-btn2" type="button">{{ t("settings.check_updates") }}</button>
            <button class="btn btn-quiet sm-text" type="button">{{ t("settings.view_licence") }}</button>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.align-start{align-items:start}
.set-row{display:flex;align-items:center;justify-content:space-between;padding:15px 2px;border-bottom:1px solid var(--line)}
.set-row:last-child{border:0}
.set-row .st{font-size:13.5px;font-weight:620}
.set-row .sd{font-size:11.5px;color:var(--ink-3);margin-top:2px}
.sel-box{border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:12.5px;background:var(--surface-2);min-width:130px;text-align:left;color:var(--ink)}
.sm-btn{height:34px;font-size:12px}
.sm-btn2{height:36px;font-size:12px}
.sm-text{font-size:12px}
.priv-h{font-size:19px;line-height:1.4}
.mt12{margin-top:12px}
.mt16{margin-top:16px}
.mt18{margin-top:18px}
</style>

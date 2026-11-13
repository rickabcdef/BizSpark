<!-- Export.vue — B-09（负责人：B）
     对应 en/html/05-export.html。F06 完成页：
     大绿勾 → eyebrow → H1 → 说明 → 文件行 → Open folder / Find another idea
     → 分隔线 → 小字（价格配置渲染 export-note，首版不含金额）。
     export_plan 走 A 的另存为对话框；Open folder 调 A 的系统能力。 -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { exportPlan, openExportFolder } from "../bridge/cmd";
import { renderPriceSlots } from "../bridge/price";
import AppShell from "../components/AppShell.vue";
import Tag from "../components/Tag.vue";

const router = useRouter();
const fileName = ref<string>("");
const fileMeta = ref<string>("");
const done = ref(false);
const lastDir = ref<string>("");

async function runExport(): Promise<void> {
  // 路径由 A 的另存为对话框决定（B 只传目标 id；path 占位空串由 A 端接管对话框）
  const r = await exportPlan(String(history.state?.ideaId || ""), "");
  if (r) {
    fileName.value = r.file_name || "";
    fileMeta.value = t("export.file_meta", { dir: "Documents / BizSpark", kb: Math.max(1, Math.round((r.bytes || 0) / 1024)), pages: r.pages || 1 });
    done.value = true;
  }
}

function openFolder(): void {
  void openExportFolder(lastDir.value);
}

onMounted(() => {
  renderPriceSlots();
  void runExport();
});
</script>

<template>
  <AppShell>
    <div class="card center-card">
      <div class="big-check">✓</div>
      <div class="eyebrow">{{ t("export.eyebrow") }}</div>
      <h1>{{ t("export.h1") }}</h1>
      <p class="lead lead-c">{{ t("export.lead") }}</p>
      <div v-if="done" class="file-row">
        <div class="file-ico">▤</div>
        <div class="fgrow">
          <div class="fn">{{ fileName }}</div>
          <div class="fs">{{ fileMeta }}</div>
        </div>
        <Tag :green="true">✓ {{ t("export.saved_tag") }}</Tag>
      </div>
      <div class="btn-row center">
        <button class="btn btn-primary" type="button" :disabled="!done" @click="openFolder">{{ t("export.open_folder") }}</button>
        <button class="btn btn-ghost" type="button" @click="router.push('/results')">{{ t("export.another") }}</button>
      </div>
      <div class="hr"></div>
      <div class="tiny" data-price-slot="export-note"></div>
    </div>
    <div class="card pad extras">
      <div class="grid g2 g-extras">
        <div><h3>{{ t("export.inside_h") }}</h3><p class="tiny mt6">{{ t("export.inside_p") }}</p></div>
        <div><h3>{{ t("export.extras_h") }}</h3><p class="tiny mt6">{{ t("export.extras_p") }}</p></div>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.center-card{max-width:620px;margin:24px auto 0;text-align:center;padding:46px 40px}
.big-check{width:74px;height:74px;border-radius:50%;background:var(--green-soft);color:var(--green);
  display:grid;place-items:center;font-size:34px;margin:0 auto 22px;box-shadow:0 0 0 12px rgba(31,138,112,.06)}
.lead-c{margin:10px auto 0}
.file-row{display:flex;align-items:center;gap:13px;background:var(--surface-2);border:1px solid var(--line);
  border-radius:12px;padding:13px 16px;text-align:left;margin:24px 0}
.file-ico{width:38px;height:38px;border-radius:9px;background:var(--accent-soft);color:var(--accent);display:grid;place-items:center;font-size:17px}
.fgrow{flex:1}
.fn{font-size:13px;font-weight:650}
.fs{font-size:11px;color:var(--ink-3)}
.center{justify-content:center}
.extras{max-width:620px;margin:18px auto 0}
.g-extras{gap:14px}
.mt6{margin-top:6px}
</style>

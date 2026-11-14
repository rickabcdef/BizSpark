<!-- Export.vue — B-09（负责人：B）
     对应 en/html/05-export.html。F06 完成页：
     大绿勾 → eyebrow → H1 → 说明 → 文件行 → 两个真按钮 → 两张说明卡
     AL-A3：Open folder 只在系统能力真实可用时渲染（静态基线不摆空壳；
            浏览器试玩/开发模式下没有系统文件管理器能力 → 不渲染）。
     样式全部来自 assets/style.css。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { t } from "../i18n";
import { exportPlan, openExportFolder } from "../bridge/cmd";
import { renderPriceSlots } from "../bridge/price";
import AppShell from "../components/AppShell.vue";
import Tag from "../components/Tag.vue";

const fileName = ref<string>("");
const fileMeta = ref<string>("");
const done = ref(false);
const lastDir = ref<string>("");

// 只有 Tauri 壳内（非浏览器试玩）才有打开系统文件夹的能力
const canOpenFolder = computed(() => {
  const w = window as unknown as { __TAURI_INTERNALS__?: unknown; BIZSPARK_DEV?: boolean };
  return !!w.__TAURI_INTERNALS__ && !w.BIZSPARK_DEV;
});

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
      <p class="lead" style="margin:10px auto 0">{{ t("export.lead") }}</p>
      <div v-if="done" class="file-row">
        <div class="file-ico">▤</div>
        <div style="flex:1">
          <div class="fn">{{ fileName }}</div>
          <div class="fs">{{ fileMeta }}</div>
        </div>
        <Tag :green="true">✓ {{ t("export.saved_tag") }}</Tag>
      </div>
      <div class="btn-row" style="justify-content:center">
        <router-link class="btn btn-primary" to="/saved">{{ t("export.open_saved") }}</router-link>
        <button v-if="done && canOpenFolder" class="btn btn-ghost" type="button" @click="openFolder">{{ t("export.open_folder") }}</button>
        <router-link class="btn btn-ghost" to="/results">{{ t("export.another") }}</router-link>
      </div>
      <div class="hr"></div>
      <div class="tiny" data-price-slot="export-note"></div>
    </div>
    <div class="card pad" style="max-width:620px;margin:18px auto 0">
      <div class="grid g2" style="gap:14px">
        <div><h3>{{ t("export.inside_h") }}</h3><p class="tiny" style="margin-top:6px">{{ t("export.inside_p") }}</p></div>
        <div><h3>{{ t("export.extras_h") }}</h3><p class="tiny" style="margin-top:6px">{{ t("export.extras_p") }}</p></div>
      </div>
    </div>
  </AppShell>
</template>

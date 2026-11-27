<!-- Export.vue — 对齐最新版原型 05-export。
     脚本（runExport 自动导出、canOpenFile 能力判断、openPdf/openFolder、价格槽渲染）全部保留。
     基线：居中成功环 + 眉题 + 标题 + 说明；文件卡；主按钮打开已存；并排两次按钮；两张说明卡。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { exportPlan, openExportFolder, openFile, saveExportDialog } from "../bridge/cmd";
import { renderPriceSlots } from "../bridge/price";
import AppShell from "../components/AppShell.vue";
import Icon from "../components/Icon.vue";

const router = useRouter();
const fileName = ref<string>("");
const filePath = ref<string>("");
const fileMeta = ref<string>("");
const done = ref(false);

// 只有 Tauri 壳内（非浏览器试玩）才有打开系统文件/阅读器的能力
const canOpenFile = computed(() => {
  const w = window as unknown as { __TAURI_INTERNALS__?: unknown; BIZSPARK_DEV?: boolean };
  return !!w.__TAURI_INTERNALS__ && !w.BIZSPARK_DEV;
});

async function runExport(): Promise<void> {
  // PM 2026-11-27：此前直接传空 path——引擎契约空=用户取消（T-34），导出从未发生，
  // 而本页仍渲染成功标题 → 假成功页。现按设计补齐：先弹另存对话框，再交给引擎写盘；
  // 取消或引擎失败一律静默回详情，绝不显示假成功。
  const ideaId = String(history.state?.ideaId || "");
  const target = await saveExportDialog("BizSpark-Plan.pdf", ["pdf"]);
  if (!target) {
    router.back();
    return;
  }
  const r = await exportPlan(ideaId, target);
  if (!r) {
    router.back();
    return;
  }
  fileName.value = r.file_name || "";
  filePath.value = r.path || "";
  const dir = filePath.value.replace(/[/\\][^/\\]+$/, "");
  fileMeta.value = t("export.file_meta", { dir: dir || "Documents / BizSpark", kb: Math.max(1, Math.round((r.bytes || 0) / 1024)), pages: r.pages || 1 });
  done.value = true;
}

function openPdf(): void {
  void openFile(filePath.value);
}

function openFolder(): void {
  void openExportFolder(filePath.value);
}

onMounted(() => {
  renderPriceSlots();
  void runExport();
});
</script>

<template>
  <AppShell>
    <div class="topbar">
      <button class="icon-btn" type="button" aria-label="关闭" @click="router.push('/')">
        <Icon name="close" :size="22" />
      </button>
      <div style="display:flex;align-items:center;gap:12px">
        <div class="side"><span style="width:8px;height:8px;border-radius:50%;background:var(--success);display:inline-block;"></span>{{ t("side.chip") }}</div>
        <button class="icon-btn" type="button" aria-label="帮助">
          <Icon name="help" :size="22" />
        </button>
      </div>
    </div>

    <div class="content" style="padding-top:6px">
      <div class="export-head">
        <div class="success-ring"><span class="check-big"><Icon name="check" :size="38" /></span></div>
        <div class="eyebrow">{{ t("export.eyebrow") }}</div>
        <h1>{{ t("export.h1") }}</h1>
        <p class="lead">{{ t("export.lead") }}</p>
      </div>

      <div class="card" style="margin-top:20px">
        <div v-if="done" class="file-card">
          <span class="file-ico"><Icon name="doc" :size="24" /></span>
          <div class="file-main">
            <button v-if="canOpenFile" type="button" class="file-name file-name-link" @click="openPdf">
              {{ fileName }}<Icon name="open" :size="15" />
            </button>
            <div v-else class="file-name">{{ fileName }}</div>
            <div class="file-meta">{{ fileMeta }}</div>
            <div v-if="!canOpenFile" class="file-hint">{{ t("export.web_hint") }}</div>
          </div>
          <span class="badge-saved">{{ t("export.saved_tag") }}</span>
        </div>
        <router-link class="btn btn-primary" style="margin-top:16px" to="/saved">{{ t("export.open_saved") }}&nbsp;→</router-link>
        <div class="btn-row" style="margin-top:12px">
          <button v-if="done && canOpenFile" class="btn btn-secondary" type="button" @click="openFolder">
            <Icon name="folder" :size="18" />{{ t("export.open_folder") }}</button>
          <router-link class="btn btn-secondary" to="/quiz">
            <Icon name="search" :size="18" />{{ t("export.another") }}</router-link>
        </div>
        <div class="tiny mt10" data-price-slot="export-note"></div>
      </div>

      <div class="card info-card">
        <span class="ico"><Icon name="doc" :size="22" /></span>
        <div><h3>{{ t("export.inside_h") }}</h3><p>{{ t("export.inside_p") }}</p></div>
      </div>
      <div class="card info-card">
        <span class="ico"><Icon name="list" :size="22" /></span>
        <div><h3>{{ t("export.extras_h") }}</h3><p>{{ t("export.extras_p") }}</p></div>
      </div>
    </div>
  </AppShell>
</template>

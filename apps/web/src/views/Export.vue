<!-- Export.vue — 对齐最新版原型 05-export。
     脚本（runExport 自动导出、canOpenFolder 能力判断、openFolder、价格槽渲染）全部保留。
     基线：居中成功环 + 眉题 + 标题 + 说明；文件卡；主按钮打开已存；并排两次按钮；两张说明卡。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { exportPlan, openExportFolder } from "../bridge/cmd";
import { renderPriceSlots } from "../bridge/price";
import AppShell from "../components/AppShell.vue";
import Icon from "../components/Icon.vue";

const router = useRouter();
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
    <div class="topbar">
      <button class="icon-btn" type="button" aria-label="关闭" @click="router.push('/')">
        <Icon name="close" :size="22" />
      </button>
      <div class="title">{{ t("nav.export") }}</div>
      <button class="icon-btn" type="button" aria-label="帮助">
        <Icon name="help" :size="22" />
      </button>
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
            <div class="file-name">{{ fileName }}</div>
            <div class="file-meta">{{ fileMeta }}</div>
          </div>
          <span class="badge-saved">{{ t("export.saved_tag") }}</span>
        </div>
        <router-link class="btn btn-primary" style="margin-top:16px" to="/saved">{{ t("export.open_saved") }}&nbsp;→</router-link>
        <div class="btn-row" style="margin-top:12px">
          <button v-if="done && canOpenFolder" class="btn btn-secondary" type="button" @click="openFolder">
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
        <span class="ico"><Icon name="card" :size="22" /></span>
        <div><h3>{{ t("export.extras_h") }}</h3><p>{{ t("export.extras_p") }}</p></div>
      </div>
    </div>
  </AppShell>
</template>

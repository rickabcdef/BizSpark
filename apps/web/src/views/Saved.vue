<!-- Saved.vue — 对齐最新版原型 06-saved。
     脚本（listSaved 倒序列表、SavedItem 结构）全部保留；对照 / 清空属 Backlog，界面不摆。
     基线：顶栏页名 + 显示器 chip；头部无眉题；插画卡（标题 / meta / 胶囊打开 / 书签角标）；
     找新点子主按钮 + 回到 3 个点子描边按钮；底部 notice 注脚。 -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { t } from "../i18n";
import { listSaved } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import Icon from "../components/Icon.vue";

interface SavedItem { id: string; title?: string; saved_at?: string; min_capital?: string }
const items = ref<SavedItem[]>([]);

const ILLUS = [
  '<path d="M20 55 L80 30 L140 55"/><path d="M28 55 h104 v55 H28 z"/><path d="M28 55 q13 12 26 0 q13 12 26 0 q13 12 26 0 q13 12 26 0"/><rect x="62" y="78" width="36" height="32"/>',
  '<path d="M30 90 V55 L80 25l50 30v35"/><path d="M55 90 V65h50v25"/><path d="M70 90V75h20v15"/>',
];

onMounted(async () => {
  const r = await listSaved();
  items.value = (r?.items as SavedItem[]) || [];
});
</script>

<template>
  <AppShell>
    <div class="topbar">
      <div class="title">{{ t("nav.saved") }}</div>
      <div class="side"><Icon name="monitor" :size="18" />{{ t("side.chip") }}</div>
    </div>

    <div class="saved-head">
      <h1>{{ t("saved.h1") }}</h1>
      <p class="lead">{{ t("saved.lead") }}</p>
    </div>

    <div class="content" style="padding-top:0">
      <template v-for="(it, i) in items" :key="it.id">
        <div class="saved-card">
          <div class="saved-illu" aria-hidden="true">
            <svg viewBox="0 0 160 130" fill="none" stroke="#56616E" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
              v-html="ILLUS[i % 2]"></svg>
          </div>
          <div class="saved-body">
            <div class="saved-title">{{ it.title || it.id }}</div>
            <div class="saved-meta">{{ [t("saved.meta_prefix"), it.min_capital || it.saved_at].filter(Boolean).join(" · ") }}</div>
            <div class="open-btn">
              <router-link :to="`/detail/${it.id}`">{{ t("saved.open") }}</router-link>
            </div>
          </div>
          <span class="bookmark"><Icon name="bookmark" :size="22" /></span>
        </div>
      </template>

      <div v-if="items.length === 0" class="empty card">
        <Icon name="bookmark" :size="34" />
        <p>{{ t("saved.empty") }}</p>
      </div>

      <template v-if="items.length">
        <router-link class="btn btn-primary" to="/quiz">{{ t("saved.find_new") }}&nbsp;→</router-link>
        <router-link class="btn btn-outline" style="margin-top:12px" to="/results">← {{ t("results.cta_back3") }}</router-link>
      </template>

      <div class="notice" style="margin-top:18px">
        <span class="ico"><Icon name="bulb" :size="20" /></span>
        <div>{{ t("saved.foot") }}</div>
      </div>
    </div>
  </AppShell>
</template>

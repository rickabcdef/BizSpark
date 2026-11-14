<!-- Saved.vue — B-09（负责人：B）
     对应 en/html/06-saved.html。F07 我的点子：
     - list_saved（saved_at 倒序）+ mini 卡（thumb / 标题 / 保存行 / Open）
     - AL-B2：Compare two ideas 与 Clear saved list 属 V2 Backlog，第一版界面不摆（本轮已移除）
     - 空态
     样式全部来自 assets/style.css。 -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { t } from "../i18n";
import { listSaved } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";

interface SavedItem { id: string; title?: string; saved_at?: string; match_pct?: number; min_capital?: string }
const items = ref<SavedItem[]>([]);
const THUMBS = ["✦", "▣", "◈"];

onMounted(async () => {
  const r = await listSaved();
  items.value = (r?.items as SavedItem[]) || [];
});
</script>

<template>
  <AppShell>
    <div class="page-head">
      <div class="eyebrow">{{ t("saved.eyebrow") }}</div>
      <h1>{{ t("saved.h1") }}</h1>
      <p class="lead">{{ t("saved.lead") }}</p>
    </div>
    <div v-if="items.length" class="grid" style="gap:12px">
      <div v-for="(it, i) in items" :key="it.id" class="card mini">
        <div class="thumb">{{ THUMBS[i % 3] }}</div>
        <div class="mt">
          <h3>{{ it.title || it.id }}</h3>
          <p>{{ it.saved_at || "" }}<template v-if="it.min_capital"> · {{ it.min_capital }}</template><template v-if="it.match_pct"> · {{ it.match_pct }}% {{ t("common.match") }}</template></p>
        </div>
        <router-link class="btn btn-ghost" style="height:34px;font-size:12px" :to="`/detail/${it.id}`">{{ t("saved.open") }}</router-link>
      </div>
    </div>
    <div v-else class="empty card">
      <div class="ico">❑</div>
      <p>{{ t("saved.empty") }}</p>
    </div>
    <div class="hr"></div>
    <div class="btn-row">
      <router-link class="btn btn-primary" to="/quiz">{{ t("saved.find_new") }}&nbsp;→</router-link>
      <router-link class="btn btn-ghost" to="/results">{{ t("results.cta_back3") }}</router-link>
    </div>
    <div class="foot-note">💡 {{ t("saved.foot") }}</div>
  </AppShell>
</template>

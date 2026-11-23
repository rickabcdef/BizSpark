<!-- Detail.vue — 对齐最新版原型 04-detail。
     脚本（getIdea 取数、diagnose 回填序号、goExport 带 ideaId 跳导出）全部保留。
     基线：纵向单栏——概览 / 成本（橙色合计条）/ 7 步 / 渠道标签 / 三个坑 / 一页纸方案卡。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { t } from "../i18n";
import { diagnose, getIdea, getState } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import Icon from "../components/Icon.vue";

interface CostItem { item?: string; amount?: string }
interface IdeaDetail {
  id?: string; title?: string; rank?: number; summary?: string;
  tags?: string[];
  costs?: CostItem[]; total_to_first_invoice?: string;
  steps?: string[]; channels?: string[]; pitfalls?: string[];
}
const route = useRoute();
const router = useRouter();
const d = ref<IdeaDetail | null>(null);

const costRows = computed(() => (d.value?.costs || []).filter((c) => c.item && c.amount));
const stepItems = computed(() => (d.value?.steps || []).map((s) => String(s)));
const channelItems = computed(() => d.value?.channels || []);
const pitfallItems = computed(() => d.value?.pitfalls || []);
const costRowIcons = ["phone", "pen", "upload"];
function costIcon(i: number): string { return costRowIcons[i] || "coin"; }

onMounted(async () => {
  d.value = await getIdea(String(route.params.id || ""));
  // 序号回填：get_idea 不带 rank，与 Results 同口径重放 diagnose；找不到按 01 降级。
  if (d.value) {
    try {
      const st = await getState();
      const la = (st && (st.last_answers as Record<string, string | string[]>)) || {};
      const r = await diagnose(Object.keys(la).length ? la : {});
      const hit = ((r?.ideas as Array<Record<string, unknown>>) || []).find(
        (x) => String(x.id || "") === String(d.value?.id || ""),
      );
      if (hit && typeof hit.rank === "number") {
        d.value = { ...d.value, rank: hit.rank };
      }
    } catch { /* diagnose 失败时序号按 01 降级 */ }
  }
});

function goExport(): void {
  router.push({ path: "/export", state: { ideaId: String(d.value?.id || route.params.id || "") } });
}
</script>

<template>
  <AppShell>
    <div class="topbar">
      <div style="display:flex;align-items:center;gap:10px">
        <button class="icon-btn" type="button" aria-label="返回" @click="router.push('/results')">
          <Icon name="chevron" :size="22" />
        </button>
      </div>
      <div class="side"><span style="width:8px;height:8px;border-radius:50%;background:var(--success);display:inline-block;"></span>{{ t("side.chip") }}</div>
    </div>

    <div v-if="d" class="content" style="padding-top:6px">
      <!-- 概览卡 -->
      <div class="card">
        <div class="eyebrow">{{ t("detail.eyebrow", { rank: String((d?.rank ?? 1)).padStart(2, "0"), total: "03" }) }}</div>
        <h1 style="font-size:28px;font-weight:800;margin:6px 0 6px">{{ d?.title || t("detail.loading") }}</h1>
        <p class="lead">{{ d?.summary || "" }}</p>
        <div v-if="d?.tags?.length" class="tags">
          <span v-for="(tg, i) in d.tags" :key="i" class="tag">{{ tg }}</span>
        </div>
      </div>

      <!-- 成本卡 -->
      <div v-if="costRows.length" class="card">
        <div class="card-title"><span class="ico"><Icon name="clock" :size="20" /></span>{{ t("detail.costs_h") }}</div>
        <div v-for="(c, i) in costRows" :key="i" class="row">
          <span class="row-main"><Icon :name="costIcon(i)" :size="18" />{{ c.item }}</span>
          <span class="row-val">{{ c.amount }}</span>
        </div>
        <div v-if="d?.total_to_first_invoice" class="cost-total">
          <Icon name="receipt" :size="18" />{{ t("detail.costs_total") }} · {{ d.total_to_first_invoice }}
        </div>
        <p class="cost-note">{{ t("detail.cost_note") }}</p>
      </div>

      <!-- 前 7 步 -->
      <div v-if="stepItems.length" class="card">
        <div class="card-title"><span class="ico"><Icon name="doc" :size="20" /></span>{{ t("detail.steps_h") }}</div>
        <div v-for="(s, i) in stepItems" :key="i" class="step">
          <span class="num">{{ String(i + 1).padStart(2, "0") }}</span>
          <span class="step-text">{{ s }}</span>
          <span class="check"><Icon name="check-circle" :size="18" /></span>
        </div>
      </div>

      <!-- 第一批客户 -->
      <div v-if="channelItems.length" class="card">
        <div class="card-title"><span class="ico"><Icon name="user" :size="20" /></span>{{ t("detail.channels_h") }}</div>
        <div class="source-tags">
          <span v-for="(c, i) in channelItems" :key="i" class="tag">{{ c }}</span>
        </div>
      </div>

      <!-- 三个坑 -->
      <div v-if="pitfallItems.length" class="card">
        <div class="card-title"><span class="ico"><Icon name="alert" :size="20" /></span>{{ t("detail.pitfalls_h") }}</div>
        <div v-for="(p, i) in pitfallItems" :key="i" class="pitfall">
          <span class="ico"><Icon name="info" :size="16" /></span>{{ p }}
        </div>
      </div>

      <!-- 一页纸方案卡 -->
      <div class="card">
        <div class="card-title"><span class="ico"><Icon name="doc" :size="20" /></span>{{ t("detail.paper_eyebrow") }}</div>
        <div class="pdf-preview">
          <div class="pdf-sheet">
            <div class="ps-title">{{ d?.title || "" }}</div>
            <div class="ps-line"></div><div class="ps-line"></div><div class="ps-line" style="width:60%"></div>
          </div>
        </div>
        <p class="lead" style="color:var(--ink-2);font-size:14px">{{ t("detail.paper_note") }}</p>
        <button class="btn btn-primary" type="button" style="margin-top:14px" @click="goExport">{{ t("detail.cta_export") }}&nbsp;↓</button>
        <router-link class="btn btn-secondary" style="margin-top:12px" to="/results">← {{ t("detail.cta_back") }}</router-link>
      </div>

      <p class="foot-note"><Icon name="lock" :size="16" />{{ t("detail.privacy") }}</p>
    </div>

    <div v-if="!d" class="empty card">
      <Icon name="doc" :size="34" />
      <p>{{ t("results.empty") }}</p>
      <router-link class="btn btn-ghost mt18" to="/results">← {{ t("detail.cta_back") }}</router-link>
    </div>
  </AppShell>
</template>

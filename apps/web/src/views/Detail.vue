<!-- Detail.vue — B-08（负责人：B）
     对应 en/html/04-detail.html。F05 详情组件：
     - 4 个内容卡顺序照 DOM：costs → steps → channels → pitfalls（不加第五张卡）
     - 右侧 sticky（一页纸 PaperPreview + 导出按钮）
     - 脏字段不显示 undefined：v-if 有值才渲染
     数据：get_idea(id)（C+D 装配的完整详情对象）；失败走空态。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { t } from "../i18n";
import { getIdea } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import KvRow from "../components/KvRow.vue";
import StepList from "../components/StepList.vue";
import PaperPreview from "../components/PaperPreview.vue";

interface CostItem { item?: string; amount?: string }
interface IdeaDetail {
  id?: string; title?: string; match_pct?: number; rank?: number; summary?: string;
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

onMounted(async () => {
  d.value = await getIdea(String(route.params.id || ""));
});
</script>

<template>
  <AppShell>
    <div class="page-head">
      <div class="eyebrow">{{ t("detail.eyebrow", { rank: String((d?.rank ?? 1)).padStart(2, "0"), total: "03", match: String(d?.match_pct ?? "") }) }}</div>
      <h1>{{ d?.title || t("detail.loading") }}</h1>
      <p class="lead">{{ d?.summary || "" }}</p>
    </div>
    <div v-if="d" class="detail-wrap">
      <div>
        <!-- 卡 1：起步成本 -->
        <div class="card sec">
          <div class="sec-h"><span class="b">$</span><h3>{{ t("detail.costs_h") }}</h3></div>
          <KvRow v-for="(c, i) in costRows" :key="i" :k="c.item || ''" :v="c.amount || ''"
            :bold-key="c.item === d?.costs?.[d.costs.length - 1]?.item" />
          <KvRow v-if="d.total_to_first_invoice" :k="t('detail.costs_total')" :v="d.total_to_first_invoice" :accent="true" :bold-key="true" />
        </div>
        <!-- 卡 2：前 7 步 -->
        <div class="card sec">
          <div class="sec-h"><span class="b">1</span><h3>{{ t("detail.steps_h") }}</h3></div>
          <StepList :items="stepItems" />
        </div>
        <!-- 卡 3：第一批客户从哪来 -->
        <div class="card sec">
          <div class="sec-h"><span class="b">↗</span><h3>{{ t("detail.channels_h") }}</h3></div>
          <div class="pill-list"><span v-for="(c, i) in channelItems" :key="i" class="pill">{{ c }}</span></div>
        </div>
        <!-- 卡 4：三个坑 -->
        <div class="card sec">
          <div class="sec-h"><span class="b">!</span><h3>{{ t("detail.pitfalls_h") }}</h3></div>
          <div v-for="(p, i) in pitfallItems" :key="i" class="warn">{{ p }}</div>
        </div>
      </div>
      <div class="sticky">
        <div class="card pad">
          <div class="eyebrow">{{ t("detail.paper_eyebrow") }}</div>
          <PaperPreview :title="d.title || ''" />
          <div class="tiny paper-note">{{ t("detail.paper_note") }}</div>
          <button class="btn btn-primary w100" type="button"
            @click="router.push({ path: '/export', state: { ideaId: String(d?.id || route.params.id || '') } })">{{ t("detail.cta_export") }}&nbsp;↓</button>
          <button class="btn btn-ghost w100 mt10" type="button" @click="router.push('/results')">← {{ t("detail.cta_back") }}</button>
        </div>
        <div class="foot-note">🔒 {{ t("detail.privacy") }}</div>
      </div>
    </div>
    <div v-else class="empty card">
      <div class="ico">▤</div>
      <p>{{ t("results.empty") }}</p>
      <button class="btn btn-ghost" type="button" @click="router.push('/results')">← {{ t("detail.cta_back") }}</button>
    </div>
  </AppShell>
</template>

<style scoped>
.detail-wrap{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:24px;align-items:start}
.sec{padding:24px 26px;margin-bottom:16px}
.sec-h{display:flex;align-items:center;gap:10px;margin-bottom:16px}
.sec-h .b{width:26px;height:26px;border-radius:8px;background:var(--accent-soft);color:var(--accent);
  display:grid;place-items:center;font-size:12px;font-weight:800}
.pill-list{display:flex;flex-wrap:wrap;gap:8px}
.pill{font-size:12px;padding:7px 12px;border:1px solid var(--line);border-radius:10px;background:var(--surface-2)}
.warn{background:#FFF8EC;border:1px solid #F2E2BE;border-radius:10px;padding:11px 13px;font-size:12.3px;color:#7A5A1E;margin-bottom:8px}
.sticky{position:sticky;top:24px}
.paper-note{margin:18px 0 14px}
.w100{width:100%}
.mt10{margin-top:10px}
</style>

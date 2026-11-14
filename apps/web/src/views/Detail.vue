<!-- Detail.vue — B-08（负责人：B）
     对应 en/html/04-detail.html。F05 一页方案：
     - 恰好 4 张内容卡（成本 / 7 步 / 第一批客户 / 3 个坑），不摆第 5 张
     - 定价提示与合规句只进 PDF 与数据对象，页面上不另立卡片
     - 右侧 sticky：纸样预览 + Export my plan + 返回 3 个点子
     样式全部来自 assets/style.css；仅保留基线里的内联间距。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { t } from "../i18n";
import { diagnose, getIdea, getState, listSaved } from "../bridge/cmd";
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
  // 基线 eyebrow 是「Idea 01 / 03 · 94% match」，但 get_idea 的 IdeaDetail 不带
  // match_pct/rank（这两个字段只在 diagnose 卡片对象里）。与 Results 同口径重放
  // diagnose（只读计算，非新功能），按 id 回填；找不到就保持空（深链降级）。
  if (d.value) {
    try {
      const st = await getState();
      const la = (st && (st.last_answers as Record<string, string | string[]>)) || {};
      const r = await diagnose(Object.keys(la).length ? la : {});
      const hit = ((r?.ideas as Array<Record<string, unknown>>) || []).find(
        (x) => String(x.id || "") === String(d.value?.id || ""),
      );
      if (hit) {
        d.value = {
          ...d.value,
          rank: typeof hit.rank === "number" ? hit.rank : d.value.rank,
          match_pct: typeof hit.match_pct === "number" ? hit.match_pct : d.value.match_pct,
        };
      } else if (!d.value.match_pct) {
        // 深链/存档打开：该点子未必在当前 Top3 里（PM 2026-11-14 修复
        // 「· % 匹配」空百分比）。回退读存档时刻记录的 match_pct。
        const sv = await listSaved().catch(() => null);
        const savedHit = ((sv?.items as Array<Record<string, unknown>>) || []).find(
          (x) => String(x.id || "") === String(d.value?.id || ""),
        );
        const m = savedHit?.match_pct;
        if (typeof m === "number") d.value = { ...d.value, match_pct: m };
      }
    } catch { /* diagnose 失败时 eyebrow 百分比留空，不影响页面其余内容 */ }
  }
});

function goExport(): void {
  router.push({ path: "/export", state: { ideaId: String(d.value?.id || route.params.id || "") } });
}
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
          <div class="tiny" style="margin:18px 0 14px">{{ t("detail.paper_note") }}</div>
          <button class="btn btn-primary" style="width:100%" type="button" @click="goExport">{{ t("detail.cta_export") }}&nbsp;↓</button>
          <router-link class="btn btn-ghost" style="width:100%;margin-top:10px" to="/results">← {{ t("detail.cta_back") }}</router-link>
        </div>
        <div class="foot-note">🔒 {{ t("detail.privacy") }}</div>
      </div>
    </div>
    <div v-else class="empty card">
      <div class="ico">▤</div>
      <p>{{ t("results.empty") }}</p>
      <router-link class="btn btn-ghost" style="margin-top:18px" to="/results">← {{ t("detail.cta_back") }}</router-link>
    </div>
  </AppShell>
</template>

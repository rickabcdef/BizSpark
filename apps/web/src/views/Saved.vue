<!-- Saved.vue — B-09（负责人：B）
     对应 en/html/06-saved.html。F07 我的点子：
     - list_saved（saved_at 倒序）+ mini 卡（thumb/标题/保存行/Open）
     - Compare two ideas 两栏（compare_ideas，不足 2 条按钮置灰、不弹提示）
     - Clear saved：二次确认（本功能唯一允许的确认框，文案温和非红色）
     - 空态 -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { clearSaved, compareIdeas, listSaved, saveIdea } from "../bridge/cmd";
import AppShell from "../components/AppShell.vue";
import KvRow from "../components/KvRow.vue";

interface SavedItem { id: string; title?: string; saved_at?: string; match_pct?: number; min_capital?: string }
const router = useRouter();
const items = ref<SavedItem[]>([]);
const showConfirm = ref(false);
const compare = ref<{ left: Record<string, unknown>; right: Record<string, unknown> } | null>(null);
const THUMBS = ["✦", "▣", "◈"];

onMounted(async () => {
  const r = await listSaved();
  items.value = (r?.items as SavedItem[]) || [];
});

async function doClear(): Promise<void> {
  showConfirm.value = false;
  await clearSaved();
  items.value = [];
}

async function doCompare(): Promise<void> {
  if (items.value.length < 2) return; // 置灰前置
  const r = await compareIdeas([items.value[0].id, items.value[1].id]);
  if (r) compare.value = r as { left: Record<string, unknown>; right: Record<string, unknown> };
}

async function reopen(id: string): Promise<void> {
  await saveIdea(id); // 幂等：同 id 去重不覆盖时间
  router.push(`/detail/${id}`);
}
</script>

<template>
  <AppShell>
    <div class="page-head">
      <div class="eyebrow">{{ t("saved.eyebrow") }}</div>
      <h1>{{ t("saved.h1") }}</h1>
      <p class="lead">{{ t("saved.lead") }}</p>
    </div>
    <div v-if="items.length" class="grid list">
      <div v-for="(it, i) in items" :key="it.id" class="card mini">
        <div class="thumb">{{ THUMBS[i % 3] }}</div>
        <div class="mt">
          <h3>{{ it.title || it.id }}</h3>
          <p>{{ it.saved_at || "" }}<template v-if="it.min_capital"> · {{ it.min_capital }}</template><template v-if="it.match_pct"> · {{ it.match_pct }}% {{ t("common.match") }}</template></p>
        </div>
        <button class="btn btn-ghost open-btn" type="button" @click="reopen(it.id)">{{ t("saved.open") }}</button>
      </div>
    </div>
    <div v-else class="empty card">
      <div class="ico">❑</div>
      <p>{{ t("saved.empty") }}</p>
    </div>
    <div class="hr"></div>
    <div class="btn-row">
      <button class="btn btn-primary" type="button" @click="router.push('/quiz')">{{ t("saved.find_new") }}&nbsp;→</button>
      <button class="btn btn-ghost" type="button" :disabled="items.length < 2" @click="doCompare">{{ t("saved.compare") }}</button>
      <button class="btn btn-quiet" type="button" :disabled="!items.length" @click="showConfirm = true">{{ t("saved.clear") }}</button>
    </div>
    <div v-if="compare" class="card pad cmp">
      <div class="grid g2">
        <div>
          <h3>{{ String(compare.left.title ?? "") }}</h3>
          <KvRow v-for="(v, k) in compare.left" :key="String(k)" :k="String(k)" :v="String(v)" />
        </div>
        <div>
          <h3>{{ String(compare.right.title ?? "") }}</h3>
          <KvRow v-for="(v, k) in compare.right" :key="String(k)" :k="String(k)" :v="String(v)" />
        </div>
      </div>
    </div>
    <div class="foot-note">💡 {{ t("saved.foot") }}</div>

    <!-- 二次确认（温和文案，非红色） -->
    <div v-if="showConfirm" class="mask" @click.self="showConfirm = false">
      <div class="card pad confirm">
        <h3>{{ t("saved.confirm_h") }}</h3>
        <p class="tiny mt8">{{ t("saved.confirm_p") }}</p>
        <div class="btn-row mt18">
          <button class="btn btn-ghost" type="button" @click="doClear">{{ t("saved.confirm_yes") }}</button>
          <button class="btn btn-quiet" type="button" @click="showConfirm = false">{{ t("saved.confirm_no") }}</button>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.list{gap:12px}
.mini{display:flex;align-items:center;gap:14px;padding:16px 18px}
.mini .thumb{width:52px;height:52px;border-radius:12px;background:var(--deep);color:#fff;display:grid;place-items:center;font-size:20px}
.mini .mt{flex:1}
.mini .mt h3{font-size:14px}
.mini .mt p{font-size:11.5px;color:var(--ink-3);margin-top:3px}
.open-btn{height:34px;font-size:12px}
.cmp{margin-top:18px}
.mask{position:fixed;inset:0;background:rgba(16,24,32,.4);display:grid;place-items:center;z-index:20}
.confirm{max-width:420px}
.mt8{margin-top:8px}
.mt18{margin-top:18px}
</style>

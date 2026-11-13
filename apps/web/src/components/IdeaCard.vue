<!-- IdeaCard.vue — B-02/B-07（负责人：B）
     结果页 3 卡 .idea-card：顶部 3px 色条按卡序（accent/deep-2/green）。
     7 元素固定：色条/序号+匹配/标题/简介/why/标签行/按钮。 -->
<script setup lang="ts">
defineProps<{
  no: string;            // "01 / 03"
  match?: string;        // "94% MATCH"
  title: string;
  desc: string;
  why?: string;          // 完整 why 句（父组件用 t("results.why_prefix") 拼好）
  tags?: string[];
}>();
</script>

<template>
  <div class="card idea-card">
    <div class="idea-no">{{ no }} <span v-if="match" class="match">{{ match }}</span></div>
    <h3>{{ title }}</h3>
    <p>{{ desc }}</p>
    <div v-if="why" class="why" v-html="why"></div>
    <div class="meta-row"><span v-for="(tg, i) in tags || []" :key="i" class="tag">{{ tg }}</span></div>
    <slot></slot>
  </div>
</template>

<style scoped>
.idea-card{position:relative;overflow:hidden;padding:24px 22px 22px;display:flex;flex-direction:column;min-height:266px;transition:.2s}
.idea-card:hover{transform:translateY(-3px);box-shadow:var(--sh)}
.idea-card::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:var(--accent);opacity:.85}
.idea-card:nth-child(2)::before{background:var(--deep-2)}
.idea-card:nth-child(3)::before{background:var(--green)}
.idea-no{font-size:11px;letter-spacing:1.5px;color:var(--ink-3);font-weight:700}
.idea-card h3{font-size:17.5px;margin:12px 0 8px;line-height:1.32}
.idea-card p{font-size:12.8px;color:var(--ink-2);flex:1}
.why{background:var(--surface-2);border-radius:10px;padding:10px 12px;font-size:11.8px;color:var(--ink-2);margin:14px 0 16px;border-left:3px solid var(--gold)}
.why :deep(b){color:var(--ink)}
.meta-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.tag{font-size:10.5px;padding:4px 9px;border-radius:999px;background:var(--bg);border:1px solid var(--line);color:var(--ink-2)}
.match{margin-left:auto;font-size:11px;font-weight:700;color:var(--green);white-space:nowrap;align-self:center}
</style>

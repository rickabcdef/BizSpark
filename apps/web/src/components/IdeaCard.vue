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


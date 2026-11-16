<!-- IdeaCard.vue — B-02/B-07（负责人：B）
     结果页 3 卡 .idea-card：顶部 3px 色条按卡序（accent/deep-2/green）。
     6 元素固定：色条/序号/标题/简介/why/标签行/按钮。
     AL-B2（2026-11-16 基线）：按《诊断收口执行方案V1.0》撤掉匹配度百分比，
     序号只留「01 / 03」，不出现 % 与 MATCH 字样。 -->
<script setup lang="ts">
defineProps<{
  no: string;            // "01 / 03"
  title: string;
  desc: string;
  why?: string;          // 完整 why 句（父组件用 t("results.why_prefix") 拼好）
  tags?: string[];
}>();
</script>

<template>
  <div class="card idea-card">
    <div class="idea-no">{{ no }}</div>
    <h3>{{ title }}</h3>
    <p>{{ desc }}</p>
    <div v-if="why" class="why" v-html="why"></div>
    <div class="meta-row"><span v-for="(tg, i) in tags || []" :key="i" class="tag">{{ tg }}</span></div>
    <slot></slot>
  </div>
</template>


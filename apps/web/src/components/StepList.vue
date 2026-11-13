<!-- StepList.vue — B-02/B-08（负责人：B）
     前置 7 步 .steps：序号深色方块 + 富文本步骤（b 标题）。 -->
<script setup lang="ts">
defineProps<{ items: string[] }>();
</script>

<template>
  <ol class="steps">
    <li v-for="(s, i) in items" :key="i"><span v-html="s"></span></li>
  </ol>
</template>

<style scoped>
.steps{list-style:none;counter-reset:s}
.steps li{counter-increment:s;display:flex;gap:12px;padding:9px 0;font-size:13px;color:var(--ink-2)}
.steps li::before{content:counter(s,decimal-leading-zero);flex:0 0 26px;height:26px;border-radius:8px;
  background:var(--deep);color:#fff;display:grid;place-items:center;font-size:10.5px;font-weight:700}
.steps li :deep(b){color:var(--ink)}
</style>

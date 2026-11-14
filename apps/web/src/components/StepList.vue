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


<!-- Tag.vue — B-02（负责人：B）
     标签 .tag（10.5px 圆角胶囊），可选绿色成功态。 -->
<script setup lang="ts">
defineProps<{ green?: boolean }>();
</script>

<template>
  <span class="tag" :class="{ green }"><slot></slot></span>
</template>

<style scoped>
.tag{font-size:10.5px;padding:4px 9px;border-radius:999px;background:var(--bg);border:1px solid var(--line);color:var(--ink-2)}
.tag.green{color:var(--green)}
</style>

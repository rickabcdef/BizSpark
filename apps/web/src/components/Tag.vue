<!-- Tag.vue — B-02（负责人：B）
     标签 .tag（10.5px 圆角胶囊），可选绿色成功态。
     基础样式来自 assets/style.css 的 .tag；仅绿色态用内联色（基线 05/08 屏就是这么写的）。 -->
<script setup lang="ts">
defineProps<{ green?: boolean }>();
</script>

<template>
  <span class="tag" :style="green ? 'color:var(--green)' : ''"><slot></slot></span>
</template>

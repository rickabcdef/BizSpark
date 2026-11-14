<!-- PaperPreview.vue — B-02/B-08（负责人：B）
     一页纸方案纸样 .paper（微倾斜 + 横条纹理）。 -->
<script setup lang="ts">
defineProps<{ title: string }>();
</script>

<template>
  <div class="paper">
    <div class="pt">BizSpark · One-page plan</div>
    <div class="ph">{{ title }}</div>
    <div class="pl"></div><div class="pl"></div><div class="pl s"></div>
    <div class="pbox"></div><div class="pl s" style="margin-top:12px"></div>
  </div>
</template>


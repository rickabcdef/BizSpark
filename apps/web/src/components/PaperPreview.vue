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

<style scoped>
.paper{background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:var(--sh);padding:20px 18px;
  transform:rotate(-1.2deg)}
.paper .pt{font-size:9px;letter-spacing:1.4px;text-transform:uppercase;color:var(--ink-3)}
.paper .ph{font-size:14px;font-weight:750;margin:8px 0 12px;line-height:1.3;color:#101820}
.paper .pl{height:5px;background:#EFEBE3;border-radius:3px;margin:7px 0}
.paper .pl.s{width:62%}
.paper .pbox{height:52px;background:repeating-linear-gradient(0deg,#F4F1EA,#F4F1EA 6px,transparent 6px,transparent 11px);border-radius:6px;margin-top:14px}
</style>

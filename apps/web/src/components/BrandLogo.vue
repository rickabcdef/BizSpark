<!-- BrandLogo.vue — PM 2026-11-28（老板需求）：全站唯一 logo 组件。
     侧边栏 34px / 首页 48px 等比缩放，图标占容器比例（79%）、圆角、描边全部由 size 派生，
     任何位置引用都是"同一张 logo 的大小两号"，杜绝散装内联样式造成的走样。
     图片加载异常时兜底字母 B（界面永不空）。 -->
<script setup lang="ts">
import { ref } from "vue";

defineProps<{ size: number }>();
const broken = ref(false);
</script>

<template>
  <span class="logo-badge" :style="{ '--s': size + 'px' }">
    <img v-if="!broken" src="/buzidea-logo.png" alt="Buzidea" @error="broken = true" />
    <template v-else>B</template>
  </span>
</template>

<style>
.logo-badge{
  --s:34px;
  width:var(--s);height:var(--s);flex:0 0 auto;
  border-radius:calc(var(--s)*0.26);
  background:#fff;
  border:1px solid rgba(0,0,0,.08);
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;
  color:var(--accent);font-weight:900;font-size:calc(var(--s)*0.5);
}
.logo-badge img{
  width:79%;height:79%;
  border-radius:calc(var(--s)*0.18);
  display:block;
}
</style>

<!-- BrandLogo.vue — PM 2026-11-28（老板需求方案三）：全站唯一 logo 组件。
     界面内用白底变体（buzidea-logo-light.png）：深色界面下深蓝原版会融底只剩橙房子，
     白底变体是大厂"深色背景专用版"标准做法（Notion/Slack 同理）。
     图片 100% 满幅铺满容器（饱满度 100%），圆角一层、与桌面图标观感一致，
     hairline 细描边只勾轮廓不占面积，解决深色界面融底问题。
     侧边栏 34px / 首页 48px 等比缩放，任何位置引用都是"同一张 logo 的大小两号"。
     图片加载异常时兜底字母 B（界面永不空）。 -->
<script setup lang="ts">
import { ref } from "vue";

defineProps<{ size: number }>();
const broken = ref(false);
</script>

<template>
  <span class="logo-badge" :style="{ '--s': size + 'px' }">
    <img v-if="!broken" src="/buzidea-logo-light.png" alt="Buzidea" @error="broken = true" />
    <template v-else>B</template>
  </span>
</template>

<style>
.logo-badge{
  --s:34px;
  width:var(--s);height:var(--s);flex:0 0 auto;
  display:flex;align-items:center;justify-content:center;
  color:var(--accent);font-weight:900;font-size:calc(var(--s)*0.5);
}
.logo-badge img{
  width:100%;height:100%;
  border-radius:calc(var(--s)*0.22);
  outline:1px solid rgba(255,255,255,.14);
  outline-offset:-1px;
  display:block;
}
</style>

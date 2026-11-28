<!-- BrandLogo.vue — PM 2026-11-28（老板需求 V2 定稿）：全站唯一 logo 组件。
     界面内用深蓝提亮版（buzidea-logo-blue.png #2B4A80）：原深蓝与界面底色过近会融底，
     白底变体虽高级但品类语言错位（消费级≠商务工具），且品牌灵魂色（深蓝=信任专业）
     在软件内部缺席造成"人格分裂"——V2 深蓝提亮一档：品牌色在场、橙店醒目、
     与桌面图标同族色（只差一档明度），品类对味（Stripe/Shopify 式深底商务语言）。
     图片 100% 满幅铺满容器（饱满度 100%），单层圆角 22%，hairline 贴边细描边勾轮廓。
     白底变体 buzidea-logo-light.png 保留作浅色场景储备。
     侧边栏 34px / 首页 48px 等比缩放，任何位置引用都是"同一张 logo 的大小两号"。
     图片加载异常时兜底字母 B（界面永不空）。 -->
<script setup lang="ts">
import { ref } from "vue";

defineProps<{ size: number }>();
const broken = ref(false);
</script>

<template>
  <span class="logo-badge" :style="{ '--s': size + 'px' }">
    <img v-if="!broken" src="/buzidea-logo-blue.png" alt="Buzidea" @error="broken = true" />
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

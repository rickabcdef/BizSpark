<!-- Icon.vue — POL-01（PM 2026-11-18 界面打磨执行卡）
     全站唯一线性图标集：18×18 viewBox、描边 1.8px、圆角端点、
     fill:none、currentColor 跟随文字色。替代几何符号与 emoji
     （国家选项国旗 emoji 按 D-03 决议第一版保留，不走本组件）。
     用法：<Icon name="home" :size="17" /> -->
<script setup lang="ts">
import { computed } from "vue";

const PATHS: Record<string, string> = {
  /* ---- 侧栏导航 ---- */
  home: '<path d="M2.5 8.2 9 3l6.5 5.2"/><path d="M4.2 7.2V15h9.6V7.2"/>',
  search: '<circle cx="8" cy="8" r="4.6"/><path d="M11.4 11.4 15 15"/>',
  cards: '<rect x="2.5" y="5.5" width="10" height="10" rx="1.8"/><path d="M6 3.2h9.3v9.3"/>',
  doc: '<rect x="4" y="2.5" width="10" height="13" rx="1.6"/><path d="M6.5 6h5M6.5 9h5M6.5 12h3"/>',
  download: '<path d="M9 3v8.6M5.6 8.6 9 12l3.4-3.4"/><path d="M3.5 14.7h11"/>',
  bookmark: '<path d="M5 2.8h8v12.4l-4-3.4-4 3.4z"/>',
  user: '<circle cx="9" cy="6.2" r="2.9"/><path d="M3.6 15.6c.7-2.6 2.9-4 5.4-4s4.7 1.4 5.4 4"/>',
  refresh: '<path d="M14.6 9a5.6 5.6 0 1 1-1.7-4"/><path d="M14.8 3.2v3.6h-3.6"/>',
  gear: '<circle cx="9" cy="9" r="2.6"/><path d="M9 2.6v2M9 13.4v2M2.6 9h2M13.4 9h2M4.4 4.4l1.4 1.4M12.2 12.2l1.4 1.4M13.6 4.4l-1.4 1.4M5.8 12.2l-1.4 1.4"/>',
  /* ---- 问卷：资金档 ---- */
  wallet: '<rect x="2.5" y="4" width="13" height="10.5" rx="2"/><path d="M12.6 9.2h2.9"/><path d="M2.5 6.6h13"/>',
  cash: '<rect x="2" y="4.5" width="14" height="9" rx="1.6"/><circle cx="9" cy="9" r="2.2"/><path d="M4.6 7v4M13.4 7v4"/>',
  card: '<rect x="2" y="4" width="14" height="10.5" rx="2"/><path d="M2 7.6h14"/><path d="M4.6 11.6h4"/>',
  bank: '<path d="M2.5 6.6 9 3l6.5 3.6"/><path d="M4 6.8v6M7.3 6.8v6M10.7 6.8v6M14 6.8v6"/><path d="M2.8 14.8h12.4"/>',
  /* ---- 问卷：时间档 ---- */
  clock: '<circle cx="9" cy="9" r="6.4"/><path d="M9 5.4V9l2.5 1.5"/>',
  clock2: '<circle cx="9" cy="9" r="6.4"/><path d="M9 5v4.2L6.4 11"/>',
  sun: '<circle cx="9" cy="9" r="3.4"/><path d="M9 2v2M9 14v2M2 9h2M14 9h2M4.2 4.2l1.4 1.4M12.4 12.4l1.4 1.4M13.8 4.2l-1.4 1.4M5.6 12.4l-1.4 1.4"/>',
  /* ---- 问卷：资源项 ---- */
  car: '<path d="M3.4 13.4v-2.2l1.5-4.6h8.2l1.5 4.6v2.2"/><path d="M3.4 11.2h11.2"/><circle cx="6" cy="13.6" r="1.1"/><circle cx="12" cy="13.6" r="1.1"/>',
  pot: '<path d="M4.6 8h8.8l-.7 5.6a2.6 2.6 0 0 1-2.6 2.3H7.9a2.6 2.6 0 0 1-2.6-2.3z"/><path d="M2.6 8h12.8"/><path d="M7 5.6c0-.9.9-.9.9-1.8M10.1 5.6c0-.9.9-.9.9-1.8"/>',
  laptop: '<rect x="4" y="4.2" width="10" height="7" rx="1.2"/><path d="M2.4 14.4h13.2"/>',
  palette: '<path d="M9 2.6a6.4 6.4 0 1 0 0 12.8c1.2 0 1.6-.8 1.6-1.5 0-1.7 1.1-2 2.4-2h1.4a1.5 1.5 0 0 0 1.5-1.5A6.4 6.4 0 0 0 9 2.6z"/><path d="M6.2 7h.01M9.4 5.4h.01M12.4 7h.01"/>',
  keyboard: '<rect x="2" y="5.4" width="14" height="7.8" rx="1.6"/><path d="M5 8.2h.01M7.7 8.2h.01M10.4 8.2h.01M13.1 8.2h.01M6 10.6h6"/>',
  door: '<path d="M4.6 15.4V2.8h8.8v12.6"/><path d="M3 15.4h12"/><path d="M11.1 9.4h.01"/>',
  handshake: '<path d="M2.4 9.4 5.4 6.4 9 9.6l3.6-3.2 3 3"/><path d="M5.4 11.4 8 14l1-1 1 1 2.6-2.6"/><path d="M9 9.6 7.4 11.2"/>',
  /* ---- 问卷：风险档 ---- */
  shield: '<path d="M9 2.6 14.4 4.5v4.1c0 3.4-2.2 5.9-5.4 6.8-3.2-.9-5.4-3.4-5.4-6.8V4.5z"/>',
  scale: '<path d="M9 3.6v11.2M4.6 14.8h8.8"/><path d="M9 4.4 4.8 6M9 4.4 13.2 6"/><path d="M2.6 9.8a2.2 2.2 0 0 0 4.4 0L4.8 6z"/><path d="M11 9.8a2.2 2.2 0 0 0 4.4 0L13.2 6z"/>',
  flame: '<path d="M9 2.6c1 3-3.4 4.6-3.4 8a3.4 3.4 0 0 0 6.8 0C12.4 7.2 10.4 6 9 2.6z"/><path d="M9 15.2c-1.2-1.4.4-2.8 0-4.2"/>',
  box: '<rect x="4" y="4" width="10" height="10" rx="2"/>',
  /* ---- 详情卡头 / 说明 / 状态 ---- */
  coin: '<circle cx="9" cy="9" r="6.4"/><path d="M9 5.4v7.2"/><path d="M11.3 6.7c-.6-.8-3.6-1-3.6.6 0 1.9 3.7.8 3.7 2.7 0 1.5-2.9 1.4-3.8.5"/>',
  pin: '<path d="M9 15.4c-2.9-3.3-4.4-5.5-4.4-7.8a4.4 4.4 0 1 1 8.8 0c0 2.3-1.5 4.5-4.4 7.8z"/><circle cx="9" cy="7.5" r="1.6"/>',
  alert: '<path d="M9 2.8 16.2 15H1.8z"/><path d="M9 7.4v3.4"/><path d="M9 13h.01"/>',
  lock: '<rect x="4.4" y="7.8" width="9.2" height="7" rx="1.6"/><path d="M6.4 7.8V6a2.6 2.6 0 0 1 5.2 0v1.8"/>',
  bulb: '<path d="M9 2.4a5 5 0 0 1 2.5 9.3c-.5.3-.8.7-.8 1.2h-3.4c0-.5-.3-.9-.8-1.2A5 5 0 0 1 9 2.4z"/><path d="M7.4 15.4h3.2"/>',
  check: '<path d="M3.4 9.6 7.4 13.4 14.6 5.4"/>',
  "check-circle": '<circle cx="9" cy="9" r="6.6"/><path d="m6.4 9.2 1.8 1.8 3.4-3.6"/>',
  /* ---- 原型补齐：终端 / 文件 / 操作 ---- */
  monitor: '<rect x="2.5" y="3.5" width="13" height="9" rx="1.5"/><path d="M6 15.5h6M9 12.5v3"/>',
  folder: '<path d="M3 5.5h4l1.5 1.8h6.5a1 1 0 0 1 1 1v5.7a1 1 0 0 1-1 1H3z"/><path d="M3 5.5v8.7a1 1 0 0 0 1 1h12"/>',
  chevron: '<path d="M6.5 4.5 11 9l-4.5 4.5"/>',
  close: '<path d="M5 5l8 8M13 5l-8 8"/>',
  help: '<circle cx="9" cy="9" r="6.2"/><path d="M9 6.4v.2M6.8 7.9c.2-1.3 1.2-2 2.2-2 1.1 0 2 .7 2.2 1.8.3 1.6-1.6 2-1.6 3.6"/>',
  star: '<path d="M9 3l1.7 3.5 3.8.6-2.7 2.7.6 3.8L9 11.7 5.6 13.6l.6-3.8L3.5 7.1l3.8-.6z"/>',
};

const props = defineProps<{ name: string; size?: number }>();
const markup = computed(() => PATHS[props.name] || "");
</script>

<template>
  <svg class="ic" :width="size || 18" :height="size || 18" viewBox="0 0 18 18" fill="none"
    stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true" v-html="markup"></svg>
</template>

<style scoped>
.ic{display:inline-block;vertical-align:-0.15em;flex:0 0 auto}
</style>

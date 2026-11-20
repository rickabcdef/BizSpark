<!-- OptionCard.vue — 对齐最新版原型选项卡 .option
     图标（iconName 线性 SVG 优先；icon 仅剩第 1 题国旗 emoji）+ 标题 + 解释 + 右箭头。
     单选/多选共用；selected 高亮橘边橘底。props / emit 与原契约保持不变。 -->
<script setup lang="ts">
import Icon from "./Icon.vue";
defineProps<{ icon?: string; iconName?: string; title: string; desc?: string; selected?: boolean; radio?: boolean }>();
defineEmits<{ (e: "pick"): void }>();
</script>

<template>
  <button class="option" :class="{ sel: selected }" type="button" @click="$emit('pick')">
    <span v-if="iconName" class="opt-ico"><Icon :name="iconName" :size="20" /></span>
    <span v-else-if="icon" class="opt-ico">{{ icon }}</span>
    <div class="opt-text">
      <div class="opt-title">{{ title }}</div>
      <div v-if="desc" class="opt-sub">{{ desc }}</div>
    </div>
    <span class="opt-chevron"><Icon name="chevron" :size="18" /></span>
  </button>
</template>

<!-- OptionCard.vue — B-02/B-06（负责人：B）
     问卷选项大卡 .opt：radio + 图标 + 标题 + 一行解释。
     单选/多选共用；selected 高亮橘边橘底。
     【POL-03】图标二选一：iconName（线性 SVG，走 Icon.vue）优先；
     icon（emoji 字符串）仅剩第 1 题六国国旗（D-03 决议：第一版保留）。
     样式全部来自 assets/style.css（.opt/.radio/.em/.ot/.od）。 -->
<script setup lang="ts">
import Icon from "./Icon.vue";
defineProps<{ icon?: string; iconName?: string; title: string; desc?: string; selected?: boolean; radio?: boolean }>();
defineEmits<{ (e: "pick"): void }>();
</script>

<template>
  <button class="opt" :class="{ sel: selected }" type="button" @click="$emit('pick')">
    <span v-if="radio !== false" class="radio"></span>
    <span v-if="iconName" class="em"><Icon :name="iconName" :size="18" /></span>
    <span v-else-if="icon" class="em">{{ icon }}</span>
    <span style="display:flex;flex-direction:column">
      <span class="ot">{{ title }}</span>
      <span v-if="desc" class="od">{{ desc }}</span>
    </span>
  </button>
</template>

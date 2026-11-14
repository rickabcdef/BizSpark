<!-- OptionCard.vue — B-02/B-06（负责人：B）
     问卷选项大卡 .opt：radio + emoji + 标题 + 一行解释。
     单选/多选共用；selected 高亮橘边橘底。
     样式全部来自 assets/style.css（.opt/.radio/.em/.ot/.od），这里不再另写一份。 -->
<script setup lang="ts">
defineProps<{ icon?: string; title: string; desc?: string; selected?: boolean; radio?: boolean }>();
defineEmits<{ (e: "pick"): void }>();
</script>

<template>
  <button class="opt" :class="{ sel: selected }" type="button" @click="$emit('pick')">
    <span v-if="radio !== false" class="radio"></span>
    <span v-if="icon" class="em">{{ icon }}</span>
    <span style="display:flex;flex-direction:column">
      <span class="ot">{{ title }}</span>
      <span v-if="desc" class="od">{{ desc }}</span>
    </span>
  </button>
</template>

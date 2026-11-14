<!-- Toggle.vue — B-02/B-09（负责人：B）
     设置开关 .toggle（40×23 圆角，on 绿色）。 -->
<script setup lang="ts">
const props = defineProps<{ on?: boolean }>();
const emit = defineEmits<{ (e: "update:on", v: boolean): void }>();
function flip() {
  emit("update:on", !props.on);
}
</script>

<template>
  <button class="toggle" :class="{ on: props.on }" type="button" role="switch"
    :aria-checked="props.on ? 'true' : 'false'" @click="flip"></button>
</template>


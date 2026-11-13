<!-- OptionCard.vue — B-02/B-06（负责人：B）
     问卷选项大卡 .opt：radio + emoji + 标题 + 一行解释。
     单选/多选共用；selected 高亮橘边橘底。 -->
<script setup lang="ts">
defineProps<{ icon?: string; title: string; desc?: string; selected?: boolean; radio?: boolean }>();
defineEmits<{ (e: "pick"): void }>();
</script>

<template>
  <button class="opt" :class="{ sel: selected }" type="button" @click="$emit('pick')">
    <span class="radio" :class="{ hide: radio === false }"></span>
    <span v-if="icon" class="em">{{ icon }}</span>
    <span class="txt"><span class="ot">{{ title }}</span><span v-if="desc" class="od">{{ desc }}</span></span>
  </button>
</template>

<style scoped>
.opt{display:flex;align-items:center;gap:14px;padding:15px 17px;border:1.5px solid var(--line);
  border-radius:var(--r-md);background:var(--surface-2);transition:.16s;text-align:left;width:100%}
.opt:hover{border-color:#CFC6B7;transform:translateY(-1px);box-shadow:var(--sh-sm)}
.opt.sel{border-color:var(--accent);background:var(--accent-soft)}
.radio{width:19px;height:19px;border-radius:50%;border:1.5px solid #C9C3B8;flex:0 0 19px;position:relative}
.radio.hide{display:none}
.opt.sel .radio{border-color:var(--accent);background:var(--accent)}
.opt.sel .radio::after{content:"";position:absolute;inset:5px;border-radius:50%;background:#fff}
.opt .em{font-size:18px;width:26px;text-align:center}
.opt .txt{display:flex;flex-direction:column}
.ot{font-size:14px;font-weight:620}
.od{font-size:11.5px;color:var(--ink-2);margin-top:2px}
</style>

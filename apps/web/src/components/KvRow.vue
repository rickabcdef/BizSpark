<!-- KvRow.vue — B-02/B-08（负责人：B）
     键值行 .kv：左键右值（值可高亮 accent）。 -->
<script setup lang="ts">
defineProps<{ k: string; v: string; accent?: boolean; boldKey?: boolean }>();
</script>

<template>
  <div class="kv">
    <span><b v-if="boldKey">{{ k }}</b><template v-else>{{ k }}</template></span>
    <b :style="accent ? 'color:var(--accent)' : ''">{{ v }}</b>
  </div>
</template>

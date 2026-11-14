<!-- Welcome.vue — B-03（负责人：B）
     对应 en/html/01-welcome.html：全屏 hero（无 AppShell）。
     AL-B2：右上角只留只读版本标记 hero-meta（基线已删 3 个假菜单）。
     AL-B4：两个主按钮是真实链接（router-link → #/quiz、#/saved）。
     B-13：hero-trust / hero-foot 两个价格槽。 -->
<script setup lang="ts">
import { onMounted } from "vue";
import { t } from "../i18n";
import { renderPriceSlots } from "../bridge/price";

onMounted(renderPriceSlots);
</script>

<template>
  <div class="hero">
    <div class="orb a"></div><div class="orb b"></div>
    <div class="hero-top">
      <div class="brand"><div class="brand-mark">B</div><div>BizSpark<small>{{ t("brand.tag") }}</small></div></div>
      <div class="hero-meta">v1.0.0</div>
    </div>
    <div class="hero-body"><div class="hero-in">
      <div class="eyebrow">{{ t("welcome.eyebrow") }}</div>
      <h1 v-html="t('welcome.h1')"></h1>
      <p>{{ t("welcome.lead") }}</p>
      <div class="btn-row">
        <router-link class="btn btn-primary btn-lg" to="/quiz">{{ t("welcome.cta_start") }}&nbsp;→</router-link>
        <router-link class="btn btn-quiet btn-lg" to="/saved">{{ t("welcome.cta_saved") }}</router-link>
      </div>
      <div class="hero-price">
        <div data-price-slot="hero-trust"></div>
        <div>✓ {{ t("welcome.offline") }}</div><div>✓ {{ t("welcome.never_leave") }}</div>
      </div>
    </div></div>
    <div class="hero-mock"><div class="card">
      <div class="tiny" style="letter-spacing:1.4px;text-transform:uppercase">{{ t("welcome.mock_cap") }}</div>
      <div class="idea-card" style="border:0;box-shadow:none;padding:16px 0 0">
        <div class="idea-no">01 / 03 &nbsp;·&nbsp; 94% {{ t("common.match") }}</div>
        <h3>{{ t("welcome.mock_title") }}</h3>
        <p>{{ t("welcome.mock_desc") }}</p>
        <div class="meta-row"><span class="tag">{{ t("welcome.mock_tag1") }}</span><span class="tag">{{ t("welcome.mock_tag2") }}</span><span class="tag">{{ t("welcome.mock_tag3") }}</span></div>
      </div>
    </div></div>
    <div class="hero-foot"><span>{{ t("welcome.foot") }}</span><span data-price-slot="hero-foot"></span></div>
  </div>
</template>

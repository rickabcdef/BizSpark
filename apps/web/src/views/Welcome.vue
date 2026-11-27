<!-- Welcome.vue — 对齐最新版原型 01-welcome。
     脚本（renderPriceSlots 价格槽、isEn 语言判断）全部保留。
     基线：深色品牌 hero；顶栏品牌徽标 + 版本；眉题 / 标题 / 两段共情 / 斜体 hook；
     主次按钮；两条信任胶囊；样例白卡（插画 + 三条要点 + 三标签）；注脚。 -->
<script setup lang="ts">
import { computed, onMounted } from "vue";
import { locale, t } from "../i18n";
import { renderPriceSlots } from "../bridge/price";
import AppShell from "../components/AppShell.vue";
import Icon from "../components/Icon.vue";

onMounted(renderPriceSlots);

const isEn = computed(() => locale() === "en-US");
void isEn;
</script>

<template>
  <AppShell page-class="hero">
    <div class="content">
      <div class="topbar">
        <div class="brand">
          <div class="brand-badge">
            <img src="/buzidea-logo.png" alt="Buzidea" style="width:27px;height:27px;border-radius:6px;display:block" />
          </div>
          <div>
            <div class="brand-name">Buzidea</div>
            <div class="brand-sub">{{ t("brand.tag") }}</div>
          </div>
        </div>
        <div class="version">v1.0.0</div>
      </div>

      <div class="hero-eyebrow">{{ t("welcome.eyebrow") }}</div>
      <h1 v-html="t('welcome.h1')"></h1>
      <p class="body">{{ t("welcome.empathy1") }}</p>
      <p class="body">{{ t("welcome.empathy2") }}</p>
      <div class="hook">{{ t("welcome.hook") }}</div>

      <div class="hero-actions">
        <router-link class="btn btn-primary" to="/quiz">{{ t("welcome.cta_start") }}&nbsp;→</router-link>
        <router-link class="btn btn-secondary" style="margin-top:12px" to="/saved">{{ t("welcome.cta_saved") }}</router-link>
      </div>

      <div class="trust">
        <span class="item"><span class="ico"><Icon name="check-circle" :size="18" /></span>{{ t("welcome.offline") }}</span>
        <span class="item"><span class="ico"><Icon name="check-circle" :size="18" /></span>{{ t("welcome.never_leave") }}</span>
      </div>

      <div class="hero-card">
        <div class="hc-top">
          <div class="hc-illu" aria-hidden="true">
            <svg viewBox="0 0 160 130" width="100%" fill="none" stroke="#56616E" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 55 L80 30 L140 55"/><path d="M28 55 h104 v55 H28 z"/>
              <path d="M28 55 q13 12 26 0 q13 12 26 0 q13 12 26 0 q13 12 26 0"/>
              <rect x="62" y="78" width="36" height="32"/><path d="M70 70 h20"/>
              <path d="M12 110 h16 M132 110 h16"/><path d="M18 110 v-14 M138 110 v-14"/>
              <rect x="112" y="66" width="18" height="14" rx="2"/>
            </svg>
          </div>
          <div class="hc-list">
            <div class="li"><span class="ico"><Icon name="clock" :size="20" /></span>{{ t("welcome.li1") }}</div>
            <div class="li"><span class="ico"><Icon name="star" :size="20" /></span>{{ t("welcome.li2") }}</div>
            <div class="li"><span class="ico"><Icon name="flame" :size="20" /></span>{{ t("welcome.li3") }}</div>
          </div>
        </div>
        <div class="tags">
          <span class="tag accent">{{ t("welcome.mock_tag1") }}</span>
          <span class="tag accent">{{ t("welcome.mock_tag2") }}</span>
          <span class="tag accent">{{ t("welcome.mock_tag3") }}</span>
        </div>
      </div>

      <div class="footer-note">{{ t("welcome.foot") }}</div>
    </div>
  </AppShell>
</template>

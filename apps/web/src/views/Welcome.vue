<!-- Welcome.vue — B-03（负责人：B）
     对应 en/html/01-welcome.html：全屏 hero（无 AppShell）。
     AL-B2：右上角只留只读版本标记 hero-meta（基线已删 3 个假菜单）。
     AL-B4：两个主按钮是真实链接（router-link → #/quiz、#/saved）。
     B-13：hero-trust / hero-foot 两个价格槽。
     【PM 2026-11-17】首页两栏版式（工单 V1.0 §1 栅格契约）：
       左栏 .hero-in 720px 撑满、h1 72px、左列正文 18px/560px；
       右栏 .hero-note 定稿 founder note（420px，right 132 / top 196）；
       白框 .hero-mock 归右下（right 132 / top 76%，保留原 transform）。
       栅格值全部内联，不改 assets/style.css。 -->
<script setup lang="ts">
import { computed, onMounted } from "vue";
import { locale, t } from "../i18n";
import { renderPriceSlots } from "../bridge/price";

onMounted(renderPriceSlots);

// 工单 §3 第 1 处：英文首句 34px → 30px 一行（white-space:nowrap 保留）
const noteTitleStyle = computed(() => ({
  fontSize: locale() === "en-US" ? "30px" : "34px",
}));
</script>

<template>
  <div class="hero">
    <div class="orb a"></div><div class="orb b"></div>
    <div class="hero-top">
      <div class="brand"><div class="brand-mark">B</div><div>BizSpark<small>{{ t("brand.tag") }}</small></div></div>
      <div class="hero-meta">v1.0.0</div>
    </div>
    <div class="hero-body"><div class="hero-in" style="width:720px;max-width:none">
      <div class="eyebrow">{{ t("welcome.eyebrow") }}</div>
      <h1 v-html="t('welcome.h1')" style="font-size:72px;letter-spacing:-3.4px"></h1>
      <p style="max-width:560px;font-size:18px">{{ t("welcome.lead") }}</p>
      <div class="btn-row">
        <router-link class="btn btn-primary btn-lg" to="/quiz">{{ t("welcome.cta_start") }}&nbsp;→</router-link>
        <router-link class="btn btn-quiet btn-lg" to="/saved">{{ t("welcome.cta_saved") }}</router-link>
      </div>
      <div class="hero-price">
        <div data-price-slot="hero-trust"></div>
        <div>✓ {{ t("welcome.offline") }}</div><div>✓ {{ t("welcome.never_leave") }}</div>
      </div>
    </div></div>
    <!-- 右栏定稿 founder note（工单 §2 第 5 条 / §3 片段，逐字照贴） -->
    <div class="hero-note" style="position:absolute;right:132px;top:196px;width:420px;z-index:2">
      <div style="font-size:10.5px;letter-spacing:3.6px;color:#F2653A;font-weight:750;margin-bottom:10px"
        v-html="t('welcome.note_kicker')"></div>
      <div :style="noteTitleStyle"
        style="line-height:1.2;font-weight:800;letter-spacing:-1.4px;color:#fff;white-space:nowrap">{{ t("welcome.note_title") }}<span style="color:#F2653A">{{ t("welcome.note_period") }}</span></div>
      <div style="border-left:2px solid rgba(242,101,58,.6);padding-left:12px;margin:8px 0 12px;font-size:13px;line-height:1.7;color:#9FB2C2">{{ t("welcome.note_quote") }}</div>
      <div style="font-size:14px;line-height:1.72;color:#D6E2EC">{{ t("welcome.note_p1_a") }}<br><span style="display:inline-block;margin-left:28px">{{ t("welcome.note_p1_b") }}</span></div>
      <div style="font-size:14px;line-height:1.72;color:#D6E2EC;margin-top:6px">{{ t("welcome.note_p2_a") }}<br><span style="font-size:21px;font-weight:800;color:#fff;letter-spacing:-.3px">{{ t("welcome.note_p2_kw1") }}</span>{{ t("welcome.note_p2_sep1") }}<span style="color:#F2653A;font-weight:700">{{ t("welcome.note_p2_kw2") }}</span>{{ t("welcome.note_p2_sep2") }}<br><span style="display:inline-block;margin-left:28px">{{ t("welcome.note_p2_b") }}</span></div>
      <div style="font-size:14px;line-height:1.72;color:#D6E2EC;margin-top:6px">{{ t("welcome.note_p3_a") }}<span
          style="font-size:21px;font-weight:800;color:#fff;letter-spacing:-.3px">{{ t("welcome.note_p3_kw") }}</span>{{ t("welcome.note_p3_sep") }}<br><span style="display:inline-block;margin-left:28px">{{ t("welcome.note_p3_b") }}</span></div>
      <div style="text-align:right;margin-top:10px;font-size:13.5px;font-style:italic;color:#F2653A;letter-spacing:.6px">{{ t("welcome.note_sign") }}</div>
    </div>
    <div class="hero-mock" style="right:132px;top:76%"><div class="card">
      <div class="tiny" style="letter-spacing:1.4px;text-transform:uppercase">{{ t("welcome.mock_cap") }}</div>
      <div class="idea-card" style="border:0;box-shadow:none;padding:16px 0 0">
        <div class="idea-no">01 / 03</div>
        <h3>{{ t("welcome.mock_title") }}</h3>
        <p>{{ t("welcome.mock_desc") }}</p>
        <div class="meta-row"><span class="tag">{{ t("welcome.mock_tag1") }}</span><span class="tag">{{ t("welcome.mock_tag2") }}</span><span class="tag">{{ t("welcome.mock_tag3") }}</span></div>
      </div>
    </div></div>
    <div class="hero-foot"><span>{{ t("welcome.foot") }}</span><span data-price-slot="hero-foot"></span></div>
  </div>
</template>

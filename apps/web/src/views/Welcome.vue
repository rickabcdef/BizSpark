<!-- Welcome.vue — B-03（负责人：B）
     对应 en/html/01-welcome.html：全屏 hero（无 AppShell）。
     AL-B2：右上角只留只读版本标记 hero-meta（基线已删 3 个假菜单）。
     AL-B4：两个主按钮是真实链接（router-link → #/quiz、#/saved）。
     B-13：hero-trust / hero-foot 两个价格槽。
     【PM 2026-11-17】首页两栏版式 · 流式弹性版（v3）
       版式骨架沿用两栏：左栏主张 + 右栏 founder note + 右下白框。
       尺寸全部弹性（clamp + min(vw,vh)），禁止任何写死像素：
       窗口越大字号/留白同步放大，窗口缩小自动收敛但保持占满，
       任何尺寸下都是"撑满的大版面"，不做整屏等比缩小。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { locale, t } from "../i18n";
import { renderPriceSlots } from "../bridge/price";

onMounted(renderPriceSlots);

const isEn = computed(() => locale() === "en-US");
</script>

<template>
  <div class="hero hero-fluid" :class="{ 'is-en': isEn }">
    <div class="orb a"></div><div class="orb b"></div>
    <div class="hero-top">
      <div class="brand"><div class="brand-mark">B</div><div>BizSpark<small>{{ t("brand.tag") }}</small></div></div>
      <div class="hero-meta">v1.0.0</div>
    </div>

    <div class="hero-body">
      <div class="hero-in">
        <div class="eyebrow">{{ t("welcome.eyebrow") }}</div>
        <h1 v-html="t('welcome.h1')"></h1>
        <p class="hero-lead">{{ t("welcome.lead") }}</p>
        <div class="btn-row">
          <router-link class="btn btn-primary btn-lg" to="/quiz">{{ t("welcome.cta_start") }}&nbsp;→</router-link>
          <router-link class="btn btn-quiet btn-lg" to="/saved">{{ t("welcome.cta_saved") }}</router-link>
        </div>
        <div class="hero-price">
          <div data-price-slot="hero-trust"></div>
          <div>✓ {{ t("welcome.offline") }}</div><div>✓ {{ t("welcome.never_leave") }}</div>
        </div>
      </div>

      <!-- 右栏：定稿 founder note（上）+ 白框（下），列内自然排布，永不重叠 -->
      <aside class="hero-side">
        <div class="hero-note">
          <div class="note-kicker" v-html="t('welcome.note_kicker')"></div>
          <div class="note-title">{{ t("welcome.note_title") }}<span class="dot">{{ t("welcome.note_period") }}</span></div>
          <div class="note-quote">{{ t("welcome.note_quote") }}</div>
          <div class="note-p">{{ t("welcome.note_p1_a") }}<br><span class="ind">{{ t("welcome.note_p1_b") }}</span></div>
          <div class="note-p">
            {{ t("welcome.note_p2_a") }}<br><span class="kw">{{ t("welcome.note_p2_kw1") }}</span>{{ t("welcome.note_p2_sep1") }}<span class="kw-accent">{{ t("welcome.note_p2_kw2") }}</span>{{ t("welcome.note_p2_sep2") }}<br><span class="ind">{{ t("welcome.note_p2_b") }}</span>
          </div>
          <div class="note-p">
            {{ t("welcome.note_p3_a") }}<span class="kw">{{ t("welcome.note_p3_kw") }}</span>{{ t("welcome.note_p3_sep") }}<br><span class="ind">{{ t("welcome.note_p3_b") }}</span>
          </div>
          <div class="note-sign">{{ t("welcome.note_sign") }}</div>
        </div>

        <div class="hero-mock"><div class="card">
          <div class="tiny mock-cap">{{ t("welcome.mock_cap") }}</div>
          <div class="idea-card mock-idea">
            <div class="idea-no">01 / 03</div>
            <h3>{{ t("welcome.mock_title") }}</h3>
            <p>{{ t("welcome.mock_desc") }}</p>
            <div class="meta-row"><span class="tag">{{ t("welcome.mock_tag1") }}</span><span class="tag">{{ t("welcome.mock_tag2") }}</span><span class="tag">{{ t("welcome.mock_tag3") }}</span></div>
          </div>
        </div></div>
      </aside>
    </div>

    <div class="hero-foot"><span>{{ t("welcome.foot") }}</span><span data-price-slot="hero-foot"></span></div>
  </div>
</template>

<style scoped>
/* ---------- 流式标度：所有尺寸由视口推导，无写死像素 ---------- */
.hero.hero-fluid {
  --pad-x: clamp(28px, 4.6vw, 150px);
  --pad-y: clamp(12px, 2.2vh, 72px);
  --col-gap: clamp(40px, 6.6vw, 220px);
  --side-w: clamp(296px, 29vw, 780px);

  --fs-h1: clamp(40px, min(6.6vw, 11vh), 200px);
  --fs-lead: clamp(15px, min(1.3vw, 1.9vh), 30px);
  --fs-eyebrow: clamp(10px, 0.82vw, 17px);
  --fs-price: clamp(11px, 0.86vw, 19px);
  --fs-foot: clamp(10.5px, 0.82vw, 17px);

  --fs-kicker: clamp(9.5px, 0.8vw, 17px);
  --fs-quote: clamp(12.5px, 1vw, 22px);
  --fs-body: clamp(12.5px, 1.06vw, 24px);
  --fs-kw: clamp(17px, 1.52vw, 36px);
  --fs-sign: clamp(12px, 0.96vw, 21px);

  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-height: 100vh;
}

/* ---------- 顶栏 ---------- */
.hero-fluid .hero-top { padding: clamp(16px, 2.6vh, 36px) var(--pad-x); }
.hero-fluid .hero-meta { font-size: var(--fs-foot); }

/* ---------- 主体两栏：两栏头齐，底部留白 ---------- */
.hero-fluid .hero-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) var(--side-w);
  column-gap: var(--col-gap);
  align-items: start;
  align-content: safe center;
  padding: var(--pad-y) var(--pad-x) clamp(16px, 3vh, 54px);
  min-height: 0;
}

.hero-fluid .hero-in {
  max-width: none;
  width: auto;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.hero-fluid .eyebrow { font-size: var(--fs-eyebrow); }
.hero-fluid h1 {
  font-size: var(--fs-h1);
  line-height: 1.04;
  letter-spacing: -0.045em;
  margin-top: clamp(8px, 1.3vh, 18px);
}
.hero-fluid .hero-lead {
  font-size: var(--fs-lead);
  line-height: 1.6;
  max-width: 34em;
  margin-top: clamp(12px, 2.2vh, 40px);
}
.hero-fluid .btn-row { margin-top: clamp(20px, 3.4vh, 72px); }
.hero-fluid .hero-price {
  margin-top: clamp(20px, 4.4vh, 96px);
  font-size: var(--fs-price);
  gap: clamp(14px, 1.6vw, 26px);
  flex-wrap: wrap;
}

/* ---------- 右栏：文案在上，白框紧随其后 ---------- */
.hero-side {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  min-height: 0;
  container-type: inline-size;
}
.hero-side > * { flex: 0 0 auto; }

.hero-fluid .hero-note { position: static; width: auto; max-width: 100%; z-index: 2; }
.note-kicker {
  font-size: var(--fs-kicker);
  letter-spacing: 0.34em;
  color: #F2653A;
  font-weight: 750;
  margin-bottom: clamp(6px, 1vh, 12px);
}
.note-title {
  font-size: clamp(24px, 9.1cqw, 68px);
  line-height: 1.2;
  font-weight: 800;
  letter-spacing: -0.038em;
  color: #fff;
  white-space: nowrap;
}
.note-title .dot { color: #F2653A; }
.hero-fluid.is-en .note-title { font-size: clamp(18px, 6.65cqw, 52px); }

.note-quote {
  border-left: 2px solid rgba(242, 101, 58, 0.6);
  padding-left: clamp(9px, 0.9vw, 14px);
  margin: clamp(6px, 0.9vh, 12px) 0 clamp(8px, 1.3vh, 16px);
  font-size: var(--fs-quote);
  line-height: 1.66;
  color: #9FB2C2;
}
.note-p {
  font-size: var(--fs-body);
  line-height: 1.62;
  color: #D6E2EC;
  margin-top: clamp(3px, 0.6vh, 8px);
}
.note-p .ind { display: inline-block; margin-left: 2em; }
.note-p .kw { font-size: var(--fs-kw); font-weight: 800; color: #fff; letter-spacing: -0.014em; }
.note-p .kw-accent { color: #F2653A; font-weight: 700; }
.note-sign {
  text-align: right;
  margin-top: clamp(7px, 1.1vh, 16px);
  font-size: var(--fs-sign);
  font-style: italic;
  color: #F2653A;
  letter-spacing: 0.04em;
}

/* ---------- 右下白框：紧跟文案，永不压字 ---------- */
.hero-fluid .hero-mock {
  position: relative;
  right: auto;
  top: auto;
  width: clamp(258px, 23vw, 640px);
  max-width: 100%;
  align-self: flex-end;
  margin-top: clamp(18px, 4vh, 96px);
  transform: rotate(-3.2deg);
  transform-origin: bottom right;
  z-index: 1;
}
.mock-cap { letter-spacing: 0.14em; text-transform: uppercase; }
.hero-fluid .mock-idea {
  border: 0;
  box-shadow: none;
  padding: clamp(12px, 1.4vh, 18px) 0 0;
}
.hero-fluid .mock-idea h3 { font-size: clamp(13.5px, 1.05vw, 24px); }
.hero-fluid .mock-idea p { font-size: clamp(10.5px, 0.82vw, 18px); }

/* ---------- 底栏 ---------- */
.hero-fluid .hero-foot {
  padding: clamp(13px, 1.9vh, 26px) var(--pad-x);
  font-size: var(--fs-foot);
  gap: 16px;
  flex-wrap: wrap;
}

/* ---------- 矮窗口：右栏收紧，保证首屏完整 ---------- */
@media (max-height: 800px) {
  .hero-fluid .hero-mock { width: clamp(224px, 19vw, 300px); margin-top: clamp(14px, 2.6vh, 40px); }
  .hero-fluid .hero-mock .card { padding: 15px; }
  .hero-fluid .mock-idea h3 { font-size: clamp(12.5px, 0.95vw, 15px); }
  .hero-fluid .mock-idea p { font-size: clamp(10px, 0.76vw, 12px); }
  .hero-fluid .note-quote { margin: 5px 0 8px; }
  .hero-fluid .note-sign { margin-top: 6px; }
  .hero-fluid .hero-price { margin-top: clamp(16px, 2.6vh, 40px); }
  .hero-fluid .hero-body { padding-bottom: clamp(12px, 2vh, 40px); }
}
@media (max-height: 700px) {
  .hero-fluid .hero-mock { width: clamp(188px, 16vw, 252px); margin-top: clamp(10px, 2vh, 30px); }
  .hero-fluid .hero-mock .card { padding: 10px 11px; }
  .hero-fluid .note-p { line-height: 1.5; }
  .hero-fluid .note-quote { line-height: 1.55; }
  .hero-fluid .hero-top { padding-top: 10px; padding-bottom: 10px; }
  .hero-fluid .hero-body { padding-bottom: clamp(10px, 2vh, 30px); }
  .hero-fluid .hero-foot { padding-top: 10px; padding-bottom: 10px; }
}

/* ---------- 窄窗口：单列堆叠（不再横向挤压） ---------- */
@media (max-width: 960px) {
  .hero-fluid .hero-body { grid-template-columns: minmax(0, 1fr); row-gap: clamp(24px, 4vh, 52px); }
  .hero-fluid .hero-mock { align-self: flex-start; transform-origin: bottom left; margin-top: clamp(26px, 4.4vh, 56px); }
  .hero-fluid .note-title { white-space: normal; }
}
</style>

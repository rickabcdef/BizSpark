<!-- Welcome.vue — B-03（负责人：B）
     对应 en/html/01-welcome.html：全屏 hero（无 AppShell）。
     AL-B2：右上角只留只读版本标记 hero-meta（基线已删 3 个假菜单）。
     AL-B4：两个主按钮是真实链接（router-link → #/quiz、#/saved）。
     B-13：价格槽只剩 hero-trust；hero-foot 槽已按 PM 2026-11-17 决定整段移除
     （右下「Microsoft Store · Mac App Store · 一次买断」不再展示，locales 的
     price.hero_foot_* 键按"不增删键"铁律保留在库，price.ts 的槽位渲染逻辑不动）。
     【PM 2026-11-17】首页两栏版式 · 流式弹性版（v3）
       版式骨架沿用两栏：左栏主张 + 右栏 founder note + 右下白框。
       尺寸全部弹性（clamp + min(vw,vh)），禁止任何写死像素：
       窗口越大字号/留白同步放大，窗口缩小自动收敛但保持占满，
       任何尺寸下都是"撑满的大版面"，不做整屏等比缩小。 -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { locale, t } from "../i18n";
import { renderPriceSlots } from "../bridge/price";
import Icon from "../components/Icon.vue";

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
        <!-- 【POL-02】两段共情文字（定稿图左栏正文）；welcome.lead 键语义保留在语言包不渲染 -->
        <p class="hero-empathy">{{ t("welcome.empathy1") }}</p>
        <p class="hero-empathy">{{ t("welcome.empathy2") }}</p>
        <div class="btn-row">
          <router-link class="btn btn-primary btn-lg" to="/quiz">{{ t("welcome.cta_start") }}&nbsp;→</router-link>
          <router-link class="btn btn-quiet btn-lg" to="/saved">{{ t("welcome.cta_saved") }}</router-link>
        </div>
        <div class="hero-price">
          <div data-price-slot="hero-trust"></div>
          <div><Icon name="check" :size="14" /> {{ t("welcome.offline") }}</div>
          <div><Icon name="check" :size="14" /> {{ t("welcome.never_leave") }}</div>
        </div>
      </div>

      <!-- 【POL-02】右栏：白卡上方一句 hook（定稿图右上角斜体橙句）+ 一张白卡；
           原 founder note 长段自述从模板移除（welcome.note_* 键保留在语言包不删） -->
      <aside class="hero-side">
        <div class="hero-hook">{{ t("welcome.hook") }}</div>

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

    <div class="hero-foot"><span>{{ t("welcome.foot") }}</span></div>
  </div>
</template>

<style scoped>
/* ---------- 流式标度：所有尺寸由视口推导，无写死像素 ---------- */
.hero.hero-fluid {
  --pad-x: clamp(28px, 4.6vw, 150px);
  --pad-y: clamp(12px, 1.9vh, 62px);
  --col-gap: clamp(40px, 6.6vw, 220px);
  --side-w: clamp(296px, 29vw, 780px);

  --fs-h1: clamp(40px, min(6.6vw, 11vh), 200px);
  --fs-lead: clamp(15px, min(1.3vw, 1.9vh), 30px);
  --fs-eyebrow: clamp(10px, 0.82vw, 17px);
  --fs-price: clamp(11px, 0.86vw, 19px);
  --fs-foot: clamp(10.5px, 0.82vw, 17px);

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
  padding: var(--pad-y) var(--pad-x) clamp(12px, 2.1vh, 40px);
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
.hero-fluid .hero-empathy {
  font-size: var(--fs-lead);
  line-height: 1.6;
  max-width: 34em;
  margin-top: clamp(10px, 1.7vh, 30px);
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
.hero-side > .hero-hook { flex: 0 0 auto; }
/* 白卡吃掉右栏剩余高度 → 整栏一块大面板，而不是右下角一张小纸片 */
.hero-side > .hero-mock { flex: 1 1 auto; min-height: 0; display: flex; }

/* 【POL-02】右栏 hook：斜体橙句，右对齐（定稿图右上角），随右栏宽度伸缩 */
.hero-fluid .hero-hook {
  align-self: flex-end;
  text-align: right;
  font-style: italic;
  font-weight: 700;
  font-size: clamp(13px, 1.15vw, 26px);
  letter-spacing: 0.02em;
  color: var(--accent);
  z-index: 2;
  text-shadow: 0 2px 14px rgba(4, 16, 34, 0.4);
}

/* 【POL-02】左栏两段共情文字（定稿图口吻） */
.hero-fluid .hero-empathy { color: #C4D3E0; }
.hero-fluid .hero-empathy + .hero-empathy { margin-top: clamp(6px, 1.1vh, 20px); }

/* ---------- 右下白卡：撑满右栏的整栏大卡（cqw 随右栏宽度伸缩） ---------- */
.hero-fluid .hero-mock {
  position: relative;
  right: auto;
  top: auto;
  /* 向右咬进页面边距一点（padding 内有余量），让卡片"顶"出去，视觉更有气势 */
  width: calc(100% + clamp(0px, 1.5vw, 32px));
  max-width: none;
  margin-right: calc(-1 * clamp(0px, 1.5vw, 32px));
  align-self: stretch;
  margin-top: clamp(14px, 2.1vh, 56px);
  transform: rotate(-2.2deg);
  transform-origin: bottom right;
  z-index: 1;
}
/* 卡本体：大内边距 + 大圆角 + 厚投影，撑起整栏的分量 */
.hero-fluid .hero-mock .card {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: clamp(15px, 4.8cqw, 44px);
  border-radius: clamp(12px, 3.2cqw, 30px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    0 clamp(12px, 3cqw, 46px) clamp(30px, 7cqw, 100px) rgba(4, 16, 34, 0.55),
    0 clamp(2px, 0.7cqw, 12px) clamp(8px, 1.8cqw, 26px) rgba(4, 16, 34, 0.4);
}
/* 白卡身后的冷光晕：把卡片从深底上"托"起来，干净而不花 */
.hero-fluid .hero-mock::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  border-radius: clamp(16px, 4cqw, 36px);
  transform: translate(clamp(4px, 1.1cqw, 14px), clamp(4px, 1.1cqw, 14px));
  background: linear-gradient(135deg, rgba(120, 190, 255, 0.16), rgba(232, 90, 43, 0.14));
  filter: blur(clamp(6px, 1.8cqw, 22px));
}
.mock-cap {
  font-size: clamp(10px, 3.1cqw, 21px);
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.hero-fluid .mock-idea {
  border: 0;
  box-shadow: none;
  min-height: 0;
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  padding: clamp(10px, 3.4cqw, 30px) 0 0;
}
/* ---- 卡内层级：编号 → 标题 → 描述 → 三列信息带 ---- */
.hero-fluid .mock-idea .idea-no {
  font-size: clamp(12px, 4.4cqw, 34px);
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #9AAEBF;
}
.hero-fluid .mock-idea h3 {
  font-size: clamp(24px, 8.8cqw, 72px);
  line-height: 1.08;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin: clamp(6px, 1.9cqw, 16px) 0 clamp(6px, 1.8cqw, 14px);
}
.hero-fluid .mock-idea p {
  font-size: clamp(13px, 4.4cqw, 33px);
  line-height: 1.46;
  color: #45596B;
}
/* 标签沉到面板底部、三列等宽铺满 → 底部一条整齐的信息带 */
.hero-fluid .mock-idea .meta-row {
  margin-top: auto;
  padding-top: clamp(8px, 1.9cqw, 20px);
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: clamp(6px, 1.5cqw, 14px);
}
.hero-fluid .mock-idea .tag {
  font-size: clamp(11px, 3.4cqw, 25px);
  padding: clamp(5px, 1.3cqw, 12px) clamp(6px, 1.6cqw, 14px);
  font-weight: 700;
  background: rgba(232, 90, 43, 0.09);
  border-color: rgba(232, 90, 43, 0.32);
  color: #A93D1C;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* 卡片顶部标识带加厚，像产品样张而不是文档缩略图 */
.hero-fluid .mock-idea::before { height: clamp(3px, 0.9cqw, 9px); }

/* ---------- 底栏 ---------- */
.hero-fluid .hero-foot {
  padding: clamp(12px, 1.6vh, 22px) var(--pad-x);
  font-size: var(--fs-foot);
  gap: 16px;
  flex-wrap: wrap;
}

/* ---------- 矮窗口：右栏收紧，保证首屏完整 ---------- */
@media (max-height: 800px) {
  .hero-fluid .hero-mock { margin-top: clamp(12px, 2.2vh, 34px); }
  .hero-fluid .hero-mock .card { padding: clamp(13px, 4.05cqw, 32px); }
  .hero-fluid .mock-idea { padding-top: clamp(9px, 2.5cqw, 20px); }
  .hero-fluid .mock-idea h3 { font-size: clamp(20px, 7.2cqw, 46px); margin: clamp(7px, 2cqw, 15px) 0 clamp(6px, 1.8cqw, 14px); }
  .hero-fluid .mock-idea p { font-size: clamp(12.5px, 4cqw, 25px); }
  .hero-fluid .mock-idea .meta-row { margin-top: clamp(10px, 2.8cqw, 24px); }
  .hero-fluid .hero-empathy { line-height: 1.54; }
  .hero-fluid .hero-price { margin-top: clamp(16px, 2.6vh, 40px); }
  .hero-fluid .hero-body { padding-bottom: clamp(12px, 2.4vh, 38px); }
}
@media (max-height: 700px) {
  .hero-fluid .hero-mock { margin-top: clamp(10px, 1.8vh, 26px); }
  .hero-fluid .hero-mock .card { padding: clamp(13px, 3.9cqw, 28px); }
  .hero-fluid .mock-idea { padding-top: clamp(8px, 2.5cqw, 18px); }
  .hero-fluid .mock-idea h3 { font-size: clamp(19px, 7cqw, 42px); }
  .hero-fluid .mock-idea p { font-size: clamp(12px, 3.8cqw, 23px); }
  .hero-fluid .mock-idea .tag { font-size: clamp(10.5px, 3.2cqw, 22px); }
  .hero-fluid .hero-empathy { line-height: 1.5; }
  .hero-fluid .hero-top { padding-top: 10px; padding-bottom: 10px; }
  .hero-fluid .hero-body { padding-bottom: clamp(12px, 3vh, 34px); }
  .hero-fluid .hero-foot { padding-top: 10px; padding-bottom: 10px; }
}

/* ---------- 窄窗口：单列堆叠（不再横向挤压） ---------- */
@media (max-width: 960px) {
  .hero-fluid .hero-body { grid-template-columns: minmax(0, 1fr); row-gap: clamp(24px, 4vh, 52px); }
  .hero-fluid .hero-mock { align-self: flex-start; transform-origin: bottom left; margin-top: clamp(26px, 4.4vh, 56px); }

}
</style>

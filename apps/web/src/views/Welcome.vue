<!-- Welcome.vue — B-03（负责人：B）
     对应 en/html/01-welcome.html：全屏 hero（无 AppShell），零偏差还原。
     B-13：hero-trust / hero-foot 两个价格槽。 -->
<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { t } from "../i18n";
import { renderPriceSlots } from "../bridge/price";

const router = useRouter();
onMounted(renderPriceSlots);
</script>

<template>
  <div class="hero">
    <div class="orb a"></div><div class="orb b"></div>
    <div class="hero-top">
      <div class="brand"><div class="brand-mark">B</div><div>BizSpark<small>{{ t("brand.tag") }}</small></div></div>
      <div class="hero-links">
        <span>{{ t("welcome.link_how") }}</span><span>{{ t("welcome.link_get") }}</span>
        <span>{{ t("welcome.link_privacy") }}</span><span>v1.0.0</span>
      </div>
    </div>
    <div class="hero-body"><div class="hero-in">
      <div class="eyebrow">{{ t("welcome.eyebrow") }}</div>
      <h1 v-html="t('welcome.h1')"></h1>
      <p>{{ t("welcome.lead") }}</p>
      <div class="btn-row">
        <button class="btn btn-primary btn-lg" type="button" @click="router.push('/quiz')">{{ t("welcome.cta_start") }}&nbsp;→</button>
        <button class="btn btn-quiet btn-lg" type="button" @click="router.push('/saved')">{{ t("welcome.cta_saved") }}</button>
      </div>
      <div class="hero-price">
        <div data-price-slot="hero-trust"></div>
        <div>✓ {{ t("welcome.offline") }}</div><div>✓ {{ t("welcome.never_leave") }}</div>
      </div>
    </div></div>
    <div class="hero-mock"><div class="card">
      <div class="tiny mock-cap">{{ t("welcome.mock_cap") }}</div>
      <div class="mock-card">
        <div class="idea-no">01 / 03 &nbsp;·&nbsp; 94% {{ t("common.match") }}</div>
        <h3>{{ t("welcome.mock_title") }}</h3>
        <p>{{ t("welcome.mock_desc") }}</p>
        <div class="meta-row"><span class="tag">{{ t("welcome.mock_tag1") }}</span><span class="tag">{{ t("welcome.mock_tag2") }}</span><span class="tag">{{ t("welcome.mock_tag3") }}</span></div>
      </div>
    </div></div>
    <div class="hero-foot"><span>{{ t("welcome.foot") }}</span><span data-price-slot="hero-foot"></span></div>
  </div>
</template>

<style scoped>
.hero{min-height:100vh;background:radial-gradient(1100px 620px at 78% 12%,#1C4262 0%,transparent 62%),
  radial-gradient(760px 520px at 8% 92%,#3A2A28 0%,transparent 60%),var(--deep);color:#fff;position:relative;overflow:hidden;display:flex;flex-direction:column}
.hero::before{content:"";position:absolute;inset:0;opacity:.16;
  background-image:radial-gradient(rgba(255,255,255,.5) .7px,transparent .7px);background-size:26px 26px}
.orb{position:absolute;border-radius:50%;filter:blur(2px)}
.orb.a{width:340px;height:340px;border:1px solid rgba(255,255,255,.13);right:8%;top:16%}
.orb.b{width:220px;height:220px;background:radial-gradient(circle,rgba(242,101,58,.35),transparent 70%);right:16%;top:26%}
.hero-top{position:relative;z-index:2;display:flex;align-items:center;justify-content:space-between;padding:30px 48px}
.brand{display:flex;align-items:center;gap:11px;font-size:19px;font-weight:750;letter-spacing:-.4px}
.brand-mark{width:32px;height:32px;border-radius:10px;background:var(--accent);display:grid;place-items:center;font-size:17px;font-weight:800;color:#fff;box-shadow:0 6px 16px rgba(242,101,58,.35)}
.brand small{display:block;font-size:10px;font-weight:500;letter-spacing:1.4px;color:#88A0B4;text-transform:uppercase;margin-top:2px}
.hero-links{display:flex;gap:26px;font-size:12.5px;color:#9FB2C2}
.hero-body{position:relative;z-index:2;flex:1;display:flex;align-items:center;padding:20px 48px 60px}
.hero-in{max-width:700px}
.eyebrow{color:var(--gold)}
.hero h1{font-size:66px;line-height:1.06;letter-spacing:-3px;font-weight:760}
.hero h1 :deep(em){font-style:normal;color:var(--accent)}
.hero p{font-size:17px;color:#B7C6D3;max-width:530px;margin-top:22px;line-height:1.65}
.hero .btn-row{margin-top:36px}
.hero .btn-quiet{color:#B7C6D3}
.hero-price{display:flex;align-items:center;gap:22px;margin-top:52px;font-size:12px;color:#8FA4B6}
.hero-price b{color:#fff;font-size:15px}
.hero-foot{position:relative;z-index:2;display:flex;justify-content:space-between;padding:22px 48px;
  border-top:1px solid rgba(255,255,255,.1);font-size:11px;color:#7F95A8;letter-spacing:.3px}
.hero-mock{position:absolute;right:5%;top:50%;transform:translateY(-50%) rotate(-4deg);width:330px;z-index:1}
.hero-mock .card{padding:20px;box-shadow:0 30px 70px rgba(0,0,0,.35)}
.mock-cap{letter-spacing:1.4px;text-transform:uppercase}
.mock-card{min-height:0;background:#fff;color:var(--ink);position:relative;overflow:hidden;padding:16px 0 0}
.mock-card::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:var(--accent);opacity:.85}
.mock-card h3{font-size:14px;margin:8px 0}
.mock-card p{font-size:10.5px;color:var(--ink-2)}
.idea-no{font-size:11px;letter-spacing:1.5px;color:var(--ink-3);font-weight:700}
.meta-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.meta-row .tag{font-size:10.5px;padding:4px 9px;border-radius:999px;background:var(--bg);border:1px solid var(--line);color:var(--ink-2)}
</style>

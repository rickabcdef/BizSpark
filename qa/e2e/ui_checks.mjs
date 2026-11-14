/**
 * ui_checks.mjs — H-02/H-05 前端用例（负责人：H）
 *
 * 真前端（apps/web/dist）+ 真 sidecar（apps/core/main.py）+ 真浏览器（系统 Edge）。
 * 每个用例独立 appdata，互不影响；结果以 JSON 打给 stdout，由 qa/cases/test_ui.py 收集。
 *
 * 跑法：cd qa && node e2e/ui_checks.mjs            # 全部
 *       cd qa && node e2e/ui_checks.mjs T-05 T-19   # 指定用例
 */

import os from "node:os";
import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";
import { startBridge, REPO } from "./bridge_server.mjs";

const DIST = path.join(REPO, "apps", "web", "dist");
const LOCALES = JSON.parse(
  fs.readFileSync(path.join(REPO, "apps", "web", "src", "locales", "en-US.json"), "utf8"),
);
const t = (k) => LOCALES[k] || k;

const results = [];
const record = (id, ok, detail, metrics) => {
  results.push({ id, ok: Boolean(ok), detail: detail || "", metrics: metrics || {} });
  console.log(`[${ok ? "PASS" : "FAIL"}] ${id} ${detail || ""}`);
};

async function withApp(browser, fn, opts = {}) {
  const appData = fs.mkdtempSync(path.join(os.tmpdir(), "bz_ui_"));
  const bridge = await startBridge({ distDir: DIST, appData, ...opts });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  const requests = [];
  page.on("request", (r) => requests.push(r.url()));
  try {
    return await fn({ page, bridge, appData, errors, requests });
  } finally {
    await ctx.close();
    await bridge.close();
    fs.rmSync(appData, { recursive: true, force: true });
  }
}

const goto = async (page, base, hash) => {
  await page.goto(base + "/" + (hash ? "#" + hash : ""), { waitUntil: "networkidle" });
  await page.waitForTimeout(120);
};

/** 依次回答 5 题（默认每题选第 idx 个选项），最后停在 Results。 */
async function answerQuiz(page, picks = [0, 1, 0, [0, 2, 4], 0]) {
  await goto(page, page.__base, "/quiz");
  for (let i = 0; i < 5; i++) {
    const opts = page.locator(".opt");
    await opts.first().waitFor({ state: "visible" });
    if (i === 3) {
      for (const k of picks[3]) await opts.nth(k).click();
    } else {
      await opts.nth(picks[i]).click();
    }
    await page.waitForTimeout(150);
    // 界面对齐基线：Back/Next 手动推进（AL-B 卡：不要自动跳题）
    await page.locator("button.btn-primary").click();
    await page.waitForTimeout(250);
  }
  await page.waitForTimeout(600); // 等 diagnose
}

/* ------------------------------------------------------------------ */
/* 用例                                                                */
/* ------------------------------------------------------------------ */

const CHECKS = {
  "T-01": async (browser) => withApp(browser, async ({ page, bridge, requests }) => {
    const t0 = Date.now();
    await page.goto(bridge.base + "/", { waitUntil: "load" });
    await page.locator(".hero .btn-primary").waitFor();
    const ms = Date.now() - t0;
    const scroll = await page.evaluate(() => document.documentElement.scrollHeight - window.innerHeight);
    const primaries = await page.locator(".btn-primary").count();
    const orange = await page.locator(".hero .btn-primary").first().evaluate(
      (el) => getComputedStyle(el).backgroundColor,
    );
    const external = requests.filter((u) => !u.startsWith(bridge.base));
    record("T-01", ms <= 1500 && scroll <= 1 && primaries === 1 && external.length === 0,
      `首屏 ${ms}ms（红线 1500）· 溢出 ${scroll}px · 主 CTA ${primaries} 个 · 外网请求 ${external.length}`,
      { ms, scroll, primaries });
  }),

  "T-03": async (browser) => withApp(browser, async ({ page, bridge }) => {
    // 模拟 sidecar 两次失败：所有 cmd 都回 E_CORE_DOWN
    await goto(page, bridge.base, "/");
    await goto(page, bridge.base, "/saved");
    const body = await page.locator("body").innerText();
    const red = await page.evaluate(() => {
      const bad = [];
      document.querySelectorAll("*").forEach((el) => {
        const c = getComputedStyle(el).color;
        const m = c.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (m && Number(m[1]) > 170 && Number(m[2]) < 90 && Number(m[3]) < 90 && el.textContent.trim()) {
          bad.push(el.className || el.tagName);
        }
      });
      return bad;
    });
    const shouts = /(error|failed|错误|失败|无法)/i.test(body);
    record("T-03", red.length === 0 && !shouts,
      `降级页无红色提示（${red.length} 处红字）· 无错误字样=${!shouts}`, { red: red.slice(0, 5) });
  }, { failMode: "core_down" }),

  "T-04": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await goto(page, bridge.base, "/");
    await page.locator("a.btn, button.btn").filter({ hasText: t("welcome.cta_start") }).first().click();
    await page.waitForTimeout(300);
    const hash = await page.evaluate(() => location.hash);
    const onCount = await page.locator(".step.on").count();
    const firstOn = onCount === 1 ? (await page.locator(".step").first().getAttribute("class")) || "" : "";
    const bg = await page.locator(".step.on .num").evaluate((el) => getComputedStyle(el).backgroundColor);
    record("T-04", hash.includes("/quiz") && onCount === 1 && /on/.test(firstOn) && /242/.test(bg),
      `路由 ${hash} · stepper 高亮 ${onCount} 个 · 第 1 点色 ${bg}`);
  }),

  "T-05": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await goto(page, bridge.base, "/quiz");
    // 基线交互：点选项出选中态 → Next question 推进（界面对齐 AL-B 卡）
    await page.locator(".opt").first().click();
    await page.waitForTimeout(150);
    const sel = await page.locator(".opt.sel").count();
    await page.locator("button.btn-primary").click();
    await page.waitForTimeout(350);
    const after = await page.locator(".q-count").innerText();
    const advanced = /0?2/.test(after);
    record("T-05", sel === 1 && advanced, `选中态 ${sel} 个 · Next 推进到「${after.trim()}」`);
  }),

  "T-06": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await goto(page, bridge.base, "/quiz");
    // 基线交互：未选中时 Next 置灰、连点不动；选中后 Next 推进一题
    const next = page.locator("button.btn-primary");
    const disabled = await next.isDisabled();
    // 未选中时 Next 置灰：force 点击（disabled 元素浏览器不派发 click，页面不会动）
    await next.click({ force: true }); await next.click({ force: true }); await next.click({ force: true });
    await page.waitForTimeout(400);
    const before = await page.locator(".q-count").innerText();
    await page.locator(".opt").first().click();
    await page.waitForTimeout(150);
    await next.click();
    await page.waitForTimeout(400);
    const after = await page.locator(".q-count").innerText();
    record("T-06", disabled && before !== after,
      `未选连点不动（${before.trim()}）· 选中后 Next 进题（→ ${after.trim()}）· 未选时置灰=${disabled}`);
  }),

  "T-07": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await goto(page, bridge.base, "/quiz");
    // 先用 Next 走到第 4 题（多选页）
    for (let i = 0; i < 3; i++) {
      await page.locator(".opt").first().click();
      await page.waitForTimeout(150);
      await page.locator("button.btn-primary").click();
      await page.waitForTimeout(300);
    }
    const opts = page.locator(".opt");
    await opts.nth(0).click();
    await opts.nth(2).click();
    await opts.nth(4).click();
    const picked3 = await page.locator(".opt.sel").count();
    await page.getByRole("button", { name: t("quiz.q4.nothing") }).click();
    // Nothing yet 自身会显示为选中态，所以数"资产项里被选中的个数"
    const picked0 = await page.locator(".opts .opt.sel").evaluateAll(
      (els) => els.filter((e) => !/Nothing yet/i.test(e.textContent)).length,
    );
    await opts.nth(1).click();
    const picked1 = await page.locator(".opts .opt.sel").evaluateAll(
      (els) => els.filter((e) => !/Nothing yet/i.test(e.textContent)).length,
    );
    const nextBtn = page.getByRole("button", { name: new RegExp(t("quiz.next")) });
    const enabled = (await nextBtn.count()) === 1 && (await nextBtn.isEnabled());
    record("T-07", picked3 === 3 && picked0 === 0 && picked1 === 1 && enabled,
      `选 3 项=${picked3} → Nothing yet 清空=${picked0} → 再选 1=${picked1} · Next 可用=${enabled}`);
  }),

  "T-08": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await answerQuiz(page, [0, 1, 0, [0, 2], 0]);
    await page.locator("a.btn, button.btn").filter({ hasText: t("results.change") }).first().click();
    await page.waitForTimeout(600);
    const stepNow = await page.evaluate(() =>
      Array.from(document.querySelectorAll(".step")).findIndex((s) => s.classList.contains("on")));
    // 回到 Q1 时应带上次答案（United States 选中）
    const selText = await page.locator(".opt.sel").first().innerText().catch(() => "");
    record("T-08", selText.includes("United States") || selText.includes("United"),
      `Back 后停在第 ${stepNow + 1} 题，预选项「${selText.split("\n")[0] || "无"}」`);
  }),

  "T-19": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await answerQuiz(page);
    const cards = page.locator(".idea-card");
    const n = await cards.count();
    const heights = await cards.evaluateAll((els) => els.map((e) => Math.round(e.getBoundingClientRect().height)));
    const equal = heights.length > 0 && Math.max(...heights) - Math.min(...heights) <= 2;
    const order = await cards.first().evaluate((el) =>
      Array.from(el.children).map((c) => c.className || c.tagName.toLowerCase()));
    const extraBtns = await page.evaluate(() => {
      const allow = ["See the one-page plan", "Change my answers", "Save all three", "Saved ✓"];
      return Array.from(document.querySelectorAll("button, a.btn"))
        .map((b) => b.textContent.replace(/\s+/g, " ").trim())
        .filter((txt) => txt && !allow.some((a) => txt.startsWith(a)) && !txt.startsWith("←"));
    });
    const ok = n === 3 && equal && order[0].includes("idea-no") && order.length === 6
      && order[1] === "h3" && order[4].includes("meta-row") && extraBtns.length === 0;
    record("T-19", ok, `${n} 卡 · 等高=${equal}(${heights.join("/")}) · 元素序 ${order.length} 个 · 多余控件 ${extraBtns.length}`,
      { heights, order });
  }),

  "T-20": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await answerQuiz(page, [0, 1, 0, [0, 2], 0]);   // US / 第2档 / <10h
    const lead = await page.locator(".page-head .lead").innerText();
    const need = [t("results.ans_cap2"), t("results.ans_h1"), "United States"];
    const missing = need.filter((w) => !lead.includes(w));
    record("T-20", missing.length === 0, `复述句「${lead}」· 缺 ${JSON.stringify(missing)}`);
  }),

  "T-21": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await answerQuiz(page);
    await page.locator(".card-cta").first().click();
    await page.waitForTimeout(700);
    const heads = await page.locator(".card.sec h3").allInnerTexts();
    const want = [t("detail.costs_h"), t("detail.steps_h"), t("detail.channels_h"), t("detail.pitfalls_h")];
    const ok = heads.length === 4 && heads.every((h, i) => h === want[i]);
    record("T-21", ok, `4 卡顺序：${heads.map((h) => h.slice(0, 12)).join(" | ")}`);
  }),

  "T-22": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await answerQuiz(page);
    await page.locator(".card-cta").first().click();
    await page.waitForTimeout(700);
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(300);
    const box = await page.locator(".sticky").boundingBox();
    const inView = box && box.y < 900 && box.y + Math.min(box.height, 300) > 0;
    const pos = await page.locator(".sticky").evaluate((el) => getComputedStyle(el).position);
    record("T-22", Boolean(inView), `滚到底后右侧卡仍在视口（position:${pos}, y=${Math.round(box?.y ?? -1)}）`);
  }),

  "T-24": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await answerQuiz(page);
    await page.locator(".card-cta").first().click();
    await page.waitForTimeout(700);
    const text = (await page.locator(".detail-wrap").innerText()).toLowerCase();
    const banned = ["wave", "maturity", "algorithm", "score", "version"].filter((w) => text.includes(w));
    record("T-24", banned.length === 0, `详情页全文禁词命中：${JSON.stringify(banned)}`);
  }),

  "T-37": async (browser) => withApp(browser, async ({ page, bridge }) => {
    page.__base = bridge.base;
    await answerQuiz(page);
    await page.getByRole("button", { name: new RegExp(t("results.save_all")) }).click();
    await page.waitForTimeout(500);
    await goto(page, bridge.base, "/saved");
    // 基线 06 屏（AL-B2 / V2 Backlog）：Compare two ideas 与 Clear saved list 第一版不摆
    const cmp = await page.locator("a.btn, button.btn").filter({ hasText: t("saved.compare") }).count();
    const clr = await page.locator("a.btn, button.btn").filter({ hasText: t("saved.clear") }).count();
    const body = (await page.locator("body").innerText()).toLowerCase();
    const banned = ["score", "weight", "algorithm", "compare two"].filter((w) => body.includes(w));
    const openBtns = await page.locator(".mini a.btn").count();
    record("T-37", cmp === 0 && clr === 0 && banned.length === 0 && openBtns >= 1,
      `06 屏无 Compare/Clear 假按钮（cmp ${cmp}·clear ${clr}）· 存档卡可打开 ${openBtns} 张 · 禁词 ${JSON.stringify(banned)}`);
  }),

  "T-46": async (browser) => withApp(browser, async ({ page, bridge }) => {
    await goto(page, bridge.base, "/settings");
    const rows = await page.locator(".set-row").count();
    const pills = await page.locator(".state-pill").count();
    // 基线 09 屏：5 行只读 state-pill；语言行/更改路径/检查更新/查看授权一律不摆（AL-B2）
    const controls = await page.evaluate(() =>
      document.querySelectorAll(".main select, .main .toggle, .main .sel-box, .main button, .main input[type=button]").length);
    const body = (await page.locator(".main").innerText()).toLowerCase();
    const banned = ["account settings", "notification", "theme store", "订阅", "check for updates", "view licence"].filter((w) => body.includes(w));
    record("T-46", rows === 5 && pills === 5 && controls === 0 && banned.length === 0,
      `设置 ${rows} 行只读（pill ${pills}）· 可点控件 ${controls} 个（要求 0）· 多余项 ${JSON.stringify(banned)}`);
  }),

  "T-47": async (browser) => withApp(browser, async ({ page, bridge, requests }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await goto(page, bridge.base, "/settings");
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    const dark = /rgb\((\d+), (\d+), (\d+)\)/.exec(bg)?.slice(1).map(Number) ?? [255, 255, 255];
    const lum = (0.299 * dark[0] + 0.587 * dark[1] + 0.114 * dark[2]) / 255;
    const external = requests.filter((u) => !u.startsWith(bridge.base));
    record("T-47", lum < 0.5 && external.length === 0,
      `深色模式 body 亮度 ${lum.toFixed(2)}（<0.5 为深色）· 外网请求 ${external.length}`);
  }),

  "T-59": async (browser) => {
    const visible = { display_mode: "visible", amount: 39, currency: "USD", model: "one-time" };
    const hidden = { display_mode: "hidden", amount: null, currency: "USD", model: "one-time" };
    const out = await withApp(browser, async ({ page, bridge }) => {
      await goto(page, bridge.base, "/");
      const trust = await page.locator('[data-price-slot="hero-trust"]').innerText();
      const foot = await page.locator('[data-price-slot="hero-foot"]').innerText();
      await goto(page, bridge.base, "/activate");
      const eye = await page.locator('[data-price-slot="activate-eyebrow"]').innerText();
      return { trust, foot, eye };
    }, { pricing: visible });
    const out2 = await withApp(browser, async ({ page, bridge }) => {
      await goto(page, bridge.base, "/");
      const trust = await page.locator('[data-price-slot="hero-trust"]').innerText();
      const foot = await page.locator('[data-price-slot="hero-foot"]').innerText();
      const hasAmount = /\$\s?\d/.test(trust + foot);
      return { trust, foot, hasAmount };
    }, { pricing: hidden });
    const rendered = /\$39\.00/.test(out.trust) && /\$39\.00/.test(out.foot) && /\$39\.00/.test(out.eye);
    record("T-59", rendered && !out2.hasAmount,
      `visible：hero-trust「${out.trust}」/ hero-foot「${out.foot}」/ activate「${out.eye}」；hidden 无金额=${!out2.hasAmount}`,
      { visible: out, hidden: out2 });
  },
};

/* ------------------------------------------------------------------ */

async function main() {
  const only = process.argv.slice(2).filter((a) => a.startsWith("T-"));
  const ids = only.length ? only : Object.keys(CHECKS);
  if (!fs.existsSync(path.join(DIST, "index.html"))) {
    console.error("dist 不存在，先跑 (cd apps/web && npm run build)");
    process.exit(2);
  }
  const browser = await chromium.launch({ channel: "msedge" });
  try {
    for (const id of ids) {
      const fn = CHECKS[id];
      if (!fn) {
        record(id, false, "没有对应实现");
        continue;
      }
      try {
        await fn(browser);
      } catch (e) {
        record(id, false, "异常：" + String(e.message || e).split("\n")[0]);
      }
    }
  } finally {
    await browser.close();
  }
  const summary = {
    total: results.length,
    passed: results.filter((r) => r.ok).length,
    failed: results.filter((r) => !r.ok).map((r) => r.id),
    results,
  };
  fs.mkdirSync(path.join(REPO, "qa", "reports"), { recursive: true });
  fs.writeFileSync(path.join(REPO, "qa", "reports", "ui-checks.json"),
    JSON.stringify(summary, null, 2) + "\n", "utf8");
  console.log(`\n== UI 用例 ${summary.passed}/${summary.total} 通过 ==`);
  process.exit(0);
}

main();

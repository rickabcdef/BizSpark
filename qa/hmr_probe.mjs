/**
 * hmr_probe.mjs — 「改完即见」自检（PM 2026-11-14）
 *
 * 证明开发常驻站两种改动都能自动生效，不需要手动刷新：
 *   阶段 A 组件（.vue）：给 Settings.vue 的 h1 临时加 data-hmr-probe 属性
 *           → 期望：属性出现 **且** window.__probe 标记还在（= 真组件级热替换，页面没刷新）
 *   阶段 B 语言包（.json）：改 en-US.json 的 settings.h1 文案
 *           → 期望：h1 文案自动变（JSON 模块无热替换边界，Vite 会整页自动刷新，属正常）
 * 两个阶段都在 finally 里还原源文件，不会把探针留在代码里。
 *
 * 用法：node qa/hmr_probe.mjs [端口，默认 5181]
 * 退出码：0 两阶段都生效；1 有阶段没生效（打印具体是哪个）
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const QA = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.join(QA, "..", "apps", "web", "src");
const VUE = path.join(SRC, "views", "Settings.vue");
const LOCALE = path.join(SRC, "locales", "en-US.json");
const PORT = Number(process.argv[2] || 5181);
const BASE = `http://127.0.0.1:${PORT}`;

const vueSrc = fs.readFileSync(VUE, "utf8");
const locSrc = fs.readFileSync(LOCALE, "utf8");
const H1 = '<h1>{{ t("settings.h1") }}</h1>';
const LOC_KEY = '"settings.h1": "Settings"';
if (!vueSrc.includes(H1) || !locSrc.includes(LOC_KEY)) {
  console.error("探针锚点找不到，请先核对 Settings.vue / en-US.json");
  process.exit(2);
}

const browser = await chromium.launch({ channel: "msedge" });
let aOk = false;
let bOk = false;
try {
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const reloads = [];
  page.on("load", () => reloads.push(Date.now()));
  await page.goto(`${BASE}/#/settings`, { waitUntil: "networkidle" });
  await page.waitForTimeout(500);
  await page.evaluate(() => { window.__probe = "alive"; });
  const h1Before = await page.locator("h1").innerText();

  // ---------- 阶段 A：.vue 组件热替换（不刷新） ----------
  try {
    fs.writeFileSync(VUE, vueSrc.replace(H1, '<h1 data-hmr-probe="1">{{ t("settings.h1") }}</h1>'), "utf8");
    await page.waitForTimeout(2500);
    const a = await page.evaluate(() => ({
      flag: document.querySelector("h1")?.getAttribute("data-hmr-probe"),
      probe: window.__probe,
    }));
    aOk = a.flag === "1" && a.probe === "alive";
    console.log(`阶段 A 组件热替换：属性 ${a.flag === "1" ? "已生效" : "未生效"} · ` +
      `页面${a.probe === "alive" ? "未刷新" : "被整页刷新"} → ${aOk ? "PASS" : "FAIL"}`);
  } finally {
    fs.writeFileSync(VUE, vueSrc, "utf8");
    await page.waitForTimeout(1200);
  }

  // ---------- 阶段 B：语言包改动（允许整页自动刷新） ----------
  try {
    fs.writeFileSync(LOCALE, locSrc.replace(LOC_KEY, '"settings.h1": "Settings ⟳ HMR"'), "utf8");
    await page.waitForTimeout(2500);
    const mid = await page.locator("h1").innerText();
    bOk = mid === "Settings ⟳ HMR";
    console.log(`阶段 B 语言包改动：h1 变为「${mid}」→ ${bOk ? "PASS（自动刷新生效）" : "FAIL"}`);
  } finally {
    fs.writeFileSync(LOCALE, locSrc, "utf8");
    await page.waitForTimeout(1500);
  }

  const h1After = await page.locator("h1").innerText();
  const restored = h1After === h1Before && fs.readFileSync(VUE, "utf8") === vueSrc;
  console.log(`源文件已还原：${restored ? "是" : "否！请检查 Settings.vue / en-US.json"}`);
  console.log(`期间页面 load 次数：${reloads.length}（阶段 B 的自动刷新计 1 次属正常）`);
  console.log(aOk && bOk && restored ? "\n✅ 改完即见：组件热替换 + 语言包自动刷新都可用" : "\n❌ 有阶段未生效");
} finally {
  // 双保险：异常退出也还原
  fs.writeFileSync(VUE, vueSrc, "utf8");
  fs.writeFileSync(LOCALE, locSrc, "utf8");
  await browser.close();
}
process.exit(aOk && bOk ? 0 : 1);

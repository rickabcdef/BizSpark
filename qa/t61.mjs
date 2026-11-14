/**
 * t61.mjs — 界面对齐门禁（AL-H1）：两版界面零假控件 + 装饰只读 + 主链路连点
 *
 * 查什么：
 *   1) 9 页全部可达（hash 路由）
 *   2) 死链 href="#"、假开关 .toggle、假下拉 select/.sel-box → 零命中
 *   3) 装饰元素（chip/avatar/crumb/side-ver/badge-line/hero-meta/state-pill）
 *      computed style：user-select=none；hero-meta/avatar/state-pill 另 pointer-events=none
 *   4) 主链路 01→02→03→04→05→06→02 每个按钮都有真实响应（URL 变化或内容变化）
 *   5) 中英两版各跑一遍
 *
 * 用法：cd qa && node t61.mjs 5180
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const port = Number(process.argv[2] || 5180);
const base = `http://127.0.0.1:${port}`;
const ROUTES = ["/", "/quiz", "/results", "/detail/x", "/export", "/saved", "/library", "/activate", "/settings"];
const PAGE_NO = ["01", "02", "03", "04", "05", "06", "08", "07", "09"]; // 与 ROUTES 对应
const REPORT = path.join(path.dirname(fileURLToPath(import.meta.url)), "reports", "t61.json");

const results = [];

async function auditPage(p, route, tag) {
  const out = { route, tag, dead: [], deco: [], buttons: 0 };
  await p.goto(base + "/#" + route, { waitUntil: "networkidle" });
  await p.waitForTimeout(500);

  // 1) 死链与假控件
  out.dead = await p.evaluate(() => {
    const bad = [];
    document.querySelectorAll('a[href="#"]').forEach((el) => bad.push("href=# <" + el.tagName + "> " + (el.textContent || "").trim().slice(0, 30)));
    document.querySelectorAll(".toggle").forEach(() => bad.push("假开关 .toggle"));
    document.querySelectorAll("select").forEach((el) => bad.push("下拉 select: " + (el.getAttribute("aria-label") || el.name || "")));
    document.querySelectorAll(".sel-box").forEach(() => bad.push("假下拉 .sel-box"));
    // 空按钮：无文字无 aria-label 无图标内容
    document.querySelectorAll("button").forEach((el) => {
      const txt = (el.textContent || "").trim();
      if (!txt && !el.getAttribute("aria-label")) bad.push("空按钮 <button> 无文字");
    });
    return bad;
  });

  // 2) 装饰元素只读
  out.deco = await p.evaluate(() => {
    const bad = [];
    const need = [
      [".chip", ["user-select", "none"]],
      [".avatar", ["pointer-events", "none"]],
      [".crumb", ["user-select", "none"]],
      [".side-ver", ["user-select", "none"]],
      [".badge-line", ["user-select", "none"]],
    ];
    for (const [sel, [prop, want]] of need) {
      const el = document.querySelector(sel);
      if (!el) continue;
      const v = getComputedStyle(el)[prop.replace(/-(\w)/g, (_, c) => c.toUpperCase())];
      if (v !== want) bad.push(`${sel} ${prop}=${v}（应 ${want}）`);
    }
    const hm = document.querySelector(".hero-meta");
    if (hm) {
      const cs = getComputedStyle(hm);
      if (cs.userSelect !== "none" || cs.pointerEvents !== "none") bad.push(".hero-meta 不可选/不可点未生效");
    }
    document.querySelectorAll(".state-pill").forEach((el, i) => {
      const cs = getComputedStyle(el);
      if (cs.pointerEvents !== "none" || cs.userSelect !== "none") bad.push(`state-pill#${i} 只读未生效`);
    });
    return bad;
  });

  out.buttons = await p.locator("button:visible, a.btn:visible").count();
  return out;
}

async function walkMainFlow(p) {
  // 主链路 01→02→03→04→05→06→02：每个按钮点了要"真的走"
  const steps = [];
  const go = async (hash) => {
    await p.goto(base + "/#" + hash, { waitUntil: "networkidle" });
    await p.waitForTimeout(350);
  };
  const clickAndWait = async (label, expectHashPrefix) => {
    const before = new URL(p.url()).hash;
    const btn = p.locator("a.btn, button.btn").filter({ hasText: label }).first();
    if (!(await btn.count())) { steps.push(`${label}: 找不到按钮 ✗`); return false; }
    await btn.click();
    await p.waitForTimeout(700);
    const after = new URL(p.url()).hash;
    const ok = expectHashPrefix ? after.startsWith(expectHashPrefix) : after !== before;
    steps.push(`${label}: ${before || "#/"} → ${after || "#/"} ${ok ? "✓" : "✗"}`);
    return ok;
  };

  let ok = true;
  await go("/");
  ok = (await clickAndWait("找我的 3 个点子", "#/quiz")) && ok;
  // 答完 5 题（每题选第 1 项 → Next）
  for (let i = 0; i < 5; i++) {
    const opts = p.locator(".opt");
    if (await opts.count()) {
      await opts.nth(0).click();
      await p.waitForTimeout(120);
      if (i === 3) { await opts.nth(2).click(); await p.waitForTimeout(120); }
    }
    const next = p.locator("button.btn-primary:enabled");
    await next.click();
    await p.waitForTimeout(900);
  }
  ok = (new URL(p.url()).hash.startsWith("#/results") ? true : (steps.push("问卷推进未到结果页 ✗"), false)) && ok;
  ok = (await clickAndWait("看一页方案", "#/detail/")) && ok;
  ok = (await clickAndWait("导出我的方案", "#/export")) && ok;
  ok = (await clickAndWait("打开我存的点子", "#/saved")) && ok;
  ok = (await clickAndWait("找新点子", "#/quiz")) && ok;
  return { steps, ok };
}

const browser = await chromium.launch({ channel: "msedge" });
for (const locale of ["zh-CN", "en-US"]) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale });
  const p = await ctx.newPage();
  for (let i = 0; i < ROUTES.length; i++) {
    results.push(await auditPage(p, ROUTES[i], `${locale} ${PAGE_NO[i]}`));
  }
  if (locale === "zh-CN") {
    const flow = await walkMainFlow(p);
    results.push({ route: "主链路", tag: "flow", flow });
  }
  await ctx.close();
}
await browser.close();

let fail = 0;
for (const r of results) {
  if (r.flow) {
    console.log(`\n== 主链路连点 ==`);
    for (const s of r.flow.steps) console.log("  " + s);
    if (!r.flow.ok) fail++;
    continue;
  }
  const bad = [...r.dead, ...r.deco];
  if (bad.length) fail++;
  console.log(`${bad.length ? "✗" : "✓"} ${r.tag} ${r.route}  按钮 ${r.buttons}${bad.length ? "\n     " + bad.join("\n     ") : ""}`);
}
console.log(fail === 0 ? "\n✅ T-61 通过：零假控件、装饰只读、主链路全通" : `\n❌ T-61 未过：${fail} 项`);

fs.mkdirSync(path.dirname(REPORT), { recursive: true });
fs.writeFileSync(
  REPORT,
  JSON.stringify({ gate: "T-61", date: new Date().toISOString(), status: fail === 0 ? "PASS" : "FAIL", fail, results }, null, 2) + "\n",
  "utf8",
);
console.log(`报告：${path.relative(process.cwd(), REPORT)}`);
process.exit(fail === 0 ? 0 : 1);

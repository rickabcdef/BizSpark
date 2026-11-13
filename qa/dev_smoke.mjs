/**
 * dev_smoke.mjs — 开发站快速自检（PM 2026-11-13）
 *
 * 改动后一键确认：页面能开、无 JS 报错、中文生效、IPC 通。比全量回归快得多。
 *
 * 用法：cd qa && node dev_smoke.mjs [port]
 */
import { chromium } from "playwright";

const port = Number(process.argv[2] || 5180);
const base = `http://127.0.0.1:${port}`;

const b = await chromium.launch({ channel: "msedge" });
const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
const errs = [];
const notFound = [];
p.on("pageerror", (e) => errs.push("pageerror: " + String(e)));
p.on("console", (m) => {
  if (m.type() === "error" && !/favicon|Failed to load resource/i.test(m.text())) errs.push("console: " + m.text());
});
p.on("response", (r) => {
  if (r.status() >= 400) notFound.push(`${r.status()} ${r.url()}`);
});

await p.goto(base + "/", { waitUntil: "networkidle" });
await p.waitForTimeout(1000);

// 走一遍核心链路：首屏 → 问卷 5 题 → 结果 → 详情
const clickNext = async () => {
  const btn = p.locator(".btn-primary").last();
  if (await btn.count()) await btn.click();
  await p.waitForTimeout(450);
};

const firstCta = await p.locator(".btn-primary").first().innerText().catch(() => "");
await p.locator(".btn-primary").first().click();
await p.waitForTimeout(700);

for (let i = 0; i < 5; i++) {
  const opts = p.locator(".opt");
  const n = await opts.count();
  if (n === 0) break;
  if (i === 3) {
    // 技能题多选：选两项
    await opts.nth(0).click();
    await opts.nth(2).click();
  } else {
    await opts.nth(0).click();
  }
  await clickNext();
}
await p.waitForTimeout(1500);

const onResults = await p.locator(".card, .idea-card").count();
const titles = await p.locator(".card h3, .idea-card h3").allInnerTexts().catch(() => []);
const recap = await p.locator(".lead").first().innerText().catch(() => "");
const zhCount = (await p.locator("body").innerText()).match(/[\u4e00-\u9fff]/g)?.length || 0;

console.log("首屏 CTA:", firstCta.replace(/\s+/g, " ").trim());
console.log("结果页卡片:", onResults, titles.slice(0, 3));
console.log("复述句:", recap.replace(/\s+/g, " ").trim().slice(0, 90));
console.log("页面中文字符数:", zhCount);
console.log("locale:", await p.evaluate(() => document.documentElement.lang), "| dev:", await p.evaluate(() => !!window.BIZSPARK_DEV));
console.log("JS 错误:", errs.length === 0 ? "无" : errs.slice(0, 4));
console.log("4xx/5xx:", notFound.length === 0 ? "无" : notFound.slice(0, 4));

await b.close();
process.exit(errs.length === 0 && onResults >= 1 ? 0 : 1);

/**
 * c2-topbar-check.mjs — 本轮顶部规范自检：
 * 1) 内页顶栏无居中 .title；2) 每页顶栏右侧统一绿点隐私标注；
 * 3) 设置页无齿轮；4) 采集眉题颜色留档。手机视口截图。
 * 用法：cd qa && node c2-topbar-check.mjs
 */
import { chromium } from "playwright";

const base = "http://127.0.0.1:5181";
const routes = [
  ["quiz", "/#/quiz"],
  ["results", "/#/results"],
  ["detail", "/#/detail/test"],
  ["export", "/#/export"],
  ["saved", "/#/saved"],
  ["library", "/#/library"],
  ["settings", "/#/settings"],
];

const b = await chromium.launch({ channel: "msedge" });
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
const errs = [];
p.on("pageerror", (e) => errs.push("pageerror: " + String(e)));
p.on("console", (m) => {
  if (m.type() === "error" && !/favicon|Failed to load resource/i.test(m.text())) errs.push("console: " + m.text());
});

let fail = 0;
for (const [name, hash] of routes) {
  await p.goto(base + hash, { waitUntil: "networkidle" });
  await p.waitForTimeout(500);
  const titleCount = await p.locator(".topbar .title").count();
  const sideText = (await p.locator(".topbar .side").innerText().catch(() => "")).replace(/\s+/g, " ").trim();
  const gearCount = await p.locator(".gear").count();
  const eyrowColor = await p.locator(".eyebrow").first().evaluate((el) => getComputedStyle(el).color).catch(() => "—");
  const hasChip = /on this device|这台设备/.test(sideText);
  const ok = titleCount === 0 && hasChip && gearCount === 0;
  if (!ok) fail++;
  console.log(`[${ok ? "OK" : "FAIL"}] ${name} | chip="${sideText}" | title=${titleCount} gear=${gearCount} eyebrow=${eyrowColor}`);
  await p.screenshot({ path: `reports/c2-topbar-${name}.png`, fullPage: false });
}

console.log("\nJS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(fail ? 1 : 0);

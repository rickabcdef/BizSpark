/**
 * c-topbar-check.mjs — 临时自检：C 方案内页顶栏不得再有居中 .title。
 * 手机视口逐页断言 .topbar 内无 .title，并截图留档。
 * 用法：cd qa && node c-topbar-check.mjs
 */
import { chromium } from "playwright";

const base = "http://127.0.0.1:5181";
const routes = [
  ["quiz", "/#/quiz"],
  ["results", "/#/results"],
  ["saved", "/#/saved"],
  ["export", "/#/export"],
  ["detail", "/#/detail/test"],
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
  const topbarText = (await p.locator(".topbar").innerText().catch(() => "")).replace(/\s+/g, " ").trim();
  const h1 = (await p.locator("h1").first().innerText().catch(() => "")).replace(/\s+/g, " ").trim();
  const ok = titleCount === 0;
  if (!ok) fail++;
  console.log(`[${ok ? "OK" : "FAIL"}] ${name} | topbar="${topbarText}" | h1="${h1}" | title=${titleCount}`);
  await p.screenshot({ path: `reports/c-topbar-${name}.png`, fullPage: false });
}

console.log("\nJS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(fail ? 1 : 0);

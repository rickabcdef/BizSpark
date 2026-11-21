/**
 * c3-settings-check.mjs — 设置页眉题移除复核：头部无 eyebrow，标题+引导句保留，chip 在。
 */
import { chromium } from "playwright";

const b = await chromium.launch({ channel: "msedge" });
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
const errs = [];
p.on("pageerror", (e) => errs.push(String(e)));

await p.goto("http://127.0.0.1:5181/#/settings", { waitUntil: "networkidle" });
await p.waitForTimeout(500);

const eyebrowCount = await p.locator(".set-head .eyebrow").count();
const h1 = (await p.locator(".set-head h1").innerText().catch(() => "")).trim();
const lead = (await p.locator(".set-head .lead").innerText().catch(() => "")).replace(/\s+/g, " ").trim();
const sideText = (await p.locator(".topbar .side").innerText().catch(() => "")).replace(/\s+/g, " ").trim();
const gearCount = await p.locator(".gear").count();
const ok = eyebrowCount === 0 && h1 && /on this device/.test(sideText) && gearCount === 0;
console.log(`[${ok ? "OK" : "FAIL"}] eyebrow=${eyebrowCount} h1="${h1}" lead="${lead}" chip="${sideText}" gear=${gearCount}`);
await p.screenshot({ path: "reports/c3-settings.png", fullPage: false });
console.log("JS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(ok ? 0 : 1);

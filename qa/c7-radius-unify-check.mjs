/**
 * c7-radius-unify-check.mjs — 复核：动作按钮与底部菜单上圆角统一为 12px。
 */
import { chromium } from "playwright";

const b = await chromium.launch({ channel: "msedge" });
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
const errs = [];
p.on("pageerror", (e) => errs.push(String(e)));
const num = (v) => parseFloat(v);

await p.goto("http://localhost:5173/#/", { waitUntil: "networkidle" });
await p.waitForTimeout(700);

const radius = (sel) => p.locator(sel).first().evaluate((el) => getComputedStyle(el).borderTopLeftRadius);
const pri = await radius(".btn-primary");
const sec = await radius(".btn-secondary");
const dock = await p.locator(".tabbar").evaluate((el) => getComputedStyle(el).borderTopLeftRadius);
const ok = num(pri) === 12 && num(sec) === 12 && num(dock) === 12;
console.log(`[${ok ? "OK" : "FAIL"}] primary=${pri} secondary=${sec} tabbar=${dock}`);
await p.screenshot({ path: "reports/c7-welcome.png", fullPage: false });

console.log("JS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(ok && errs.length === 0 ? 0 : 1);

/**
 * c4-brand-align.mjs — 方案 A 复核：首页品牌行左右边距交给 content，badge 左沿与下方正文/h1 左基线对齐。
 * 内页 topbar 与 content 平级，顺带确认未被破坏、无 JS 报错。
 */
import { chromium } from "playwright";

const b = await chromium.launch({ channel: "msedge" });
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
const errs = [];
p.on("pageerror", (e) => errs.push(String(e)));

// 首页
await p.goto("http://localhost:5173/#/", { waitUntil: "networkidle" });
await p.waitForTimeout(700);

const badge = await p.locator(".brand-badge").boundingBox();
const eyebrow = await p.locator(".hero-eyebrow").boundingBox();
const h1 = await p.locator(".hero h1").boundingBox();
if (!badge || !eyebrow || !h1) { console.log("FAIL: 元素布局未就绪", { badge, eyebrow, h1 }); await b.close(); process.exit(1); }
const diffBadgeH1 = Math.abs(badge.x - h1.x);
const diffBadgeEyebrow = Math.abs(badge.x - eyebrow.x);
const brandName = (await p.locator(".brand-name").innerText().catch(() => "")).trim();
const okHome = diffBadgeH1 <= 1.5 && diffBadgeEyebrow <= 1.5 && brandName === "BizSpark";
console.log(`[${okHome ? "OK" : "FAIL"}] badge.x=${badge.x.toFixed(1)} eyebrow.x=${eyebrow.x.toFixed(1)} h1.x=${h1.x.toFixed(1)} badge→h1=${diffBadgeH1.toFixed(1)}px badge→eyebrow=${diffBadgeEyebrow.toFixed(1)}px brand="${brandName}"`);
await p.screenshot({ path: "reports/c4-welcome.png", fullPage: false });

// 内页抽查：设置页 topbar 平级结构未受影响
await p.goto("http://localhost:5173/#/settings", { waitUntil: "networkidle" });
await p.waitForTimeout(400);
const side = (await p.locator(".topbar .side").innerText().catch(() => "")).replace(/\s+/g, " ").trim();
const setH1 = (await p.locator(".set-head h1").innerText().catch(() => "")).trim();
const okInner = /on this device/.test(side) && setH1.length > 0;
console.log(`[${okInner ? "OK" : "FAIL"}] settings chip="${side}" h1="${setH1}"`);
await p.screenshot({ path: "reports/c4-settings.png", fullPage: false });

console.log("JS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(okHome && okInner && errs.length === 0 ? 0 : 1);

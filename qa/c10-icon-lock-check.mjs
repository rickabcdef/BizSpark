/**
 * c10-icon-lock-check.mjs — 复核：图标在英文手机窄屏下不被 flex 挤压，保持正方形尺寸。
 */
import { chromium } from "playwright";

const b = await chromium.launch({ channel: "msedge" });
const errs = [];
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
p.on("pageerror", (e) => errs.push(String(e)));

async function measure(sel, label) {
  const rows = await p.evaluate((sel) => {
    return [...document.querySelectorAll(sel)].map((svg) => {
      const r = svg.getBoundingClientRect();
      return { w: +r.width.toFixed(2), h: +r.height.toFixed(2) };
    });
  }, sel);
  console.log(`[${label}]`, JSON.stringify(rows));
  return rows;
}

await p.goto("http://localhost:5173/#/", { waitUntil: "networkidle" });
await p.waitForTimeout(500);
const hc = await measure(".hc-list .li svg", "EN 手机 hc-list 图标");
const trust = await measure(".trust .item svg", "EN 手机 trust 图标");
await p.locator(".hero-card").scrollIntoViewIfNeeded();
await p.waitForTimeout(200);
await p.screenshot({ path: "reports/c10-icon-mobile.png", fullPage: false });

await p.setViewportSize({ width: 1280, height: 900 });
await p.waitForTimeout(300);
await measure(".hc-list .li svg", "EN 电脑 hc-list 图标");

// 问答选项卡图标
await p.goto("http://localhost:5173/#/quiz", { waitUntil: "networkidle" });
await p.waitForTimeout(400);
await measure(".option .opt-ico svg", "quiz 选项卡图标");

const bad = hc.some((r) => Math.abs(r.w - 20) > 0.5 || Math.abs(r.h - 20) > 0.5);
console.log("hc-list 全部 20×20:", bad ? "FAIL" : "OK");
console.log("JS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(!bad && errs.length === 0 ? 0 : 1);

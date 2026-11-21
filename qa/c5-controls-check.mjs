/**
 * c5-controls-check.mjs — 复核：全站按钮 12px 圆角矩形 + 主按钮柔影；手机/平板底部菜单悬浮圆角 dock；宽屏左竖栏不变。
 */
import { chromium } from "playwright";

const b = await chromium.launch({ channel: "msedge" });
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
const errs = [];
p.on("pageerror", (e) => errs.push(String(e)));

const num = (v) => parseFloat(v);

// 首页
await p.goto("http://localhost:5173/#/", { waitUntil: "networkidle" });
await p.waitForTimeout(700);

const pri = await p.locator(".btn-primary").first().boundingBox();
const priStyle = await p.locator(".btn-primary").first().evaluate((el) => {
  const s = getComputedStyle(el);
  return { radius: s.borderTopLeftRadius, shadow: s.boxShadow };
});
const dock = await p.locator(".tabbar").boundingBox();
const dockStyle = await p.locator(".tabbar").evaluate((el) => {
  const s = getComputedStyle(el);
  return { radius: s.borderTopLeftRadius, pos: s.position, shadow: s.boxShadow };
});
const dockBottom = 844 - (dock.y + dock.height);
const okBtn = num(priStyle.radius) === 12 && priStyle.shadow !== "none";
const okDock = num(dockStyle.radius) === 18 && dock.x > 8 && dockBottom >= 8 && dockStyle.shadow !== "none";
console.log(`[${okBtn ? "OK" : "FAIL"}] primary radius=${priStyle.radius} shadow=${priStyle.shadow}`);
console.log(`[${okDock ? "OK" : "FAIL"}] dock radius=${dockStyle.radius} x=${dock.x.toFixed(1)} bottomGap=${dockBottom.toFixed(1)} pos=${dockStyle.pos} shadow=${dockStyle.shadow}`);
await p.screenshot({ path: "reports/c5-welcome.png", fullPage: false });

// 内页抽查：问答页按钮圆角
await p.goto("http://localhost:5173/#/quiz", { waitUntil: "networkidle" });
await p.waitForTimeout(500);
const quizBtnCount = await p.locator(".btn").count();
let quizBtnRadius = "n/a";
if (quizBtnCount > 0) {
  quizBtnRadius = await p.locator(".btn").first().evaluate((el) => getComputedStyle(el).borderTopLeftRadius);
}
console.log(`[${num(quizBtnRadius) === 12 ? "OK" : "INFO"}] quiz .btn count=${quizBtnCount} radius=${quizBtnRadius}`);
await p.screenshot({ path: "reports/c5-quiz.png", fullPage: false });

// 宽屏：左侧竖栏导航应保留，不变成悬浮横栏
await p.setViewportSize({ width: 1280, height: 900 });
await p.goto("http://localhost:5173/#/", { waitUntil: "networkidle" });
await p.waitForTimeout(500);
const wideNav = await p.locator(".tabbar").evaluate((el) => {
  const s = getComputedStyle(el);
  return { pos: s.position, dir: s.flexDirection, radius: s.borderTopLeftRadius, width: s.width };
});
const okWide = wideNav.pos === "sticky" && wideNav.dir === "column";
console.log(`[${okWide ? "OK" : "FAIL"}] wide nav pos=${wideNav.pos} dir=${wideNav.dir} radius=${wideNav.radius} width=${wideNav.width}`);
await p.screenshot({ path: "reports/c5-wide.png", fullPage: false });

console.log("JS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(okBtn && okDock && okWide && errs.length === 0 ? 0 : 1);

/**
 * c6-tabbar-plain-check.mjs — 复核：底部菜单改贴底通栏 + 上圆角 16px、去投影、顶部细边；宽屏左竖栏不变。
 */
import { chromium } from "playwright";

const b = await chromium.launch({ channel: "msedge" });
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
const errs = [];
p.on("pageerror", (e) => errs.push(String(e)));
const num = (v) => parseFloat(v);

await p.goto("http://localhost:5173/#/", { waitUntil: "networkidle" });
await p.waitForTimeout(700);

const dock = await p.locator(".tabbar").boundingBox();
const ds = await p.locator(".tabbar").evaluate((el) => {
  const s = getComputedStyle(el);
  return {
    rTL: s.borderTopLeftRadius, rBL: s.borderBottomLeftRadius,
    shadow: s.boxShadow, topW: s.borderTopWidth, leftW: s.borderLeftWidth,
    pos: s.position, bottom: s.bottom,
  };
});
const bottomGap = 844 - (dock.y + dock.height);
const okPlain = bottomGap <= 1 && dock.x <= 1 && num(ds.rTL) === 16 && num(ds.rBL) === 0
  && ds.shadow === "none" && num(ds.topW) > 0 && num(ds.leftW) === 0;
console.log(`[${okPlain ? "OK" : "FAIL"}] x=${dock.x.toFixed(1)} bottomGap=${bottomGap.toFixed(1)} w=${dock.width.toFixed(1)} rTL=${ds.rTL} rBL=${ds.rBL} shadow=${ds.shadow} top=${ds.topW} left=${ds.leftW}`);
await p.screenshot({ path: "reports/c6-welcome.png", fullPage: false });

await p.goto("http://localhost:5173/#/quiz", { waitUntil: "networkidle" });
await p.waitForTimeout(500);
await p.screenshot({ path: "reports/c6-quiz.png", fullPage: false });

await p.setViewportSize({ width: 1280, height: 900 });
await p.goto("http://localhost:5173/#/", { waitUntil: "networkidle" });
await p.waitForTimeout(500);
const wide = await p.locator(".tabbar").evaluate((el) => {
  const s = getComputedStyle(el);
  return { pos: s.position, dir: s.flexDirection, radius: s.borderTopLeftRadius, shadow: s.boxShadow };
});
const okWide = wide.pos === "sticky" && wide.dir === "column" && num(wide.radius) === 0 && wide.shadow === "none";
console.log(`[${okWide ? "OK" : "FAIL"}] wide pos=${wide.pos} dir=${wide.dir} radius=${wide.radius} shadow=${wide.shadow}`);
await p.screenshot({ path: "reports/c6-wide.png", fullPage: false });

console.log("JS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(okPlain && okWide && errs.length === 0 ? 0 : 1);

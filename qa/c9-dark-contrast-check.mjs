/**
 * c9-dark-contrast-check.mjs — 复核深色模式：浅色实心块已翻深底浅字，文字对比达标。
 * 模拟 prefers-color-scheme: dark；核对首页信任胶囊、问答选中项，并注入探针核对
 * pitfalls / 白纸卡 / accent 标签 / 绿徽章 / warn 等类的深色计算样式。
 */
import { chromium } from "playwright";

const b = await chromium.launch({ channel: "msedge" });
const p = await b.newPage({ viewport: { width: 390, height: 844 }, colorScheme: "dark" });
const errs = [];
p.on("pageerror", (e) => errs.push(String(e)));

function parseRgb(c) {
  const m = c.match(/[\d.]+/g);
  if (!m) return [0, 0, 0];
  return [Number(m[0]), Number(m[1]), Number(m[2])];
}
function lum(rgb) {
  const [r, g, b2] = rgb.map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b2;
}
function ratio(bg, fg) {
  const l1 = lum(parseRgb(bg)), l2 = lum(parseRgb(fg));
  const hi = Math.max(l1, l2), lo = Math.min(l1, l2);
  return (hi + 0.05) / (lo + 0.05);
}
const sample = (el) => {
  const s = getComputedStyle(el);
  return { bg: s.backgroundColor, color: s.color, border: s.borderColor };
};

// ---------- 首页：信任胶囊 ----------
await p.goto("http://localhost:5173/#/", { waitUntil: "networkidle" });
await p.waitForTimeout(600);
const trust = await p.locator(".trust .item").first().evaluate(sample);
console.log("[trust.item]", JSON.stringify(trust));
await p.screenshot({ path: "reports/c9-welcome-dark.png", fullPage: true });

// ---------- 问答：选中项 ----------
await p.goto("http://localhost:5173/#/quiz", { waitUntil: "networkidle" });
await p.waitForTimeout(500);
await p.locator(".option").first().click();
await p.waitForTimeout(300);
const sel = await p.locator(".option.sel").first().evaluate((el) => {
  const s = getComputedStyle(el);
  const title = el.querySelector(".opt-title");
  const sub = el.querySelector(".opt-sub");
  return {
    bg: s.backgroundColor,
    border: s.borderColor,
    titleColor: title ? getComputedStyle(title).color : "(none)",
    subColor: sub ? getComputedStyle(sub).color : "(none)",
  };
});
console.log("[option.sel]", JSON.stringify(sel));
if (sel.subColor !== "(none)") {
  console.log("  副标题对比度:", ratio(sel.bg, sel.subColor).toFixed(2));
}
await p.screenshot({ path: "reports/c9-quiz-dark.png", fullPage: false });

// ---------- 探针：无真实数据的浅底类，注入临时 DOM 核对深色样式 ----------
const probe = await p.evaluate(() => {
  const wrap = document.createElement("div");
  wrap.style.cssText = "padding:16px;display:flex;flex-direction:column;gap:10px;";
  const mk = (cls, html) => {
    const d = document.createElement("div");
    d.className = cls;
    d.innerHTML = html || "探针文字 Probe text";
    wrap.appendChild(d);
    return d;
  };
  mk("pitfall", '<span class="ico">!</span> 探针 pitfall 文字');
  const paper = mk("paper", '<div class="pt">PROBE</div><div class="ph">探针样板卡标题</div><div class="pl"></div><div class="pbox"></div>');
  mk("pdf-sheet", '<div class="ps-title">探针 PDF 样板</div><div class="ps-line"></div>');
  mk("tag accent", "探针 accent 标签");
  mk("badge-green", "探针绿徽章");
  mk("warn", "探针 warn 提示");
  document.body.appendChild(wrap);
  const out = {};
  const grab = (root, cls) => {
    const el = root.querySelector("." + cls) || wrap.querySelector("." + cls);
    if (!el) return;
    const s = getComputedStyle(el);
    out[cls] = { bg: s.backgroundColor, color: s.color };
  };
  ["pitfall", "paper", "pdf-sheet", "tag", "badge-green", "warn"].forEach((c) => grab(wrap, c));
  const pl = wrap.querySelector(".paper .pl");
  if (pl) out["paper .pl"] = { bg: getComputedStyle(pl).backgroundColor };
  wrap.scrollIntoView();
  return out;
});
console.log("[probe]", JSON.stringify(probe, null, 0));
await p.waitForTimeout(200);
await p.screenshot({ path: "reports/c9-probe-dark.png", fullPage: false });

// ---------- 浅色回归：确认浅色主题下胶囊仍是近白底深字 ----------
const p2 = await b.newPage({ viewport: { width: 390, height: 844 }, colorScheme: "light" });
await p2.goto("http://localhost:5173/#/", { waitUntil: "networkidle" });
await p2.waitForTimeout(500);
const trustLight = await p2.locator(".trust .item").first().evaluate(sample);
console.log("[trust.light]", JSON.stringify(trustLight));
await p2.screenshot({ path: "reports/c9-welcome-light.png", fullPage: false });

console.log("JS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(errs.length === 0 ? 0 : 1);

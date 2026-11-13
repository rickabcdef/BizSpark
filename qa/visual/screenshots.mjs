/**
 * screenshots.mjs — H-05 视觉回归 / H-06 商店截图（负责人：H）
 *
 * 用真前端 + 真 sidecar 渲染 9 页，两种语言各 9 张 + 2 张总览图。
 *   qa/reports/visual/en/01..09.png   （英文，同时拷进 qa/store-assets/screenshots/en/）
 *   qa/reports/visual/cn/01..09.png   （中文自检包用；**不进商店素材**，F14.3）
 *   qa/reports/visual/overview-en.png / overview-cn.png
 *
 * 每页同时记录版式指标（是否溢出、卡片数），写 qa/reports/visual/metrics.json，
 * 与 ui/ 稿的尺寸（1440×900）逐页对照，偏差靠人工看图确认（≤2px 观感）。
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { chromium } from "playwright";
import { startBridge, REPO } from "../e2e/bridge_server.mjs";

const DIST = path.join(REPO, "apps", "web", "dist");
const OUT = path.join(REPO, "qa", "reports", "visual");
const STORE = path.join(REPO, "qa", "store-assets", "screenshots", "en");

const PAGES = [
  { n: "01", name: "welcome", hash: "/" },
  { n: "02", name: "quiz", hash: "/quiz" },
  { n: "03", name: "results", hash: "/results" },
  { n: "04", name: "detail", hash: null },   // 需要先拿到 id
  { n: "05", name: "export", hash: "/export" },
  { n: "06", name: "saved", hash: "/saved" },
  { n: "07", name: "activate", hash: "/activate" },
  { n: "08", name: "library", hash: "/library" },
  { n: "09", name: "settings", hash: "/settings" },
];

const ANSWERS = { country: "US", capital: "500-2k", hours: "<10", assets: ["laptop", "local_network"], risk: "small_loss" };

async function seed(sidecar) {
  await sidecar.call("save_answers", { answers: ANSWERS });
  const d = await sidecar.call("diagnose", { answers: ANSWERS });
  const ideas = d?.data?.ideas || [];
  for (const i of ideas) await sidecar.call("save_idea", { id: i.id });
  return ideas;
}

async function contactSheet(dir, files, out, title) {
  const cells = files.map((f, i) => `
    <figure><img src="file:///${path.join(dir, f).replace(/\\/g, "/")}" />
      <figcaption>${String(i + 1).padStart(2, "0")} · ${PAGES[i].name}</figcaption></figure>`).join("");
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    body{margin:0;background:#0E1A24;color:#DCE7F0;font-family:system-ui,"Segoe UI",sans-serif;padding:28px}
    h1{font-size:20px;margin:0 0 18px;letter-spacing:.2px}
    .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
    figure{margin:0}
    img{width:100%;display:block;border-radius:8px;border:1px solid rgba(255,255,255,.12)}
    figcaption{font-size:11px;color:#8CA3B7;margin-top:6px;letter-spacing:.6px;text-transform:uppercase}
  </style></head><body><h1>${title}</h1><div class="grid">${cells}</div></body></html>`;
  const file = path.join(dir, "_sheet.html");
  fs.writeFileSync(file, html, "utf8");
  return file;
}

async function shoot(browser, locale, subdir) {
  const appData = fs.mkdtempSync(path.join(os.tmpdir(), "bz_shot_"));
  const dialogDir = fs.mkdtempSync(path.join(os.tmpdir(), "bz_dlg_"));
  const bridge = await startBridge({ distDir: DIST, appData, locale, dialogDir });
  const ideas = await seed(bridge.sidecar);
  const dir = path.join(OUT, subdir);
  fs.mkdirSync(dir, { recursive: true });

  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const metrics = [];
  const files = [];

  for (const p of PAGES) {
    const hash = p.name === "detail" ? `/detail/${ideas[0]?.id || ""}` : p.hash;
    await page.goto(bridge.base + "/#" + hash, { waitUntil: "networkidle" });
    await page.waitForTimeout(p.name === "export" ? 1200 : 500);
    const m = await page.evaluate(() => ({
      overflowX: document.documentElement.scrollWidth - window.innerWidth,
      overflowY: document.documentElement.scrollHeight - window.innerHeight,
      cards: document.querySelectorAll(".card").length,
      scrollH: document.documentElement.scrollHeight,
    }));
    const file = path.join(dir, `${p.n}-${p.name}.png`);
    await page.screenshot({ path: file, fullPage: false });
    files.push(path.basename(file));
    metrics.push({ page: p.name, locale, ...m });
    console.log(`  ${locale} ${p.n} ${p.name} 溢出 ${m.overflowX}px 卡 ${m.cards}`);
  }

  // 总览图（3×3 联系表）
  const sheet = await contactSheet(dir, files, null, `BizSpark ${locale === "zh-CN" ? "中文自检版" : "English"} · 9 屏总览`);
  const sheetPage = await ctx.newPage();
  await sheetPage.setViewportSize({ width: 1600, height: 1100 });
  await sheetPage.goto("file:///" + sheet.replace(/\\/g, "/"));
  await sheetPage.waitForTimeout(700);
  await sheetPage.screenshot({ path: path.join(OUT, `overview-${locale === "zh-CN" ? "cn" : "en"}.png`), fullPage: true });
  fs.removeSync?.(sheet);
  try { fs.unlinkSync(sheet); } catch {}

  await ctx.close();
  await bridge.close();
  fs.rmSync(appData, { recursive: true, force: true });
  fs.rmSync(dialogDir, { recursive: true, force: true });
  return { dir, files, metrics };
}

const browser = await chromium.launch({ channel: "msedge" });
try {
  console.log("== 英文 9 屏 ==");
  const en = await shoot(browser, "en-US", "en");
  console.log("== 中文 9 屏（自检包，不进商店素材） ==");
  const cn = await shoot(browser, "zh-CN", "cn");

  // 商店素材只放英文
  fs.mkdirSync(STORE, { recursive: true });
  for (const f of en.files) fs.copyFileSync(path.join(en.dir, f), path.join(STORE, f));
  fs.copyFileSync(path.join(OUT, "overview-en.png"), path.join(STORE, "overview-en.png"));

  const all = [...en.metrics, ...cn.metrics];
  fs.writeFileSync(path.join(OUT, "metrics.json"), JSON.stringify({ pages: all }, null, 2) + "\n", "utf8");
  const bad = all.filter((m) => m.overflowX > 1);
  console.log(`\n导出完成：${en.files.length}+${cn.files.length} 张 + 2 张总览`);
  console.log(bad.length ? `⚠️ 有 ${bad.length} 屏横向溢出：${JSON.stringify(bad)}` : "✅ 9 屏均无横向溢出");
} finally {
  await browser.close();
}

/**
 * compare.mjs — H-05 视觉回归：基线截图（负责人：H）
 *
 * 只做一件事：把「基线」的 9 张静态 HTML 用同一视口（1440×900）截下来，
 * 落到 qa/reports/visual/baseline-en/，供 compare.py 与「实现」截图逐屏对比。
 *
 * 基线目录可用环境变量覆盖：BIZSPARK_BASELINE=<...>/en/html
 * 用法：node qa/visual/compare.mjs && python qa/visual/compare.py
 */

import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";
import { REPO } from "../e2e/bridge_server.mjs";

const BASELINE =
  process.env.BIZSPARK_BASELINE ||
  "F:/迅雷下载/BizSpark_中英双版_UI与HTML_202611141112/en/html";
const OUT = path.join(REPO, "qa", "reports", "visual", "baseline-en");

// 文件名沿用基线自己的命名（08 的 HTML 文件名是 08-update.html，内容其实是 Library）
const PAGES = [
  ["01", "welcome", "01-welcome.html"],
  ["02", "quiz", "02-quiz.html"],
  ["03", "results", "03-results.html"],
  ["04", "detail", "04-detail.html"],
  ["05", "export", "05-export.html"],
  ["06", "saved", "06-saved.html"],
  ["07", "activate", "07-activate.html"],
  ["08", "library", "08-update.html"],
  ["09", "settings", "09-settings.html"],
];

if (!fs.existsSync(BASELINE)) {
  console.error(`基线目录不存在：${BASELINE}`);
  process.exit(2);
}
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ channel: "msedge" });
try {
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const page = await ctx.newPage();
  for (const [n, name, file] of PAGES) {
    const abs = path.join(BASELINE, file);
    if (!fs.existsSync(abs)) {
      console.log(`  ✗ ${n} ${name} 基线缺失：${file}`);
      continue;
    }
    await page.goto("file:///" + abs.replace(/\\/g, "/"), { waitUntil: "load" });
    await page.waitForTimeout(250);
    await page.screenshot({ path: path.join(OUT, `${n}-${name}.png`), fullPage: false });
    console.log(`  ✓ ${n} ${name}`);
  }
  await ctx.close();
} finally {
  await browser.close();
}
console.log(`\n基线 9 屏已截到 ${path.relative(REPO, OUT)}`);

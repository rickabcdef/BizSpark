/**
 * c11-export-open-check.mjs — 复核导出页：桌面壳 mock 下文件名可点、文件夹按钮出现；
 * 浏览器分支不报错。核对链接/提示渲染与 JS 错误。
 */
import { chromium } from "playwright";

const b = await chromium.launch({ channel: "msedge" });
const errs = [];

// 桌面壳分支：mock Tauri 运行时 + 导出数据
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
p.on("pageerror", (e) => errs.push(String(e)));
await p.addInitScript(() => {
  window.__TAURI_INTERNALS__ = {
    invoke: async (cmd, args) => {
      if (cmd === "handle_core_cmd" && args && args.cmd === "export_plan") {
        return {
          ok: true,
          data: {
            file_name: "BizSpark-Plan-bs-svc-review-reply-003.pdf",
            path: "C:/Users/Administrator/Documents/BizSpark/BizSpark-Plan-bs-svc-review-reply-003.pdf",
            bytes: 3072,
            pages: 1,
          },
        };
      }
      return { ok: true, data: null };
    },
  };
});
await p.goto("http://localhost:5173/#/export", { waitUntil: "networkidle" });
await p.waitForTimeout(500);

const link = await p.locator(".file-name-link").count();
const folderBtn = await p.locator("button.btn-secondary").count();
const hint = await p.locator(".file-hint").count();
const linkText = await p.locator(".file-name-link").first().textContent().catch(() => "(none)");
console.log("[desktop mock] 可点文件名:", link, "| 文件夹按钮:", folderBtn, "| web提示:", hint);
console.log("  文件名:", (linkText || "").trim());
await p.screenshot({ path: "reports/c11-export-desktop.png", fullPage: false });

// 浏览器/dev 降级分支：有导出数据，但 BIZSPARK_DEV=true → 纯文本文件名 + 轻提示，无文件夹按钮
const p2 = await b.newPage({ viewport: { width: 390, height: 844 } });
p2.on("pageerror", (e) => errs.push(String(e)));
await p2.addInitScript(() => {
  window.BIZSPARK_DEV = true;
  window.__TAURI_INTERNALS__ = {
    invoke: async (cmd, args) => {
      if (cmd === "handle_core_cmd" && args && args.cmd === "export_plan") {
        return { ok: true, data: { file_name: "BizSpark-Plan-bs-svc-review-reply-003.pdf", path: "", bytes: 3072, pages: 1 } };
      }
      return { ok: true, data: null };
    },
  };
});
await p2.goto("http://localhost:5173/#/export", { waitUntil: "networkidle" });
await p2.waitForTimeout(400);
const plain = await p2.locator(".file-name:not(.file-name-link)").count();
const hint2 = await p2.locator(".file-hint").count();
const folder2 = await p2.locator("button.btn-secondary").count();
console.log("[dev 降级] 纯文本文件名:", plain, "| web提示:", hint2, "| 文件夹按钮:", folder2);
await p2.screenshot({ path: "reports/c11-export-web.png", fullPage: false });

console.log("JS 报错:", errs.length ? errs : "无");
await b.close();
process.exit(errs.length === 0 ? 0 : 1);

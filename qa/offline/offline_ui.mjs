/**
 * offline_ui.mjs — H-04 场景 D5（负责人：H）
 *
 * 前端侧离线演练：sidecar 注入 socket 桩（真零出网），真前端走完
 * welcome → quiz → results → detail → export → saved，
 * 断言：无 pageerror、无 E_* 错误冒泡到界面、导出真出 PDF、
 *       全部网络请求只打到 127.0.0.1 桥接（无任何外部主机）、socket 零尝试。
 *
 * 输出：qa/reports/offline-drill-ui.json
 * 用法：node qa/offline/offline_ui.mjs
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { chromium } from "playwright";
import { startBridge, REPO } from "../e2e/bridge_server.mjs";

const REPORT = path.join(REPO, "qa", "reports", "offline-drill-ui.json");
const LOCALES = JSON.parse(
  fs.readFileSync(path.join(REPO, "apps", "web", "src", "locales", "en-US.json"), "utf8"),
);
const t = (k) => LOCALES[k] || k;

function mkAppData(tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `bz-off-${tag}-`));
  return dir;
}

function socketStubEnv(guard) {
  fs.writeFileSync(
    path.join(guard, "sitecustomize.py"),
    [
      "import socket, json, os",
      "class _Blocked(RuntimeError):",
      "    pass",
      "_LOG = os.path.join(os.environ['BIZSPARK_APP_DATA'], 'blocked.jsonl')",
      "def _deny(*a, **k):",
      "    with open(_LOG, 'a', encoding='utf-8') as f:",
      "        f.write(json.dumps([str(x) for x in a]) + '\\n')",
      "    raise _Blocked('network disabled by QA (H-04)')",
      "socket.socket = _deny",
      "socket.create_connection = _deny",
      "socket.getaddrinfo = _deny",
    ].join("\n"),
    "utf8",
  );
  return { PYTHONPATH: guard };
}

async function withPage(browser, fn) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const externalRequests = [];
  const failedUrls = [];
  page.on("pageerror", (e) => pageErrors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });
  page.on("response", (r) => {
    if (r.status() >= 400) failedUrls.push(r.url());
  });
  page.on("request", (r) => {
    const u = new URL(r.url());
    if (u.hostname !== "127.0.0.1") externalRequests.push(r.url());
  });
  try {
    await fn(page);
  } finally {
    await context.close();
  }
  return { pageErrors, consoleErrors, externalRequests, failedUrls };
}

const goto = async (page, base, hash) => {
  await page.goto(base + "/" + (hash ? "#" + hash : ""), { waitUntil: "networkidle" });
  await page.waitForTimeout(120);
};

/** 依次回答 5 题（与 ui_checks.mjs 同一走法），最后停在 Results。 */
async function answerQuiz(page, base, picks = [0, 1, 0, [0, 2, 4], 0]) {
  await goto(page, base, "/quiz");
  for (let i = 0; i < 5; i++) {
    const opts = page.locator(".opt");
    await opts.first().waitFor({ state: "visible" });
    if (i === 3) {
      for (const k of picks[3]) await opts.nth(k).click();
      await page.getByRole("button", { name: t("quiz.done") }).click();
    } else {
      await opts.nth(picks[i]).click();
    }
    await page.waitForTimeout(520); // 0.35s 自动进题 + 余量
  }
  await page.waitForTimeout(600); // 等 diagnose
}

async function main() {
  const appData = mkAppData("appdata");
  const exportDir = mkAppData("export");
  const guard = mkAppData("guard");

  const bridge = await startBridge({
    appData,
    locale: "en-US",
    pricing: null,
    dialogDir: exportDir,
    sidecarEnv: socketStubEnv(guard),
  });

  const result = {
    scenario: "D5 frontend offline drill (socket stubbed sidecar)",
    steps: [],
    pageErrors: [],
    consoleErrors: [],
    externalRequests: [],
    socketBlocked: 0,
    exportPdf: null,
    status: "FAIL",
  };

  const browser = await chromium.launch({ channel: "msedge" });
  try {
    const obs = await withPage(browser, async (page) => {
      // 1) welcome 首屏
      await page.goto(bridge.base + "/", { waitUntil: "load" });
      await page.locator(".hero .btn-primary").waitFor({ timeout: 15000 });
      result.steps.push({ step: "welcome", ok: true });

      // 2) 5 题问答 → Results
      await answerQuiz(page, bridge.base);
      await page.locator(".card-cta").first().waitFor({ timeout: 15000 });
      const cards = await page.locator(".idea-card, .card-cta").count();
      result.steps.push({ step: "results", ok: cards >= 3, cards });

      // 3) 详情
      await page.locator(".card-cta").first().click();
      await page.locator(".detail-wrap").waitFor({ timeout: 15000 });
      const ideaId = (page.url().match(/#\/detail\/([^/?#]+)/) || [])[1] || "";
      result.steps.push({ step: "detail", ok: Boolean(ideaId), ideaId });

      // 4) 导出（Export 页 onMounted 自动 export_plan，路径由 dialogDir 补）
      //    已知缺陷（B-09 候选）：Detail 的 CTA router.push('/export') 不带 ideaId，
      //    Export.vue 读 history.state?.ideaId 拿到空串 → 导出失败、无文件行。
      //    演练记缺陷后，用注入 history.state 的方式继续验证导出链路本身离线可用。
      await page.getByRole("button", { name: t("detail.cta_export") }).click();
      let exported = false;
      try {
        await page.locator(".file-row").waitFor({ timeout: 4000 });
        exported = true;
      } catch {
        result.defects = result.defects || [];
        result.defects.push(
          "B-09 候选（新发现）：Detail.vue 跳 /export 未携带 ideaId，" +
          "Export.vue 的 history.state?.ideaId 为空 → 完成页不出文件行（导出静默失败）",
        );
        await page.evaluate((id) => {
          history.pushState({ ideaId: id }, "", "#/export");
          window.dispatchEvent(new PopStateEvent("popstate"));
        }, ideaId);
        await page.waitForTimeout(300);
        await page.reload({ waitUntil: "networkidle" }); // reload 让 onMounted 重新拿 state
        await page.waitForTimeout(300);
        // pushState 的 state 在 reload 后保留（同源同文档历史项）
        await page.locator(".file-row").waitFor({ timeout: 20000 });
        exported = true;
      }
      const pdfs = fs.existsSync(exportDir)
        ? fs.readdirSync(exportDir).filter((f) => f.endsWith(".pdf"))
        : [];
      result.exportPdf = pdfs[0] || null;
      result.steps.push({ step: "export", ok: exported && pdfs.length > 0, pdf: result.exportPdf });

      // 5) Saved 页可开（离线读存档）
      await goto(page, bridge.base, "/saved");
      await page.waitForTimeout(400);
      const body = await page.locator("body").innerText();
      result.steps.push({ step: "saved", ok: !/E_[A-Z_]+/.test(body) });
    });

    result.pageErrors = obs.pageErrors;
    // 浏览器自动请求 /favicon.ico 在 dist 里不存在 → 404 噪音（Tauri 壳不走 HTTP，非缺陷）；
    // 其余 4xx 一律视为异常
    const nonFaviconFailures = obs.failedUrls.filter((u) => !/favicon/i.test(u));
    result.failed4xx = nonFaviconFailures;
    result.consoleErrors = obs.consoleErrors.filter(
      (x) => !(/failed to load resource/i.test(x) && nonFaviconFailures.length === 0),
    );
    result.externalRequests = obs.externalRequests;
  } finally {
    await browser.close();
    await bridge.close();
  }

  const blockedLog = path.join(appData, "blocked.jsonl");
  result.socketBlocked = fs.existsSync(blockedLog)
    ? fs.readFileSync(blockedLog, "utf8").trim().split("\n").filter(Boolean).length
    : 0;

  const ok =
    result.steps.every((s) => s.ok) &&
    result.pageErrors.length === 0 &&
    result.consoleErrors.length === 0 &&
    result.externalRequests.length === 0 &&
    result.socketBlocked === 0;
  result.status = ok ? "PASS" : "FAIL";

  fs.mkdirSync(path.dirname(REPORT), { recursive: true });
  fs.writeFileSync(REPORT, JSON.stringify(result, null, 2));
  console.log(`D5 前端离线演练：${result.status}  (steps=${result.steps.length}, ` +
    `blocked=${result.socketBlocked}, external=${result.externalRequests.length}, ` +
    `pdf=${result.exportPdf || "无"})`);
  if (!ok) {
    console.log(JSON.stringify(result, null, 2));
    for (const d of [appData, exportDir, guard]) fs.rmSync(d, { recursive: true, force: true });
    process.exitCode = 1;
    return;
  }
  for (const d of [appData, exportDir, guard]) fs.rmSync(d, { recursive: true, force: true });
}

main().catch((e) => {
  console.error("D5 crashed:", e);
  process.exit(2);
});

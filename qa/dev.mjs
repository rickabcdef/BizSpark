/**
 * dev.mjs — 老板的「固定网址 + 改完即见」开发常驻服务（PM 2026-11-13）
 *
 * 与 play.mjs 的区别：
 *   play.mjs —— 一次性试玩，随机端口，改代码要重启
 *   dev.mjs  —— 常驻开发，**固定端口 5180**，改代码自动生效：
 *                · 前端（.vue/.ts/.css/locales）→ Vite HMR，页面不刷新即变
 *                · 引擎（apps/core 下 .py / data/*.json）→ sidecar 自动重启，浏览器自动刷新
 *
 * 用法：
 *   cd qa && node dev.mjs           # 中文版（默认），http://127.0.0.1:5180
 *   node dev.mjs en                 # 英文版
 *   node dev.mjs zh 5180            # 指定语言与端口
 *
 * 关闭：Ctrl+C（会同时结束 vite 与 python 子进程）
 */
import { startBridge, REPO } from "./e2e/bridge_server.mjs";
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const argLocale = String(process.argv[2] || "zh");
const locale = argLocale === "en" || argLocale === "en-US" ? "en-US" : "zh-CN";
const WEB_PORT = Number(process.argv[3] || 5180);

// 导出目录：桌面上固定的试玩导出夹（PDF/CSV 真实落盘）
const exportDir = path.join(os.homedir(), "Desktop", "BizSpark-试玩导出");
fs.mkdirSync(exportDir, { recursive: true });

// 固定 appdata（不用时间戳）：刷新/重启后数据还在，方便反复测「已存点子 / 授权状态」
const appData = path.join(os.tmpdir(), "BizSpark-dev-data");
fs.mkdirSync(appData, { recursive: true });

const log = (...a) => console.log("[dev]", ...a);

// ---------- 1) 引擎（真 sidecar + IPC） ----------
const bridge = await startBridge({
  appData,
  locale,
  dialogDir: exportDir,
  sidecarEnv: { BIZSPARK_LOCALE: locale },
});
log(`sidecar ready · appdata=${appData}`);

// ---------- 2) 前端（Vite 热更新，端口固定） ----------
const viteBin = path.join(REPO, "apps", "web", "node_modules", "vite", "bin", "vite.js");
if (!fs.existsSync(viteBin)) {
  console.error("[dev] 找不到 vite，请先在 apps/web 下执行 npm install");
  process.exit(1);
}
const vite = spawn(
  process.execPath,
  [viteBin, "--config", "vite.dev.config.mjs", "--port", String(WEB_PORT), "--strictPort"],
  {
    cwd: path.join(REPO, "apps", "web"),
    env: {
      ...process.env,
      BIZSPARK_DEV_IPC: bridge.base,
      BIZSPARK_DEV_PORT: String(WEB_PORT),
      BIZSPARK_LOCALE: locale,
    },
    stdio: ["ignore", "pipe", "pipe"],
  },
);
vite.stdout.on("data", (d) => process.stdout.write(d.toString().replace(/^/gm, "[vite] ")));
vite.stderr.on("data", (d) => process.stderr.write(d.toString().replace(/^/gm, "[vite] ")));
vite.on("exit", (code) => {
  if (!closing) {
    console.error(`[dev] vite 退出（code=${code}），端口 ${WEB_PORT} 可能被占用`);
    shutdown(code || 1);
  }
});

// ---------- 3) 引擎热重载：apps/core 变动 → 重启 sidecar ----------
let timer = null;
let restarting = false;
let queued = false;

async function doRestart(reason) {
  if (restarting) {
    queued = true;
    return;
  }
  restarting = true;
  log(`检测到改动（${reason}）→ 重启引擎…`);
  const r = await bridge.restartSidecar();
  restarting = false;
  if (r.ok) log("引擎已重启，浏览器会自动刷新");
  else log(`引擎重启失败（页面底部会红条提示）：${r.error}`);
  if (queued) {
    queued = false;
    setTimeout(() => doRestart("连续保存"), 200);
  }
}

const IGNORE = /(__pycache__|\.pyc$|\.pyo$|[\\/]tests[\\/]|[\\/]\.git[\\/])/;
const WATCH_ROOTS = [path.join(REPO, "apps", "core"), path.join(REPO, "config")];

for (const root of WATCH_ROOTS) {
  if (!fs.existsSync(root)) continue;
  try {
    fs.watch(root, { recursive: true }, (_ev, file) => {
      if (!file) return;
      const p = path.join(root, String(file));
      if (IGNORE.test(p)) return;
      if (!/\.(py|json)$/i.test(p)) return;
      clearTimeout(timer);
      timer = setTimeout(() => doRestart(path.relative(REPO, p)), 450);
    });
  } catch (e) {
    log(`监听 ${root} 失败：${e.message}`);
  }
}

// ---------- 4) 收尾 ----------
let closing = false;
async function shutdown(code = 0) {
  if (closing) {
    process.exit(code);
  }
  closing = true;
  log("正在退出…");
  try {
    vite.kill();
  } catch {}
  await bridge.close().catch(() => {});
  fs.writeFileSync(path.join(REPO, "qa", ".dev-url"), "offline\n", "utf8");
  process.exit(code);
}
process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));

// 写给别的工具/我自己读的地址文件
const url = `http://127.0.0.1:${WEB_PORT}`;
try {
  fs.writeFileSync(path.join(REPO, "qa", ".dev-url"), url + "\n", "utf8");
} catch {}

console.log("");
console.log("==============================================================");
console.log(`  BizSpark 开发常驻服务（${locale === "zh-CN" ? "中文" : "English"}）`);
console.log(`  固定网址  ${url}`);
console.log("");
console.log("  改前端（.vue/.ts/.css/语言包）→ 页面热更新，不刷新");
console.log("  改引擎（apps/core 下 .py / 数据 json）→ 引擎重启 + 页面自动刷新");
console.log(`  导出的 PDF/CSV → ${exportDir}`);
console.log(`  本地数据（存档/授权/设置）→ ${appData}`);
console.log("");
console.log("  这个终端窗口不要关；关掉就等于停服务。Ctrl+C 停止。");
console.log("==============================================================");
console.log("");

setInterval(() => {}, 1 << 30);

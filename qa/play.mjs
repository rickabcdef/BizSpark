/**
 * play.mjs — 老板试玩入口（PM 2026-11-13）
 *
 * 用途：不打包、不装 Rust，直接在浏览器里跑「真前端 + 真 Python 引擎」的完整软件，
 *      与 Windows 壳里的体验一致（仅"系统另存为对话框"由本地目录代替）。
 *
 * 用法：
 *   cd qa && node play.mjs           # 中文版（默认）
 *   node play.mjs en                 # 英文版
 *
 * 玩完在终端按 Ctrl+C 即退出，临时数据自动清掉（退出前会提示导出文件在哪）。
 */
import { startBridge, REPO } from "./e2e/bridge_server.mjs";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const locale = process.argv[2] === "en" ? "en-US" : "zh-CN";

// 导出目录：桌面上的 BizSpark-试玩导出（PDF/CSV 真实落在这里，方便你翻看）
const exportDir = path.join(os.homedir(), "Desktop", "BizSpark-试玩导出");
fs.mkdirSync(exportDir, { recursive: true });

// 独立 appdata：和 QA/正式环境完全隔离，随便玩
const appData = path.join(os.tmpdir(), `BizSpark-play-${Date.now()}`);
fs.mkdirSync(appData, { recursive: true });

const bridge = await startBridge({ appData, locale, dialogDir: exportDir,
  // 中文包：sidecar 也要知道 locale（引擎文案中文镜像 + 内容覆盖 zh_v1.json）
  sidecarEnv: { BIZSPARK_LOCALE: locale } });

console.log("");
console.log("==============================================");
console.log(`  BizSpark 试玩版已启动（${locale === "zh-CN" ? "中文" : "English"}）`);
console.log(`  在浏览器打开: ${bridge.base}`);
console.log(`  导出的 PDF/CSV 落在: ${exportDir}`);
console.log("  本地数据目录（玩熟后可删）:");
console.log(`    ${appData}`);
console.log("  按 Ctrl+C 退出并清理");
console.log("==============================================");
console.log("");

let closing = false;
async function shutdown() {
  if (closing) return;
  closing = true;
  console.log("\n[play] 正在退出…");
  await bridge.close().catch(() => {});
  try {
    fs.rmSync(appData, { recursive: true, force: true });
    console.log("[play] 临时数据已清理。导出文件保留在 " + exportDir);
  } catch {
    console.log("[play] 临时目录下次开机可手动删: " + appData);
  }
  process.exit(0);
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
// 保持常驻
setInterval(() => {}, 1 << 30);

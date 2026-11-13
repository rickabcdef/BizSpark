/**
 * bridge_server.mjs — H-02（负责人：H）
 *
 * 把「真前端 + 真 sidecar」接起来跑 E2E：
 *   ┌─ Edge(Playwright) ─┐   POST /__ipc   ┌─ 本进程 ─┐   JSONL   ┌─ python main.py ─┐
 *   │  dist/ 里的 9 页   │ ─────────────► │ 静态服务 │ ────────► │ 真实引擎/状态/导出 │
 *   └────────────────────┘                └──────────┘           └──────────────────┘
 *
 * 注入物（只注入 Tauri 壳本该提供的东西，不伪造业务数据）：
 *   window.__TAURI_INTERNALS__.invoke —— 转发到 /__ipc
 *   window.BIZSPARK_BUILD.locale      —— A 的 build-mode 注入等价物
 *   window.BIZSPARK_PRICING           —— A 的 inject-pricing 注入等价物
 *
 * 用法：import { startBridge } from "./bridge_server.mjs"
 */

import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const REPO = path.resolve(HERE, "..", "..");
const MAIN = path.join(REPO, "apps", "core", "main.py");
const PY = process.env.BIZSPARK_PY || "python";

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
  ".ico": "image/x-icon",
};

class Sidecar {
  constructor(appData, env = {}) {
    this.appData = appData;
    this.env = { ...process.env, BIZSPARK_APP_DATA: appData, PYTHONIOENCODING: "utf-8", ...env };
    this.seq = 0;
    this.pending = new Map();
    this.ready = null;
  }

  async start() {
    this.proc = spawn(PY, [MAIN], { cwd: REPO, env: this.env, stdio: ["pipe", "pipe", "pipe"] });
    this.proc.stderr.on("data", () => {});
    let buf = "";
    this.proc.stdout.on("data", (chunk) => {
      buf += chunk.toString("utf8");
      let nl;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (!line) continue;
        let msg;
        try {
          msg = JSON.parse(line);
        } catch {
          continue;
        }
        if (msg.req_id == null) {
          if (msg.data?.event === "ready") this.ready = msg.data;
          continue;
        }
        const res = this.pending.get(msg.req_id);
        if (res) {
          this.pending.delete(msg.req_id);
          res(msg);
        }
      }
    });
    const t0 = Date.now();
    while (!this.ready && Date.now() - t0 < 20000) await new Promise((r) => setTimeout(r, 30));
    if (!this.ready) throw new Error("sidecar 未 ready");
    return this.ready;
  }

  call(cmd, payload = {}, timeout = 60000) {
    return new Promise((resolve) => {
      const reqId = `h${++this.seq}`;
      const timer = setTimeout(() => {
        this.pending.delete(reqId);
        resolve({ req_id: reqId, ok: false, error: { code: "E_TIMEOUT", message: "timeout", recoverable: true } });
      }, timeout);
      this.pending.set(reqId, (msg) => {
        clearTimeout(timer);
        resolve(msg);
      });
      this.proc.stdin.write(JSON.stringify({ req_id: reqId, cmd, payload }) + "\n");
    });
  }

  stop() {
    try {
      this.proc.stdin.end();
    } catch {}
    try {
      this.proc.kill();
    } catch {}
  }
}

export async function startBridge(opts = {}) {
  const {
    distDir = path.join(REPO, "apps", "web", "dist"),
    appData,
    locale = "en-US",
    pricing = null,
    failMode = null, // "core_down" | null
    dialogDir = null, // 模拟 A 的系统另存为：export_plan 传空 path 时补一个可用路径
    sidecarEnv = null, // 透传给 sidecar 的额外环境变量（H-04 离线演练注入 socket 桩）
  } = opts;

  const sidecar = failMode ? null : new Sidecar(appData, sidecarEnv || {});
  if (sidecar) await sidecar.start();

  const injected = `<script>
  window.__TAURI_INTERNALS__ = { invoke: async (name, args) => {
    if (name !== "handle_core_cmd") return null;
    const res = await fetch("/__ipc", { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ cmd: args.cmd, payload: args.payload }) });
    return await res.json();
  }};
  window.BIZSPARK_BUILD = { locale: ${JSON.stringify(locale)} };
  window.BIZSPARK_PRICING = ${JSON.stringify(pricing)};
  </script>`;

  const server = http.createServer((req, res) => {
    const url = new URL(req.url, "http://127.0.0.1");
    if (req.method === "POST" && url.pathname === "/__ipc") {
      let body = "";
      req.on("data", (c) => (body += c));
      req.on("end", async () => {
        let cmd = "", payload = {};
        try {
          const parsed = JSON.parse(body || "{}");
          cmd = parsed.cmd || "";
          payload = parsed.payload || {};
        } catch {}
        if (failMode === "core_down") {
          res.writeHead(200, { "content-type": "application/json" });
          res.end(JSON.stringify({ ok: false, error: { code: "E_CORE_DOWN", message: "core down", recoverable: true } }));
          return;
        }
        if (dialogDir && cmd === "export_plan" && !payload.path) {
          const safe = String(payload.id || "plan").replace(/[^\w.-]/g, "");
          payload = { ...payload, path: path.join(dialogDir, `BizSpark-Plan-${safe}.pdf`) };
        }
        const out = await sidecar.call(cmd, payload);
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify(out));
      });
      return;
    }

    let rel = decodeURIComponent(url.pathname);
    if (rel === "/" || !path.extname(rel)) rel = "/index.html";
    const file = path.join(distDir, rel);
    if (!file.startsWith(distDir) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404).end("not found");
      return;
    }
    let data = fs.readFileSync(file);
    if (rel === "/index.html") {
      data = Buffer.from(
        data.toString("utf8").replace("</head>", `${injected}</head>`),
        "utf8",
      );
    }
    res.writeHead(200, { "content-type": MIME[path.extname(file)] || "application/octet-stream" });
    res.end(data);
  });

  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const port = server.address().port;
  return {
    base: `http://127.0.0.1:${port}`,
    sidecar,
    async close() {
      sidecar?.stop();
      await new Promise((r) => server.close(r));
    },
  };
}

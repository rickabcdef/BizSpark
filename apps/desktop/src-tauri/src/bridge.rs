//! A-04 IPC 桥（负责人：A）+ A-03 sidecar 生命周期
//!
//! 职责（§2.2 / §2.4 / §7）：
//! - WebView ⇄ sidecar 的 JSONL 双向转发，带 req_id 匹配
//! - sidecar 启动一次、常驻、崩溃自动重启 1 次
//! - Rust 层只转发，不做业务判断，不改写 payload
//!
//! 前端唯一出口是 apps/web/src/bridge/cmd.ts（B 负责），经
//! invoke("handle_core_cmd", { reqId, cmd, payload }) 到达这里。

use once_cell::sync::Lazy;
use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter, Manager, State};

/// 运行中的 sidecar 子进程句柄
static SIDECAR: Lazy<Mutex<Option<Child>>> = Lazy::new(|| Mutex::new(None));
/// 崩溃重启计数（A-03：仅自动重启 1 次）
static RESTARTS: Lazy<Mutex<u32>> = Lazy::new(|| Mutex::new(0));
/// sidecar 的 stdin 写句柄（转发请求用）
static SIDECAR_STDIN: Lazy<Arc<Mutex<Option<std::process::ChildStdin>>>> =
    Lazy::new(|| Arc::new(Mutex::new(None)));

#[derive(Default)]
pub struct BridgeState;

/// 前端请求结构（§2.4 协议）
#[derive(Deserialize)]
pub struct CoreRequest {
    pub req_id: String,
    pub cmd: String,
    #[serde(default)]
    pub payload: serde_json::Value,
}

/// sidecar 响应结构（§2.4 协议）：ok=true 带 data，ok=false 带 error.code
#[derive(Serialize, Clone)]
pub struct CoreResponse {
    pub req_id: String,
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<serde_json::Value>,
}

/// 拼出 sidecar 可执行文件名（externalBin 随平台带后缀，dev 阶段从 binaries/ 找）
fn sidecar_path(app: &AppHandle) -> Result<std::path::PathBuf, String> {
    let name = if cfg!(windows) {
        "bizspark-core.exe"
    } else {
        "bizspark-core"
    };
    // 开发期：apps/desktop/src-tauri/binaries/；打包后：资源目录
    let dev = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .join("binaries")
        .join(name);
    if dev.exists() {
        return Ok(dev);
    }
    let resource = app
        .path()
        .resource_dir()
        .map_err(|e| e.to_string())?
        .join("binaries")
        .join(name);
    if resource.exists() {
        return Ok(resource);
    }
    Err(format!("sidecar not found: {}", name))
}

/// A-03：启动 sidecar（启动一次、常驻、崩溃自动重启 1 次）
pub fn spawn_sidecar(app: AppHandle) -> Result<(), String> {
    let path = sidecar_path(&app)?;
    let mut child = Command::new(&path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("sidecar spawn failed: {}", e))?;

    let stdout = child.stdout.take().ok_or("sidecar stdout unavailable")?;
    let stdin = child.stdin.take().ok_or("sidecar stdin unavailable")?;
    *SIDECAR_STDIN.lock().unwrap() = Some(stdin);
    *SIDECAR.lock().unwrap() = Some(child);
    *RESTARTS.lock().unwrap() = 0;

    // 读循环：把 sidecar 的每一行 JSONL 原样推给前端（Rust 不改写内容）
    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            match line {
                Ok(l) => {
                    if l.trim().is_empty() {
                        continue;
                    }
                    let _ = app.emit("core://response", l);
                }
                Err(_) => break,
            }
        }
        // 读循环结束 = sidecar 退出（正常退出不会发生，sidecar 常驻）
        on_sidecar_exit(app);
    });
    Ok(())
}

/// A-03：崩溃自动重启，仅 1 次；再次失败上报前端统一降级（F13）
fn on_sidecar_exit(app: AppHandle) {
    let mut restarts = RESTARTS.lock().unwrap();
    if *restarts >= 1 {
        *restarts += 1;
        let _ = app.emit("core://response", serde_json::json!({
            "req_id": null,
            "ok": false,
            "error": { "code": "E_CORE_DOWN", "message": "sidecar crashed twice", "recoverable": false }
        })
        .to_string());
        return;
    }
    *restarts += 1;
    let _ = spawn_sidecar(app);
}

/// A-04：前端唯一 IPC 入口。req_id + cmd 原样转发，响应按 req_id 匹配回推。
#[tauri::command]
pub fn handle_core_cmd(
    app: AppHandle,
    state: State<BridgeState>,
    request: CoreRequest,
) -> Result<(), String> {
    // Rust 层只校验协议形态，不做业务判断
    if request.req_id.trim().is_empty() || request.cmd.trim().is_empty() {
        return Err("invalid request: req_id and cmd are required".into());
    }
    let payload = serde_json::json!({
        "req_id": request.req_id,
        "cmd": request.cmd,
        "payload": request.payload,
    });
    let mut line = payload.to_string();
    line.push('\n');

    let mut guard = SIDECAR_STDIN.lock().unwrap();
    match guard.as_mut() {
        Some(stdin) => {
            stdin
                .write_all(line.as_bytes())
                .map_err(|e| format!("sidecar write failed: {}", e))?;
            stdin.flush().map_err(|e| format!("sidecar flush failed: {}", e))?;
            Ok(())
        }
        None => {
            // sidecar 不在：走统一降级口径（F13），错误码见附录 D
            let _ = app.emit(
                "core://response",
                serde_json::json!({
                    "req_id": request.req_id,
                    "ok": false,
                    "error": { "code": "E_CORE_DOWN", "message": "sidecar unavailable", "recoverable": false }
                })
                .to_string(),
            );
            let _ = state; // BridgeState 预留
            Ok(())
        }
    }
}

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
/// PM 2026-11-16（F09）：sidecar 首行 ready 携带的本地库版本，供月度检查比对
static LOCAL_LIB_VERSION: Lazy<Mutex<Option<String>>> = Lazy::new(|| Mutex::new(None));

/// PM 2026-11-16（F09）：读 sidecar 首行 ready，提取 library_version（无则不动）。
fn note_ready_line(line: &str) {
    if let Ok(v) = serde_json::from_str::<serde_json::Value>(line) {
        let is_ready = v
            .pointer("/data/event")
            .and_then(|e| e.as_str())
            .map(|s| s == "ready")
            .unwrap_or(false);
        if is_ready {
            if let Some(ver) = v.pointer("/data/library_version").and_then(|x| x.as_str()) {
                *LOCAL_LIB_VERSION.lock().unwrap() = Some(ver.to_string());
            }
        }
    }
}

/// PM 2026-11-16（F09）：本地库版本（ready 握手带出；未就绪返回 None）。
pub fn local_library_version() -> Option<String> {
    LOCAL_LIB_VERSION.lock().unwrap().clone()
}

/// PM 2026-11-16（F09）：绕过前端直接向 sidecar 写一行请求（月度检查的
/// apply_delta 用）。响应仍走 core://response 事件总线；apply_delta 幂等
/// 且自带校验/备份/回滚，调用方无需读响应。
pub fn send_core_line(line: &str) -> bool {
    let mut guard = SIDECAR_STDIN.lock().unwrap();
    match guard.as_mut() {
        Some(stdin) => stdin
            .write_all(line.as_bytes())
            .and_then(|_| stdin.flush())
            .is_ok(),
        None => false,
    }
}

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

/// 拼出 sidecar 可执行文件路径
///
/// PM 2026-11-27（目录模式/onedir）：引擎改为 PyInstaller onedir 打包，
/// 以 `core/bizspark-core/bizspark-core.exe` 目录形态随 resources 分发。
/// 之前 onefile 模式每次启动解包到 %TEMP%，未签名 exe 从临时目录运行
/// 会触发杀软（360 等）查杀——引擎刚启动即被终结、界面全空（已实测复现）。
/// onedir 引擎常驻安装目录，不再碰 %TEMP%。
fn sidecar_path(app: &AppHandle) -> Result<std::path::PathBuf, String> {
    let rel = if cfg!(windows) {
        std::path::Path::new("core")
            .join("bizspark-core")
            .join("bizspark-core.exe")
    } else {
        std::path::Path::new("core")
            .join("bizspark-core")
            .join("bizspark-core")
    };
    // 候选1：exe 同目录（NSIS 安装版：安装根目录即 resource_dir，二者等价）
    if let Ok(exe) = std::env::current_exe() {
        let p = exe.parent().unwrap_or(std::path::Path::new(".")).join(&rel);
        if p.exists() {
            return Ok(p);
        }
    }
    // 候选2：资源目录（安装版兜底）
    let resource = app
        .path()
        .resource_dir()
        .map_err(|e| e.to_string())?
        .join(&rel);
    if resource.exists() {
        return Ok(resource);
    }
    // 候选3：工作目录（开发期：tauri dev 以 src-tauri 为 cwd）
    let dev = std::env::current_dir()
        .map_err(|e| e.to_string())?
        .join(&rel);
    if dev.exists() {
        return Ok(dev);
    }
    Err(format!("sidecar not found: {}", rel.display()))
}

/// PM 2026-11-27：引擎诊断日志。引擎的报错输出此前被丢弃（Stdio::null），
/// 出事时无据可查；现在启动/退出/报错全部落到 appData/logs/engine.log。
fn engine_log(app: &AppHandle, msg: &str) {
    let dir = app
        .path()
        .app_data_dir()
        .unwrap_or_else(|_| std::path::PathBuf::from("."))
        .join("logs");
    let _ = std::fs::create_dir_all(&dir);
    let path = dir.join("engine.log");
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(&path) {
        let _ = writeln!(f, "[{}] {}", utc_now(), msg);
    }
}

/// 紧凑 UTC 时间戳（自实现，避免引入 chrono）：2026-11-27T03:32:00Z 格式
fn utc_now() -> String {
    let secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0);
    let days = secs.div_euclid(86_400);
    let tod = secs.rem_euclid(86_400);
    // Howard Hinnant civil_from_days
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        y,
        m,
        d,
        tod / 3600,
        (tod % 3600) / 60,
        tod % 60
    )
}

/// A-03：启动 sidecar（启动一次、常驻、崩溃自动重启 1 次）
pub fn spawn_sidecar(app: AppHandle) -> Result<(), String> {
    let path = sidecar_path(&app)?;
    // PM 2026-11-27：引擎 stderr 落诊断日志（此前被丢弃）
    let stderr_stdio = match app.path().app_data_dir() {
        Ok(dir) => {
            let log_dir = dir.join("logs");
            let _ = std::fs::create_dir_all(&log_dir);
            match std::fs::OpenOptions::new()
                .create(true)
                .append(true)
                .open(log_dir.join("engine.log"))
            {
                Ok(f) => Stdio::from(f),
                Err(_) => Stdio::null(),
            }
        }
        Err(_) => Stdio::null(),
    };
    let mut child = Command::new(&path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(stderr_stdio)
        // PM 2026-11-13（中文包）：把构建目标 locale 传给 sidecar——
        // 引擎文案（why/tags/回本提示/PDF 标题）与内容覆盖 zh_v1.json 按此切换；
        // A-08 双构建：build-mode.txt 第 1 行 target 以 "cn" 开头即 zh-CN
        .env("BIZSPARK_LOCALE", {
            let loc = std::env::var("BIZSPARK_LOCALE").unwrap_or_default();
            if loc.is_empty() { "en-US".to_string() } else { loc }
        })
        .spawn()
        .map_err(|e| {
            engine_log(&app, &format!("SPAWN FAILED: {} path={}", e, path.display()));
            format!("sidecar spawn failed: {}", e)
        })?;

    engine_log(
        &app,
        &format!("SPAWN OK pid={} path={}", child.id(), path.display()),
    );

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
                    note_ready_line(&l); // PM 2026-11-16（F09）：ready 行顺带记录库版本
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
    // PM 2026-11-27：记录引擎退出状态（退出码写进诊断日志）
    let code = {
        let mut guard = SIDECAR.lock().unwrap();
        match guard.as_mut() {
            Some(child) => match child.wait() {
                Ok(st) => st.code().map(|c| c.to_string()).unwrap_or_else(|| "signal".into()),
                Err(e) => format!("wait_err:{}", e),
            },
            None => "unknown".into(),
        }
    };
    engine_log(&app, &format!("EXIT code={}", code));
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

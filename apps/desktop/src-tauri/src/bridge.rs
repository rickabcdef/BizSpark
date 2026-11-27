//! A-04 IPC 桥（负责人：A）+ A-03 sidecar 生命周期
//!
//! 职责（§2.2 / §2.4 / §7）：
//! - WebView ⇄ sidecar 的 JSONL 双向转发，带 req_id 匹配
//! - sidecar 启动一次、常驻、崩溃自动重启 1 次
//! - Rust 层只转发，不做业务判断，不改写 payload
//!
//! 前端唯一出口是 apps/web/src/bridge/cmd.ts（B 负责），经
//! invoke("handle_core_cmd", { request: { req_id, cmd, payload } }) 到达这里。
//! PM 2026-11-27：Tauri v2 按参数名匹配 invoke 参数，散参数 { reqId, cmd, payload }
//! 会在匹配层被拒（missing key `request`），且前端 catch 静默 → 打包版请求从未进过壳。

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
/// PM 2026-11-27（打包版合同修复）：等待引擎响应的请求表 req_id → 发送端。
/// handle_core_cmd 注册后原地等响应；读循环按 req_id 路由并移除。
static PENDING: Lazy<Mutex<std::collections::HashMap<String, std::sync::mpsc::Sender<serde_json::Value>>>> =
    Lazy::new(|| Mutex::new(std::collections::HashMap::new()));

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
    let mut cmd = Command::new(&path);
    cmd.stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(stderr_stdio)
        // PM 2026-11-13（中文包）：把构建目标 locale 传给 sidecar——
        // 引擎文案（why/tags/回本提示/PDF 标题）与内容覆盖 zh_v1.json 按此切换；
        // A-08 双构建：build-mode.txt 第 1 行 target 以 "cn" 开头即 zh-CN
        .env("BIZSPARK_LOCALE", {
            let loc = std::env::var("BIZSPARK_LOCALE").unwrap_or_default();
            if loc.is_empty() { "en-US".to_string() } else { loc }
        })
        // PM 2026-11-27（GBK 崩溃修复兜底）：中文 Windows 下 Python stdio 默认 GBK，
        // 引擎响应含 £ 等字符时 UnicodeEncodeError 即死（实测复现）。
        // 引擎侧 main.py 已 reconfigure UTF-8；这里再加环境变量双保险，
        // 即使旧版引擎没这行代码也不会崩。
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8:replace");
    // PM 2026-11-27：CREATE_NO_WINDOW——引擎是控制台程序，壳是图形程序，
    // 不加此标志 Windows 会给引擎配一个可见控制台窗口，窗口被关（360/系统/误点）
    // 引擎即死于 0xC000013A（控制台事件，诊断日志已实测抓到）。
    // 加上后引擎无窗口、无控制台事件通道，免疫此类查杀。
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW
    }
    let mut child = cmd
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

    // 读循环：把 sidecar 的每一行 JSONL 推给前端（Rust 不改写内容）
    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            match line {
                Ok(l) => {
                    if l.trim().is_empty() {
                        continue;
                    }
                    note_ready_line(&l); // PM 2026-11-16（F09）：ready 行顺带记录库版本
                    // PM 2026-11-27（打包版合同修复）：前端 invoke 期待"请求即响应"
                    //（与开发垫片 fetch /__ipc 语义一致）。带 req_id 的响应路由给
                    // 等待中的 handle_core_cmd 直接返回；其余行（ready 等）走事件总线。
                    // 此前响应只发事件总线而前端无人监听 → 打包版界面永远拿不到数据。
                    if let Ok(v) = serde_json::from_str::<serde_json::Value>(&l) {
                        let req_id = v.get("req_id").and_then(|x| x.as_str()).map(|s| s.to_string());
                        if let Some(req_id) = req_id {
                            let sender = PENDING.lock().unwrap().remove(&req_id);
                            if let Some(tx) = sender {
                                let _ = tx.send(v);
                                continue;
                            }
                        }
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

/// A-04：前端唯一 IPC 入口。
///
/// PM 2026-11-27（打包版合同修复）：前端 cmd.ts 的语义是 invoke 直接返回
/// `{ok, data}`（与开发垫片 fetch /__ipc 一致），但本函数此前转发后返回空、
/// 响应走事件总线而前端无人监听 → 打包版界面永远空。现改为：转发后按
/// req_id 原地等引擎响应（9 秒超时），拿到即作为 invoke 返回值。
#[tauri::command]
pub async fn handle_core_cmd(
    app: AppHandle,
    request: CoreRequest,
) -> Result<serde_json::Value, String> {
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

    let (tx, rx) = std::sync::mpsc::channel();
    PENDING.lock().unwrap().insert(request.req_id.clone(), tx);

    let started = std::time::Instant::now();
    let cmd_name = request.cmd.clone();
    let send_result = {
        let mut guard = SIDECAR_STDIN.lock().unwrap();
        match guard.as_mut() {
            Some(stdin) => stdin
                .write_all(line.as_bytes())
                .and_then(|_| stdin.flush())
                .map(|_| true)
                .map_err(|e| e.to_string()),
            None => Ok(false), // sidecar 不在
        }
    };

    match send_result {
        Err(e) => {
            PENDING.lock().unwrap().remove(&request.req_id);
            engine_log(&app, &format!("REQ {} WRITE FAILED: {}", cmd_name, e));
            Ok(serde_json::json!({
                "req_id": request.req_id,
                "ok": false,
                "error": { "code": "E_CORE_DOWN", "message": "sidecar write failed", "recoverable": false }
            }))
        }
        Ok(false) => {
            PENDING.lock().unwrap().remove(&request.req_id);
            engine_log(&app, &format!("REQ {} DROPPED: engine not running", cmd_name));
            // sidecar 不在：走统一降级口径（F13），错误码见附录 D
            Ok(serde_json::json!({
                "req_id": request.req_id,
                "ok": false,
                "error": { "code": "E_CORE_DOWN", "message": "sidecar unavailable", "recoverable": false }
            }))
        }
        Ok(true) => match rx.recv_timeout(std::time::Duration::from_secs(9)) {
            Ok(v) => {
                engine_log(
                    &app,
                    &format!("REQ {} -> RESP in {}ms", cmd_name, started.elapsed().as_millis()),
                );
                Ok(v)
            }
            Err(_) => {
                PENDING.lock().unwrap().remove(&request.req_id);
                engine_log(&app, &format!("REQ {} TIMEOUT 9s", cmd_name));
                Ok(serde_json::json!({
                    "req_id": request.req_id,
                    "ok": false,
                    "error": { "code": "E_TIMEOUT", "message": "engine response timeout", "recoverable": true }
                }))
            }
        },
    }
}

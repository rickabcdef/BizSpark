// BizSpark Tauri 壳入口（负责人：A）
// 任务：A-02 窗口 / A-03 sidecar 生命周期 / A-04 IPC 桥
//       A-05 系统能力（另存为对话框、深浅色跟随）/ A-11 性能打点
// 铁律（§2.2）：Rust 层不做业务判断，只转发与提供系统能力；
//             sidecar 不监听任何端口；本文件不写任何界面文案。
// 协同纪律：本文件归 A 所有，其他成员请勿直接修改，需求走 PR。

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod bridge;
mod fingerprint;
mod monthly_update;
mod updater;

use bridge::{handle_core_cmd, BridgeState};
use std::time::Instant;
use tauri::{Emitter, Manager};
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_shell::ShellExt;

/// A-11 性能打点：冷启动耗时。setup 完成即认为首屏可渲染，打点后推给前端/日志。
pub fn report_cold_start(app: &tauri::AppHandle, started: Instant) {
    let ms = started.elapsed().as_millis() as u64;
    // F14.1 性能基线验收；数据只打点，不做业务判断
    println!("[perf] cold_start_ms={}", ms);
    let _ = app.emit("perf://cold-start", serde_json::json!({ "cold_start_ms": ms }));
}

fn main() {
    let started = Instant::now();
    tauri::Builder::default()
        .manage(BridgeState::default())
        // A-03：sidecar 启动一次、常驻、崩溃自动重启 1 次
        // PM 2026-11-27：加 move——闭包需接管 started（Instant）所有权，否则 E0373
        .setup(move |app| {
            bridge::spawn_sidecar(app.handle().clone())?;
            report_cold_start(app.handle(), started);
            // PM 2026-11-16（F09）：月度库检查——1 号或距上次 ≥30 天静默拉 manifest，
            // 有新版逐包 apply_delta；后台线程，零弹窗零阻塞（monthly_update.rs）
            std::thread::spawn(|| monthly_update::run());
            Ok(())
        })
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        // A-04：前端唯一 IPC 入口 —— 所有 cmd 经此转发给 sidecar（JSONL）
        .invoke_handler(tauri::generate_handler![
            handle_core_cmd,
            get_fingerprint,
            save_export_dialog,
            default_export_dir,
            check_update_light,
            open_file,
            open_export_folder
        ])
        .run(tauri::generate_context!())
        .expect("error while running BizSpark");
}

/// A-06：机器指纹（SHA-256 hex）。仅供 G 的激活流程使用，原始机器信息不出 Rust 层。
#[tauri::command]
fn get_fingerprint() -> Result<String, String> {
    Ok(fingerprint::fingerprint_hex())
}

/// A-05：系统另存为对话框（F06 导出用）。
/// 返回用户选择的保存路径；取消返回 None。Rust 只提供系统能力，不写文案。
/// PM 2026-11-27：导出改走 default_export_dir（桌面\BizSpark 自动落盘），
/// 本命令保留但前端默认不再调用。
#[tauri::command]
fn save_export_dialog(
    app: tauri::AppHandle,
    default_file_name: String,
    extensions: Vec<String>,
) -> Result<Option<String>, String> {
    let mut builder = app.dialog().file().set_file_name(&default_file_name);
    if !extensions.is_empty() {
        // PM 2026-11-27：add_filter 需要 &[&str]，Vec<String> 转一次
        let ext_refs: Vec<&str> = extensions.iter().map(|s| s.as_str()).collect();
        builder = builder.add_filter("Export", &ext_refs);
    }
    Ok(builder.blocking_save_file().map(|p| p.to_string()))
}

/// PM 2026-11-27（老板需求）：导出默认落点 = 桌面\BizSpark，目录不存在自动创建，
/// 所有导出文件统一归档于此；前端不再弹另存框。桌面路径取系统 Known Folder
/// （OneDrive 重定向的桌面也能拿到），异常时回退用户主目录。
#[tauri::command]
fn default_export_dir(app: tauri::AppHandle) -> Result<String, String> {
    let base = app
        .path()
        .desktop_dir()
        .or_else(|_| app.path().home_dir())
        .map_err(|e| format!("resolve desktop dir failed: {}", e))?;
    let dir = base.join("BizSpark");
    std::fs::create_dir_all(&dir).map_err(|e| format!("create export dir failed: {}", e))?;
    Ok(dir.to_string_lossy().to_string())
}

/// A-05：用系统默认程序打开本次导出的 PDF（F06 导出后直接查看）。
/// 只接收前端从 core 拿到的本地文件路径，不接受外部任意路径。
#[tauri::command]
#[allow(deprecated)] // shell::open 已标记弃用，本机无 opener 插件；直调 Rust 不走 scope 校验
fn open_file(app: tauri::AppHandle, path: String) -> Result<(), String> {
    if path.trim().is_empty() {
        return Err("empty file path".into());
    }
    app.shell().open(path, None).map_err(|e| e.to_string())
}

/// A-05：在系统文件管理器中打开 PDF 所在目录（收文件路径，取父目录）。
#[tauri::command]
#[allow(deprecated)]
fn open_export_folder(app: tauri::AppHandle, path: String) -> Result<(), String> {
    let trimmed = path.trim().to_string();
    if trimmed.is_empty() {
        return Err("empty path".into());
    }
    let dir = std::path::Path::new(&trimmed)
        .parent()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or(trimmed);
    app.shell().open(dir, None).map_err(|e| e.to_string())
}

/// A-10 F12：分销版轻更新提示（3s 超时，失败静默）。
/// 只返回"有无新版本 + 说明"，不自动安装、不弹窗，展示方式由前端决定。
#[tauri::command]
fn check_update_light(app: tauri::AppHandle) -> Result<serde_json::Value, String> {
    let current = app.package_info().version.to_string();
    match updater::check_light_update(&current) {
        Some(m) => Ok(serde_json::json!({
            "available": true,
            "version": m.version,
            "notes": m.notes
        })),
        None => Ok(serde_json::json!({ "available": false })),
    }
}

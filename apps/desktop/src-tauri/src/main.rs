// BizSpark Tauri 壳入口（负责人：A）
// 任务：A-02 窗口 / A-03 sidecar 生命周期 / A-04 IPC 桥
//       A-05 系统能力（另存为对话框、深浅色跟随）/ A-11 性能打点
// 铁律（§2.2）：Rust 层不做业务判断，只转发与提供系统能力；
//             sidecar 不监听任何端口；本文件不写任何界面文案。
// 协同纪律：本文件归 A 所有，其他成员请勿直接修改，需求走 PR。

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod bridge;
mod fingerprint;
mod updater;

use bridge::{handle_core_cmd, BridgeState};
use std::time::Instant;
use tauri::{Emitter, Manager};
use tauri_plugin_dialog::DialogExt;

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
        .setup(|app| {
            bridge::spawn_sidecar(app.handle().clone())?;
            report_cold_start(app.handle(), started);
            Ok(())
        })
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        // A-04：前端唯一 IPC 入口 —— 所有 cmd 经此转发给 sidecar（JSONL）
        .invoke_handler(tauri::generate_handler![
            handle_core_cmd,
            get_fingerprint,
            save_export_dialog,
            check_update_light
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
#[tauri::command]
fn save_export_dialog(
    app: tauri::AppHandle,
    default_file_name: String,
    extensions: Vec<String>,
) -> Result<Option<String>, String> {
    let mut builder = app.dialog().file().set_file_name(&default_file_name);
    if !extensions.is_empty() {
        builder = builder.add_filter("Export", &extensions);
    }
    Ok(builder.blocking_save_file().map(|p| p.to_string()))
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

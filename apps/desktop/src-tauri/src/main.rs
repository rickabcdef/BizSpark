// BizSpark Tauri 壳入口（负责人：A）
// 任务：A-02 窗口初始化 / A-03 sidecar 生命周期 / A-04 IPC 桥
// 铁律（§2.2）：Rust 层不做业务判断，只转发与提供系统能力；
//             sidecar 不监听任何端口；本文件不写任何界面文案。

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod bridge;
mod fingerprint;
mod updater;

use bridge::{handle_core_cmd, BridgeState};
use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .manage(BridgeState::default())
        // A-03：sidecar 启动一次、常驻、崩溃自动重启 1 次
        .setup(|app| {
            bridge::spawn_sidecar(app.handle().clone())?;
            Ok(())
        })
        .plugin(tauri_plugin_shell::init())
        // A-04：前端唯一 IPC 入口 —— 所有 cmd 经此转发给 sidecar（JSONL）
        .invoke_handler(tauri::generate_handler![handle_core_cmd])
        .run(tauri::generate_context!())
        .expect("error while running BizSpark");
}

//! 窗口自适应屏幕（PM 2026-11-27，老板需求）：
//! ① 智能开窗——设计尺寸 1440×900 与屏幕 88% 取小，任何分辨率底部都在屏幕内
//!    （根因：老板机器 1366×768，旧配置硬开 900 高 → 窗口底边伸到屏幕外，滚不到底）
//! ② 记住窗口状态——关闭时存位置/尺寸到 app_data_dir，下次启动恢复；
//!    恢复值一律夹回当前屏幕范围（换小屏显示器也不会开到屏幕外）
//! Rust 层只做系统能力，不写界面文案（§2.2）。

use serde::{Deserialize, Serialize};
use tauri::{Manager, PhysicalPosition, PhysicalSize, WebviewWindow, WindowEvent};

/// 设计稿尺寸（逻辑像素，与 tauri.conf.json 一致）
const DESIGN_W: f64 = 1440.0;
const DESIGN_H: f64 = 900.0;
/// 屏幕占用上限比例（88% 已给任务栏/边距留量）
const FIT_RATIO: f64 = 0.88;
const STATE_FILE: &str = "window_state.json";

#[derive(Serialize, Deserialize)]
struct WinState {
    x: i32,
    y: i32,
    w: u32,
    h: u32,
}

/// setup 阶段调用：自适应开窗 + 挂关闭保存
pub fn apply(app: &tauri::AppHandle) {
    let Some(win) = app.get_webview_window("main") else {
        return;
    };

    let mon = win.current_monitor().ok().flatten();
    let scale = mon.as_ref().map(|m| m.scale_factor()).unwrap_or(1.0);

    // ① 设计尺寸与屏幕 88% 取小（物理像素，避免 DPI 换算误差）
    let (screen_w, screen_h) = match &mon {
        Some(m) => (m.size().width as f64, m.size().height as f64),
        None => (f64::MAX, f64::MAX),
    };
    let fit_w = ((DESIGN_W * scale).min(screen_w * FIT_RATIO)).round() as u32;
    let fit_h = ((DESIGN_H * scale).min(screen_h * FIT_RATIO)).round() as u32;

    if !restore(&win, &mon, fit_w, fit_h) {
        let _ = win.set_size(PhysicalSize::new(fit_w, fit_h));
        let _ = win.center();
    }

    // ② 关闭时保存窗口状态
    let win2 = win.clone();
    win.on_window_event(move |event| {
        if let WindowEvent::CloseRequested { .. } = event {
            save(&win2);
        }
    });
}

/// 恢复上次状态；成功返回 true。尺寸/位置全部夹回当前屏幕，防止换小屏后开到屏外。
fn restore(
    win: &WebviewWindow,
    mon: &Option<tauri::Monitor>,
    fit_w: u32,
    fit_h: u32,
) -> bool {
    let Ok(dir) = win.app_handle().path().app_data_dir() else {
        return false;
    };
    let Ok(raw) = std::fs::read_to_string(dir.join(STATE_FILE)) else {
        return false;
    };
    let Ok(s) = serde_json::from_str::<WinState>(&raw) else {
        return false;
    };
    if s.w < 200 || s.h < 200 {
        return false; // 异常值直接走智能开窗
    }

    let w = s.w.min(fit_w);
    let h = s.h.min(fit_h);
    // set_size 作用于内部区；set_position 作用于外框位置（Tauri/tao 语义，实测确认）
    let _ = win.set_size(PhysicalSize::new(w, h));

    // 位置夹回屏幕范围：用刚 set 完的真实外框尺寸计算，不依赖装饰常量
    if let Some(m) = mon {
        let Ok(sz) = win.outer_size() else {
            return true;
        };
        let ow = sz.width as i32;
        let oh = sz.height as i32;
        let mw = m.size().width as i32;
        let mh = m.size().height as i32;
        let mx = m.position().x;
        let my = m.position().y;
        let x = s.x.clamp(mx, (mx + mw - ow).max(mx));
        let y = s.y.clamp(my, (my + mh - oh).max(my));
        let _ = win.set_position(PhysicalPosition::new(x, y));
    }
    true
}

/// 关闭时把窗口状态存进 app_data_dir。
/// 口径（Tauri/tao 语义，实测确认）：set_size 作用内部区、set_position 作用外框位置，
/// 故存「inner_size + outer_position」，恢复时一一对应，无装饰偏移。
fn save(win: &WebviewWindow) {
    let Ok(dir) = win.app_handle().path().app_data_dir() else {
        return;
    };
    if std::fs::create_dir_all(&dir).is_err() {
        return;
    }
    let Ok(size) = win.inner_size() else {
        return;
    };
    let Ok(pos) = win.outer_position() else {
        return;
    };
    let state = WinState {
        x: pos.x,
        y: pos.y,
        w: size.width,
        h: size.height,
    };
    if let Ok(json) = serde_json::to_string(&state) {
        let _ = std::fs::write(dir.join(STATE_FILE), json);
    }
}

//! F09 月度库检查（PM 2026-11-16 补齐；落地：PM，编译复核：A——本机无 Rust 工具链）
//!
//! 流程（§2.4 F09 步骤 1–9，与 qa/e2e/bridge_server.mjs 的 runMonthlyLibraryCheck 同口径）：
//!   1. 门槛：当日为每月 1 号，或距上次检查 ≥30 天（BIZSPARK_FORCE_LIB_CHECK=1 强制）
//!   2. 静默 GET manifest.json（3 秒超时、失败不重试、不带任何用户标识/cookie）
//!   3. 失败（断网/超时/脏 JSON）→ 直接返回且**不盖戳**：下次启动重试
//!      （"断网一月回来，一次性补齐缺失 delta"）
//!   4. manifest.latest ≤ 本地版本 → 结束；成功检查即盖戳（壳层自己的记录文件）
//!   5. 有新版 → 按 manifest.files 逐包拉 delta，fire-and-forget 调 sidecar 的
//!      apply_delta（F 校验 → 备份 → 合并 → 失败回滚，全部在引擎侧完成）；
//!      任一包拉取失败即停（已成功的保留，apply_sequence 口径）
//!   6. 全程零弹窗零阻塞（T-30）；本模块**不发任何事件、不碰 UI**
//!
//! 版本比对：manifest.latest 形如 "2026-12"，本地 library_version 形如 "2026.12"，
//! 统一把 '-' 归一成 '.' 再比（字符串即可比，YYYY.MM 语义单调）。
//!
//! 注意：apply_delta 幂等（旧包/已合并包自动 skipped），fire-and-forget 安全；
//! 响应走既有的 core://response 事件总线，前端按 req_id 匹配，`f09-*` 前缀
//! 无前端消费者，天然静默。

use crate::bridge;
use crate::updater::fetch_json;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const DAY_MS: u64 = 86_400_000;
const GATE_FILE: &str = "library_check.json";
const CHECK_TIMEOUT_MS: u64 = 3_000;

fn norm_ver(s: &str) -> String {
    s.trim().replace('-', ".")
}

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis() as u64)
        .unwrap_or(0)
}

/// UTC 日历日（Howard Hinnant civil_from_days）：门槛里的"每月 1 号"用。
fn day_of_month_utc() -> u32 {
    let days = (now_ms() / 86_400_000) as i64;
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    (doy - (153 * mp + 2) / 5 + 1) as u32
}

fn gate_record_path() -> Option<std::path::PathBuf> {
    let base = std::env::var("APPDATA")
        .or_else(|_| std::env::var("HOME"))
        .ok()?;
    let dir = std::path::PathBuf::from(base).join("bizspark").join("cache");
    std::fs::create_dir_all(&dir).ok()?;
    Some(dir.join(GATE_FILE))
}

fn read_last_check_ms() -> u64 {
    gate_record_path()
        .and_then(|p| std::fs::read_to_string(p).ok())
        .and_then(|s| s.trim().parse::<u64>().ok())
        .unwrap_or(0)
}

fn stamp_check() {
    if let Some(p) = gate_record_path() {
        let _ = std::fs::write(&p, now_ms().to_string());
    }
}

fn due_for_check(force: bool) -> bool {
    if force {
        return true;
    }
    if day_of_month_utc() == 1 {
        return true;
    }
    let last = read_last_check_ms();
    last == 0 || now_ms().saturating_sub(last) >= 30 * DAY_MS
}

/// 等待 sidecar 首行 ready 带出的本地库版本（最多 5s；拿不到就放弃本次比对）。
fn wait_local_version() -> Option<String> {
    let deadline = now_ms() + 5_000;
    loop {
        if let Some(v) = bridge::local_library_version() {
            return Some(v);
        }
        if now_ms() >= deadline {
            return None;
        }
        std::thread::sleep(Duration::from_millis(100));
    }
}

/// 入口（main.rs setup 后台线程调用）。全静默：任何一步不如意直接 return。
pub fn run() {
    let force = std::env::var("BIZSPARK_FORCE_LIB_CHECK")
        .map(|v| v == "1")
        .unwrap_or(false);
    // 托管地址未配置（开发期默认占位域名）且未强制：整段跳过，不出网
    if std::env::var("BIZSPARK_HOST_URL").is_err() && !force {
        return;
    }
    if !due_for_check(force) {
        return;
    }
    // 2) 静默拉 manifest；失败不盖戳（下次启动重试）
    let body = match fetch_json("manifest.json") {
        Some(b) => b,
        None => return,
    };
    let manifest = match serde_json::from_str::<serde_json::Value>(&body) {
        Ok(m) => m,
        Err(_) => return, // 脏 JSON：A 静默丢弃，不叫 F（§7.3）
    };
    let latest = match manifest.get("latest").and_then(|v| v.as_str()) {
        Some(s) if !s.is_empty() => s.to_string(),
        _ => return,
    };
    stamp_check(); // 成功检查即盖戳（无论后续是否有新版）

    // 3) 比对本地版本（ready 握手带出，F 报本地、不联网——F09 步骤 2）
    let local = match wait_local_version() {
        Some(v) => norm_ver(&v),
        None => return,
    };
    if norm_ver(&latest) <= local {
        return; // 已是最新
    }

    // 4) 逐包拉 delta → apply_delta（fire-and-forget；任一失败即停）
    let files = manifest
        .get("files")
        .and_then(|v| v.as_array())
        .cloned()
        .unwrap_or_default();
    let mut seq = 0u32;
    for f in files.iter() {
        let name = match f.as_str() {
            Some(s) if !s.is_empty() => s,
            _ => continue,
        };
        let dbody = match fetch_json(name) {
            Some(b) => b,
            None => break,
        };
        let delta = match serde_json::from_str::<serde_json::Value>(&dbody) {
            Ok(d) => d,
            Err(_) => break,
        };
        seq += 1;
        let line = serde_json::json!({
            "req_id": format!("f09-{}", seq),
            "cmd": "apply_delta",
            "payload": { "delta": delta },
        })
        .to_string();
        if !bridge::send_core_line(&(line + "\n")) {
            break; // sidecar 不在：到此为止（已成功的保留）
        }
        std::thread::sleep(Duration::from_millis(200)); // 背靠背写盘稍作间隔
    }
    // 不读响应、不发事件：结果由 F 落到 state/library，界面下次查询自然可见
    let _ = CHECK_TIMEOUT_MS;
}

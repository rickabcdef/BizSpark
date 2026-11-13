//! manifest/delta 拉取与落盘（负责人：A/F 共管，见 F09/F12）
//!
//! A-07 静态托管 GET：3 秒超时，失败静默（联网是 F09 月度增量更新的唯一理由）；
//! A-10 F12 分销版轻更新提示：只提示、不自动安装，前端决定展示方式。
//!
//! 约束：本模块只做"拉取 + 校验 + 落盘"，合并逻辑归 F（state/merge.py）。

use serde::Deserialize;
use std::path::PathBuf;
use std::time::Duration;

/// 静态托管地址：构建期由 scripts/build-*.sh 注入（BIZSPARK_HOST_URL），双版可不同
pub fn host_base() -> String {
    std::env::var("BIZSPARK_HOST_URL").unwrap_or_else(|_| "https://static.bizspark.example".into())
}

#[derive(Deserialize, Clone)]
pub struct Manifest {
    pub version: String,
    #[serde(default)]
    pub delta_url: Option<String>,
    #[serde(default)]
    pub sha256: Option<String>,
    #[serde(default)]
    pub notes: Option<String>,
}

/// A-07：GET 一个托管文件。3 秒超时；任何失败返回 None（静默，不打扰用户）。
pub fn fetch_json(rel_path: &str) -> Option<String> {
    let url = format!("{}/{}", host_base().trim_end_matches('/'), rel_path.trim_start_matches('/'));
    let resp = ureq::AgentBuilder::new()
        .timeout_connect(Duration::from_secs(3))
        .timeout(Duration::from_secs(3))
        .build()
        .get(&url)
        .call();
    match resp {
        Ok(r) => r.into_string().ok().filter(|s| !s.trim().is_empty()),
        Err(_) => None, // 失败静默：断网/宕机/超时都不报错（T-30 系列）
    }
}

/// A-07 / F09：拉取 manifest 并落盘到应用数据目录，返回落盘路径；失败静默返回 None。
pub fn fetch_and_store_manifest() -> Option<PathBuf> {
    let body = fetch_json("manifest.json")?;
    let dir = app_cache_dir().ok()?;
    std::fs::create_dir_all(&dir).ok()?;
    let path = dir.join("manifest.json");
    std::fs::write(&path, body.as_bytes()).ok()?;
    Some(path)
}

/// A-10 F12：分销版轻更新提示。对比 manifest.version 与当前版本，
/// 有新版本时返回提示信息；不自动安装、不弹窗，仅把结果交给前端轻提示。
pub fn check_light_update(current_version: &str) -> Option<Manifest> {
    let body = fetch_json("manifest.json")?;
    let manifest: Manifest = serde_json::from_str(&body).ok()?;
    if version_gt(&manifest.version, current_version) {
        Some(manifest)
    } else {
        None
    }
}

/// 语义化版本比较：1.2.10 > 1.2.9
fn version_gt(a: &str, b: &str) -> bool {
    let parse = |s: &str| -> Vec<u64> {
        s.split('.')
            .map(|p| p.trim().parse().unwrap_or(0))
            .collect()
    };
    let (va, vb) = (parse(a), parse(b));
    for i in 0..va.len().max(vb.len()) {
        let x = va.get(i).copied().unwrap_or(0);
        let y = vb.get(i).copied().unwrap_or(0);
        if x != y {
            return x > y;
        }
    }
    false
}

fn app_cache_dir() -> Result<PathBuf, String> {
    let base = std::env::var("APPDATA")
        .or_else(|_| std::env::var("HOME"))
        .map_err(|_| "no home dir")?;
    Ok(PathBuf::from(base).join("bizspark").join("cache"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn version_compare() {
        assert!(version_gt("1.1.0", "1.0.9"));
        assert!(version_gt("1.2.10", "1.2.9"));
        assert!(!version_gt("1.0.0", "1.0.0"));
        assert!(!version_gt("0.9", "1.0"));
    }
}
